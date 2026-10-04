#!/usr/bin/env python3
"""listing-core 瘦身编排入口：四次确定性调用，保留两个语义插槽。

执行顺序：
  plan → [Product Detail + SIF 并发] → ingest → [洞察]
       → prepare-write → [Writer] → finish

本脚本不调用付费 API、不调用模型、不修改 Listing 文案。它只批量处理缓存、
投影、schema 校验、产物落盘、manifest 和最终 QA，减少 Agent 工具往返与重复 Read。
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_spec import assemble_spec  # noqa: E402
from evidence_cache import lookup_evidence, store_evidence  # noqa: E402
from linkfox_paths import session_root  # noqa: E402
from postflight_compliance import run_postflight  # noqa: E402
from project_product_detail import (  # noqa: E402
    _facts_markdown,
    build_bundle,
)
from run_full import cmd_finish  # noqa: E402
from run_manifest import (  # noqa: E402
    complete_timing,
    init_manifest,
    parse_profile,
    record_timing,
    update_stage,
)
from save_buyer_questions import normalize as normalize_questions  # noqa: E402
from save_keyword_plan import enrich_from_matrix, normalize as normalize_keywords  # noqa: E402
from validate_fields import (  # noqa: E402
    _brand_hits,
    _scan_banned,
    _special_symbols,
    _tokenize,
)

STAGE_DIRS = ("01-facts", "02-insight", "03-write")
INSIGHT_KIND = "listingInsightBundle"


def _load_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_json(path: Path, value: Any, *, compact: bool = False) -> None:
    if compact:
        content = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        content = json.dumps(value, ensure_ascii=False, indent=2)
    _atomic_text(path, content + "\n")


def _csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _asins(target: str | None, competitors: list[str]) -> list[str]:
    values = ([target] if target else []) + competitors
    normalized = [value.strip().upper() for value in values if value and value.strip()]
    return list(dict.fromkeys(normalized))


def _cache_keys(kind: str, asin: str, site: str) -> dict[str, str]:
    keys = {"asin": asin.strip().upper(), "site": site.strip().upper()}
    if kind == "product-detail":
        keys["returnAuthorsReviews"] = "true"
    elif kind == "keyword-matrix":
        keys.update({"window": "latelyDay_30", "top_n": "50"})
    return keys


def _manifest(run_dir: Path) -> str:
    return str(run_dir / "run-manifest.json")


def _ensure_dirs(run_dir: Path) -> None:
    for name in STAGE_DIRS:
        (run_dir / name).mkdir(parents=True, exist_ok=True)


def cmd_plan(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    if args.run_dir:
        run_dir = Path(os.path.abspath(args.run_dir))
    else:
        suffix = (args.target_asin or args.reference_asin or str(round(time.time()))).strip()
        run_dir = Path(session_root()) / "listing-core" / f"{args.mode}-{suffix}"
    profile = parse_profile(args.profile)
    profile.update({
        "marketplace": args.marketplace,
        "output_language": args.output_language,
        "pipeline": "collapsed-v1",
    })
    manifest_path = init_manifest(str(run_dir), args.mode, profile)
    _ensure_dirs(run_dir)
    update_stage(manifest_path, "facts", "active")
    record_timing(manifest_path, "evidence_plan", "active")

    requested_asins = _asins(
        args.target_asin,
        ([args.reference_asin] if args.reference_asin else []) + args.competitor_asin,
    )
    if not requested_asins and not args.own_facts:
        raise ValueError("plan requires --target-asin or --own-facts")
    main_asin = (args.target_asin or args.reference_asin or "").strip().upper()
    if not main_asin:
        raise ValueError("plan requires a target/reference ASIN for SIF")

    product_entries = []
    product_misses = []
    for asin in requested_asins:
        cached = lookup_evidence(
            "product-detail", _cache_keys("product-detail", asin, args.marketplace),
        )
        product_entries.append({"asin": asin, "cache": cached})
        if not cached["hit"]:
            product_misses.append(asin)
    matrix_cache = lookup_evidence(
        "keyword-matrix", _cache_keys("keyword-matrix", main_asin, args.marketplace),
    )
    fetch_plan = {
        "kind": "listingEvidenceFetchPlan",
        "schema_version": 1,
        "mode": args.mode,
        "marketplace": args.marketplace,
        "output_language": args.output_language,
        "target_asin": (args.target_asin or "").strip().upper() or None,
        "reference_asin": (args.reference_asin or "").strip().upper() or None,
        "competitor_asins": _asins(None, args.competitor_asin),
        "own_facts": os.path.abspath(args.own_facts) if args.own_facts else None,
        "audit_handoff": os.path.abspath(args.audit_handoff) if args.audit_handoff else None,
        "product_detail": {
            "entries": product_entries,
            "request_asins": product_misses,
            "request": {
                "asins": product_misses,
                "returnAuthorsReviews": True,
                "marketplace": args.marketplace,
            } if product_misses else None,
        },
        "keyword_matrix": {
            "asin": main_asin,
            "cache": matrix_cache,
            "request": None if matrix_cache["hit"] else {
                "asin": main_asin,
                "region": args.marketplace,
                "time_window": "latelyDay_30",
                "top_n": 50,
            },
        },
    }
    plan_path = run_dir / "fetch-plan.json"
    _atomic_json(plan_path, fetch_plan)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    record_timing(
        manifest_path, "evidence_plan", "complete", elapsed_ms,
        metrics={
            "product_cache_hits": len(requested_asins) - len(product_misses),
            "product_cache_misses": len(product_misses),
            "keyword_cache_hit": bool(matrix_cache["hit"]),
        },
    )
    record_timing(manifest_path, "external_evidence", "active")
    print(f"Saved full response: {manifest_path}")
    print(f"JSON artifact: {plan_path}")
    print("Fetch Product Detail ASINs: " + (",".join(product_misses) or "cache-hit"))
    print("Fetch keyword matrix: " + ("cache-hit" if matrix_cache["hit"] else main_asin))
    return 0


def _products_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("products"), list):
        return [item for item in payload["products"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and payload.get("asin"):
        return [payload]
    raise ValueError("Product Detail response must contain products[]")


def _matrix_rows(matrix: Any, top_n: int = 50) -> list[dict[str, Any]]:
    if not isinstance(matrix, dict):
        raise ValueError("keyword matrix must be a JSON object")
    raw_rows = matrix.get("scored_table")
    if not isinstance(raw_rows, list):
        raise ValueError("keyword matrix must contain scored_table[]")
    rows = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue
        word = str(raw.get("word") or raw.get("keyword") or raw.get("text") or "").strip()
        if not word:
            continue
        rows.append({
            "word": word,
            "source": str(raw.get("source") or "unknown"),
            "search_volume": raw.get("weekly_search_volume", raw.get("search_volume")),
            "rank": raw.get("rank", raw.get("natural_rank")),
        })
        if len(rows) >= top_n:
            break
    if not rows:
        raise ValueError("keyword matrix contains no usable rows")
    return rows


def _cached_paths(plan: dict[str, Any]) -> list[str]:
    paths = []
    for entry in (plan.get("product_detail") or {}).get("entries") or []:
        cache = entry.get("cache") if isinstance(entry, dict) else None
        path = cache.get("path") if isinstance(cache, dict) and cache.get("hit") else None
        if isinstance(path, str) and path not in paths:
            paths.append(path)
    return paths


def cmd_ingest(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    run_dir = Path(os.path.abspath(args.run_dir))
    manifest_path = _manifest(run_dir)
    plan_path = Path(args.fetch_plan or (run_dir / "fetch-plan.json"))
    plan = _load_json(plan_path)
    if not isinstance(plan, dict) or plan.get("kind") != "listingEvidenceFetchPlan":
        raise ValueError("invalid listingEvidenceFetchPlan")
    record_timing(manifest_path, "evidence_ingest", "active")

    source_paths = list(dict.fromkeys(_cached_paths(plan) + [os.path.abspath(p) for p in args.product_detail]))
    if not source_paths:
        raise ValueError("ingest requires Product Detail result paths or cache hits")
    products: dict[str, dict[str, Any]] = {}
    product_sources: dict[str, str] = {}
    for path in source_paths:
        for product in _products_from_payload(_load_json(path)):
            asin = str(product.get("asin") or "").strip().upper()
            if asin:
                products[asin] = product
                product_sources[asin] = path
    payload = {"products": list(products.values())}
    own_facts_path = args.own_facts or plan.get("own_facts")
    own_facts = _load_json(own_facts_path) if own_facts_path else None
    if own_facts is not None and not isinstance(own_facts, dict):
        raise ValueError("own facts must be a JSON object")
    references = list(plan.get("competitor_asins") or [])
    if plan.get("reference_asin") and plan["reference_asin"] not in references:
        references.insert(0, plan["reference_asin"])
    bundle = build_bundle(
        payload,
        plan.get("target_asin"),
        references,
        args.review_limit,
        own_facts=own_facts,
    )
    if not bundle["validation"]["target_valid"]:
        raise ValueError("product evidence target is invalid")
    detail_path = run_dir / "01-facts" / "product-detail.json"
    facts_path = run_dir / "01-facts" / "product-facts.md"
    _atomic_json(detail_path, bundle)
    _atomic_text(facts_path, _facts_markdown(bundle))

    matrix_path = args.keyword_matrix
    matrix_cache = (plan.get("keyword_matrix") or {}).get("cache") or {}
    if not matrix_path and matrix_cache.get("hit"):
        matrix_path = matrix_cache.get("path")
    if matrix_path and args.keyword_unavailable:
        raise ValueError("--keyword-matrix and --keyword-unavailable are mutually exclusive")
    if not matrix_path and not args.keyword_unavailable:
        raise ValueError(
            "ingest requires --keyword-matrix, a cache hit, or --keyword-unavailable REASON"
        )
    if matrix_path:
        matrix_path = os.path.abspath(matrix_path)
        matrix = _load_json(matrix_path)
        candidates = _matrix_rows(matrix, top_n=50)
        keyword_status = {
            "status": "available",
            "path": matrix_path,
            "reason": None,
        }
    else:
        candidates = []
        keyword_status = {
            "status": "unavailable",
            "path": None,
            "reason": args.keyword_unavailable,
        }
    plan["resolved"] = {
        "product_detail_paths": source_paths,
        "keyword_matrix_path": matrix_path,
        "keyword_data": keyword_status,
    }
    _atomic_json(plan_path, plan)
    insight_input = {
        "kind": "listingInsightInput",
        "schema_version": 1,
        "mode": plan["mode"],
        "marketplace": plan["marketplace"],
        "output_language": plan["output_language"],
        "product_evidence": bundle,
        "keyword_candidates": candidates,
        "execution_mode": (
            "facts_only" if keyword_status["status"] == "unavailable" else "external"
        ),
        "data_confidence": {
            "overall": (
                "unavailable" if keyword_status["status"] == "unavailable" else "available"
            ),
            "keyword_matrix": keyword_status,
        },
        "output_contract": {
            "kind": INSIGHT_KIND,
            "schema_version": 1,
            "required": ["insight_markdown", "buyer_questions", "keywords"],
            "keyword_groups": ["core", "scene", "pain", "attribute"],
            "report_language": "zh_CN",
        },
    }
    insight_input_path = run_dir / "02-insight" / "insight-input.json"
    _atomic_json(insight_input_path, insight_input, compact=True)

    site = str(plan["marketplace"])
    for asin, path in product_sources.items():
        store_evidence("product-detail", _cache_keys("product-detail", asin, site), path)
    if matrix_path:
        matrix_asin = str((plan.get("keyword_matrix") or {}).get("asin") or "")
        store_evidence("keyword-matrix", _cache_keys("keyword-matrix", matrix_asin, site), matrix_path)

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    record_timing(manifest_path, "external_evidence", "complete")
    record_timing(
        manifest_path, "evidence_ingest", "complete", elapsed_ms,
        metrics={
            "product_sources": len(source_paths),
            "products": len(products),
            "keyword_candidates": len(candidates),
            "evidence_mode": (
                "facts_only" if keyword_status["status"] == "unavailable" else "external"
            ),
        },
    )
    record_timing(manifest_path, "insight_semantic", "active")
    update_stage(
        manifest_path, "facts", "complete",
        artifacts=[
            {"name": "product-facts.md", "path": str(facts_path), "kind": "markdown"},
            {"name": "product-detail.json", "path": str(detail_path), "kind": "json"},
        ],
        activate="insight",
        metrics={"ingest_ms": elapsed_ms},
    )
    print(f"Saved full response: {manifest_path}")
    print(f"Markdown artifact: {facts_path}")
    print(f"JSON artifact: {detail_path}")
    print(f"Insight input: {insight_input_path}")
    return 0


def _insight_bundle(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("insight bundle must be a JSON object")
    if value.get("kind") != INSIGHT_KIND or value.get("schema_version") != 1:
        raise ValueError(f"insight bundle kind/schema must be {INSIGHT_KIND}/1")
    markdown = value.get("insight_markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("insight bundle requires non-empty insight_markdown")
    return value


def _writer_product_facts(bundle: dict[str, Any]) -> dict[str, Any]:
    """只给 Writer 本品可主张事实；评论与竞品已在洞察阶段消费。"""
    target = bundle.get("target")
    if not isinstance(target, dict):
        raise ValueError("product evidence requires target facts")
    return {
        key: value for key, value in target.items()
        if key not in {"authorsReviews", "evidence_strength"}
    }


def _fact_constraints(product_facts: dict[str, Any]) -> dict[str, Any]:
    """Project verified facts into deterministic keyword safety constraints."""
    facts_text = json.dumps(product_facts, ensure_ascii=False).replace("–", "-").replace("—", "-")
    age_ranges = [
        (int(match.group(1)), int(match.group(2)))
        for match in re.finditer(
            r"\b(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*months?\b",
            facts_text,
            flags=re.IGNORECASE,
        )
    ]
    constraints: dict[str, Any] = {
        "verified_tokens": sorted(set(_tokenize(facts_text))),
    }
    if age_ranges:
        constraints["age_months"] = {
            "min": min(value[0] for value in age_ranges),
            "max": max(value[1] for value in age_ranges),
            "source": "target_product_facts",
        }
    return constraints


def _writer_model_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Compile the full validation spec into the Writer's semantic contract."""
    shopping = ((spec.get("discovery_contract") or {}).get("shopping_assistant") or {})
    front_fields = {
        field: role
        for field, role in (spec.get("field_roles") or {}).items()
        if field in {
            "title", "item_highlights", "bullets", "description",
            "structured_attributes",
        }
    }
    return {
        "kind": "listingWriterModelSpec",
        "schema_version": 1,
        "mode": spec.get("mode"),
        "marketplace": spec.get("marketplace"),
        "output_language": spec.get("output_language"),
        "category": spec.get("category"),
        "product_type": spec.get("product_type"),
        "evidence_mode": spec.get("evidence_mode"),
        "limits": spec.get("limits") or {},
        "generation_targets": spec.get("generation_targets") or {},
        "authoring_recommendations": spec.get("authoring_recommendations") or {},
        "brands": spec.get("brands") or {"owned": [], "competitor": []},
        "user_banned_terms": spec.get("user_banned_terms") or [],
        "keywords": spec.get("keywords") or {},
        "buyer_questions": spec.get("buyer_questions") or [],
        "bullet_plan": spec.get("bullet_plan") or [],
        "claim_policy": spec.get("claim_policy") or {},
        "style": spec.get("style") or {},
        "rewrite_contract": spec.get("rewrite_contract"),
        "field_roles": front_fields,
        "required_four_pillars": shopping.get("four_pillars") or [],
        "backend_fields": {
            "generated_by": "pipeline_finish",
            "omit_from_writer": ["search_terms", "subject_matter"],
        },
    }


def _keyword_phrases(spec: dict[str, Any]) -> list[tuple[str, str]]:
    phrases: list[tuple[str, str]] = []
    for row in spec.get("keyword_evidence") or []:
        if isinstance(row, dict) and isinstance(row.get("term"), str):
            phrases.append((row["term"], str(row.get("source") or "unknown")))
    if not phrases:
        keywords = spec.get("keywords") or {}
        for group in (
            "core_to_title", "scene_to_bullets", "pain_to_bullets",
            "attribute_to_highlights",
        ):
            phrases.extend(
                (value, "unknown")
                for value in keywords.get(group) or [] if isinstance(value, str)
            )
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for phrase, source in phrases:
        folded = phrase.strip().casefold()
        if folded and folded not in seen:
            result.append((phrase.strip(), source.strip().casefold() or "unknown"))
            seen.add(folded)
    return result


def _contains_token_sequence(tokens: list[str], sequence: list[str]) -> bool:
    if not sequence or len(sequence) > len(tokens):
        return False
    width = len(sequence)
    return any(
        tokens[index:index + width] == sequence
        for index in range(len(tokens) - width + 1)
    )


def _safe_backend_phrase(
    phrase: str, source: str, spec: dict[str, Any], brand_tokens: set[str],
) -> tuple[str, list[str]] | None:
    tokens = _tokenize(phrase)
    normalized = " ".join(tokens)
    # Bare numeric tokens can join neighboring terms into fake units/model claims
    # (for example ``4 cancelling``); specifications belong in verified front fields.
    if (
        not normalized
        or any(token.isdigit() for token in tokens)
        or brand_tokens.intersection(tokens)
    ):
        return None
    constraints = spec.get("fact_constraints") or {}
    age_months = constraints.get("age_months") or {}
    if isinstance(age_months.get("min"), int) and age_months["min"] >= 4 and "newborn" in tokens:
        return None
    verified_tokens = set(constraints.get("verified_tokens") or [])
    if (
        len(tokens) == 1
        and verified_tokens
        and source not in {"user", "local", "inferred"}
        and tokens[0] not in verified_tokens
    ):
        # Opaque single-token external candidates are commonly brand/trademark
        # noise. Require presence in target facts before using scarce backend space.
        return None
    if (
        _scan_banned(normalized, spec)
        or _brand_hits(normalized, spec)
        or _special_symbols(normalized)
    ):
        return None
    return normalized, tokens


def _compile_backend_fields(
    draft: dict[str, Any], spec: dict[str, Any],
) -> dict[str, int]:
    """Build safe backend fields from keyword evidence after front copy exists."""
    if not isinstance(draft, dict):
        raise ValueError("listing draft must be a JSON object")
    title = draft.get("title")
    bullets = draft.get("bullets")
    if not isinstance(title, str) or not isinstance(bullets, list):
        raise ValueError("listing draft requires title and bullets before backend compilation")
    front_tokens = _tokenize(
        " ".join([title] + [value for value in bullets if isinstance(value, str)])
    )
    front_set = set(front_tokens)
    brand_tokens = {
        token
        for group in (spec.get("brands") or {}).values()
        for brand in (group if isinstance(group, list) else [])
        if isinstance(brand, str)
        for token in _tokenize(brand)
    }
    safe_phrases = []
    for phrase, source in _keyword_phrases(spec):
        safe = _safe_backend_phrase(phrase, source, spec, brand_tokens)
        if safe is not None:
            safe_phrases.append(safe)

    byte_limit = (spec.get("generation_targets") or {}).get("search_terms_bytes_max")
    if not isinstance(byte_limit, int) or byte_limit < 1:
        byte_limit = (spec.get("limits") or {}).get("search_terms_bytes_max")
    if not isinstance(byte_limit, int) or byte_limit < 1:
        raise ValueError("spec requires a positive search_terms byte limit")

    search_tokens: list[str] = []
    seen_tokens: set[str] = set()
    for _, tokens in safe_phrases:
        for token in tokens:
            if token in front_set or token in seen_tokens:
                continue
            candidate = " ".join(search_tokens + [token])
            if len(candidate.encode("utf-8")) > byte_limit:
                continue
            search_tokens.append(token)
            seen_tokens.add(token)
    if not search_tokens:
        raise ValueError("no safe non-front keyword tokens available for search_terms")

    subject_limit = (spec.get("limits") or {}).get("subject_matter_max")
    subject_matter: list[str] = []
    for normalized, tokens in safe_phrases:
        if _contains_token_sequence(front_tokens, tokens):
            continue
        if isinstance(subject_limit, int) and len(normalized) > subject_limit:
            continue
        if normalized not in subject_matter:
            subject_matter.append(normalized)
        if len(subject_matter) == 5:
            break

    draft["search_terms"] = " ".join(search_tokens)
    draft["subject_matter"] = subject_matter
    return {
        "search_terms_bytes": len(draft["search_terms"].encode("utf-8")),
        "search_terms_tokens": len(search_tokens),
        "subject_matter_items": len(subject_matter),
    }


def cmd_prepare_write(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    run_dir = Path(os.path.abspath(args.run_dir))
    manifest_path = _manifest(run_dir)
    bundle = _insight_bundle(_load_json(args.insight_bundle))
    plan = _load_json(run_dir / "fetch-plan.json")
    keyword_status = ((plan.get("resolved") or {}).get("keyword_data") or {}).get("status")
    evidence_mode = "facts_only" if keyword_status == "unavailable" else "external"
    questions = normalize_questions({"questions": bundle.get("buyer_questions")})
    keywords = normalize_keywords(bundle.get("keywords"))
    matrix_path = args.keyword_matrix or (plan.get("resolved") or {}).get("keyword_matrix_path")
    matrix_cache = (plan.get("keyword_matrix") or {}).get("cache") or {}
    if not matrix_path and matrix_cache.get("hit"):
        matrix_path = matrix_cache.get("path")
    if matrix_path:
        keywords = enrich_from_matrix(keywords, _load_json(matrix_path))
    product_bundle = _load_json(run_dir / "01-facts" / "product-detail.json")
    target_facts = _writer_product_facts(product_bundle)

    insight_path = run_dir / "02-insight" / "insight.md"
    questions_path = run_dir / "02-insight" / "buyer-questions.json"
    keywords_path = run_dir / "02-insight" / "keywords.json"
    _atomic_text(insight_path, bundle["insight_markdown"].rstrip() + "\n")
    _atomic_json(questions_path, questions)
    _atomic_json(keywords_path, keywords)

    spec = assemble_spec(
        mode=plan["mode"],
        brands_owned=_csv(args.brands_owned),
        brands_competitor=_csv(args.brands_competitor),
        keywords=keywords,
        category_flags=_csv(args.category_flags),
        user_spec=_load_json(args.spec) if args.spec else None,
        style_angle=args.style_angle,
        output_language=args.output_language or plan.get("output_language"),
        buyer_questions=questions,
        marketplace=args.marketplace or plan.get("marketplace") or "US",
        category=args.category,
        product_type=args.product_type,
        profile="standard",
        rewrite_handoff=(
            _load_json(args.audit_handoff or plan.get("audit_handoff"))
            if (args.audit_handoff or plan.get("audit_handoff")) else None
        ),
        evidence_mode=evidence_mode,
        banned_terms=_csv(args.banned_terms),
    )
    spec["fact_constraints"] = _fact_constraints(target_facts)
    spec_path = run_dir / "03-write" / "spec.json"
    _atomic_json(spec_path, spec)
    writer_input = {
        "kind": "listingWriterInput",
        "schema_version": 1,
        "instruction": (
            "Generate exactly one listing-draft JSON object. Preserve verified facts only; "
            "competitor evidence is structure/reference only. Obey model_spec generation_targets and types. "
            "Use at least 60% of the exact scene and pain keyword phrases naturally across bullets. "
            "Do not generate search_terms or subject_matter; pipeline_finish compiles both deterministically."
        ),
        "verified_product_facts": target_facts,
        "insight": {
            "summary": bundle["insight_markdown"],
        },
        "execution_mode": evidence_mode,
        "data_confidence": {
            "overall": "unavailable" if evidence_mode == "facts_only" else "available",
            "keyword_matrix": (plan.get("resolved") or {}).get("keyword_data"),
        },
        "model_spec": _writer_model_spec(spec),
        "draft_contract": {
            "title": "string",
            "item_highlights": "array containing exactly one string",
            "bullets": "array containing exactly five strings",
            "description": "string",
            "structured_attributes": "object",
            "question_coverage": "array",
            "four_pillars": "object",
        },
    }
    writer_input_path = run_dir / "03-write" / "writer-input.json"
    _atomic_json(writer_input_path, writer_input, compact=True)

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    record_timing(manifest_path, "insight_semantic", "complete")
    record_timing(
        manifest_path, "prepare_write", "complete", elapsed_ms,
        metrics={
            "buyer_questions": len(questions["questions"]),
            "keywords": sum(len(keywords[group]) for group in ("core", "scene", "pain", "attribute")),
        },
    )
    record_timing(manifest_path, "writer_semantic", "active")
    update_stage(
        manifest_path, "insight", "complete",
        artifacts=[
            {"name": "insight.md", "path": str(insight_path), "kind": "markdown"},
            {"name": "buyer-questions.json", "path": str(questions_path), "kind": "json"},
            {"name": "keywords.json", "path": str(keywords_path), "kind": "json"},
        ],
        activate="write",
        metrics={"prepare_write_ms": elapsed_ms},
    )
    update_stage(
        manifest_path, "write", "active",
        artifacts=[
            {"name": "spec.json", "path": str(spec_path), "kind": "json"},
            {"name": "writer-input.json", "path": str(writer_input_path), "kind": "json"},
        ],
    )
    print(f"Saved full response: {manifest_path}")
    print(f"Markdown artifact: {insight_path}")
    print(f"JSON artifact: {questions_path}")
    print(f"JSON artifact: {keywords_path}")
    print(f"Writer input: {writer_input_path}")
    print(f"Draft target: {run_dir / '03-write' / 'listing-draft.json'}")
    return 0


def cmd_pipeline_finish(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    run_dir = Path(os.path.abspath(args.run_dir))
    manifest_path = _manifest(run_dir)
    if not args.facts:
        args.facts = str(run_dir / "01-facts" / "product-facts.md")
    record_timing(manifest_path, "writer_semantic", "complete")
    record_timing(manifest_path, "finalize_pipeline", "active")
    draft_path = Path(os.path.abspath(
        args.draft or (run_dir / "03-write" / "listing-draft.json")
    ))
    spec_path = Path(os.path.abspath(args.spec or (run_dir / "03-write" / "spec.json")))
    try:
        draft = _load_json(draft_path)
        spec = _load_json(spec_path)
        backend_metrics = _compile_backend_fields(draft, spec)
        _atomic_json(draft_path, draft)
        compliance_path = run_dir / "03-write" / "compliance-report-after.json"
        compliance_report = run_postflight(
            draft_path,
            compliance_path,
            spec,
            asin=str((spec.get("rewrite_contract") or {}).get("target", {}).get("asin") or "") or None,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        record_timing(manifest_path, "finalize_pipeline", "failed", elapsed_ms)
        raise
    print(f"JSON artifact: {compliance_path}")
    gate = compliance_report.get("postflight_gate") or {}
    if gate.get("status") == "blocked":
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        record_timing(manifest_path, "finalize_pipeline", "failed", elapsed_ms)
        update_stage(
            manifest_path, "write", "failed",
            artifacts=[{"name": "compliance-report-after", "path": str(compliance_path), "kind": "json"}],
            metrics={"postflight_blocking_hits": len(gate.get("blocking_hits") or [])},
        )
        print("COMPLIANCE BLOCKED — 只重写命中字段并重新执行 finish：")
        for hit in gate.get("blocking_hits") or []:
            print(f"  [{hit.get('field')}] {hit.get('term')}: {hit.get('reason')}")
        for library in gate.get("failed_libraries") or []:
            print(f"  [scanner] {library.get('key')}: {library.get('error') or 'failed'}")
        return 2

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = cmd_finish(args)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    record_timing(
        manifest_path, "finalize_pipeline",
        "complete" if result == 0 else "failed",
        elapsed_ms,
        metrics=backend_metrics,
    )
    if result == 0:
        manifest = complete_timing(manifest_path)
    else:
        manifest = _load_json(manifest_path)
    sys.stdout.write(output.getvalue())
    timing = manifest.get("timing") or {}
    if result == 0:
        print(f"Pipeline total: {timing.get('total_duration_ms', 0)}ms")
    print(f"Pipeline finalize: {elapsed_ms}ms")
    return result


def _add_plan(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--run-dir", default=None,
        help="run 目录；省略时由本地 session_root() 分配",
    )
    parser.add_argument("--mode", required=True, choices=("benchmark", "rewrite", "create"))
    parser.add_argument("--profile", default="standard")
    parser.add_argument("--marketplace", default="US")
    parser.add_argument("--output-language", default="en_US")
    parser.add_argument("--target-asin", default=None)
    parser.add_argument("--reference-asin", default=None)
    parser.add_argument("--competitor-asin", action="append", default=[])
    parser.add_argument("--own-facts", default=None)
    parser.add_argument("--audit-handoff", default=None)


def _add_prepare_write(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--insight-bundle", required=True)
    parser.add_argument("--keyword-matrix", default=None)
    parser.add_argument("--brands-owned", default="")
    parser.add_argument("--brands-competitor", default="")
    parser.add_argument("--category-flags", default="")
    parser.add_argument("--spec", default=None)
    parser.add_argument("--style-angle", default=None)
    parser.add_argument("--marketplace", default=None)
    parser.add_argument("--output-language", default=None)
    parser.add_argument("--category", default="")
    parser.add_argument("--product-type", default="")
    parser.add_argument("--banned-terms", default="")
    parser.add_argument("--audit-handoff", default=None)


def _add_finish(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--draft", default=None)
    parser.add_argument("--spec", default=None)
    parser.add_argument("--facts", default=None)
    parser.add_argument("--brand-name", default=None)
    parser.add_argument("--seller-sku", default=None)
    parser.add_argument("--deductions", default=None)
    parser.add_argument("--scorer", default=None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_plan(sub.add_parser("plan"))
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--run-dir", required=True)
    ingest.add_argument("--fetch-plan", default=None)
    ingest.add_argument("--product-detail", action="append", default=[])
    ingest.add_argument("--keyword-matrix", default=None)
    ingest.add_argument(
        "--keyword-unavailable", default=None, metavar="REASON",
        help="SIF 与同次 backup 均失败时的明确降级原因；进入 facts_only",
    )
    ingest.add_argument("--own-facts", default=None)
    ingest.add_argument("--review-limit", type=int, default=8)
    _add_prepare_write(sub.add_parser("prepare-write"))
    _add_finish(sub.add_parser("finish"))
    args = parser.parse_args()
    handlers = {
        "plan": cmd_plan,
        "ingest": cmd_ingest,
        "prepare-write": cmd_prepare_write,
        "finish": cmd_pipeline_finish,
    }
    try:
        code = handlers[args.cmd](args)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"pipeline {args.cmd} failed: {exc}", file=sys.stderr)
        code = 1
    raise SystemExit(code)


if __name__ == "__main__":
    main()
