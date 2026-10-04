#!/usr/bin/env python3
"""
listing-title-writer 落盘器 — 裸 payload + skill-output-protocol。

Usage:
  python scripts/save_title_output.py '<json>'
  python scripts/save_title_output.py title.json --xlsx            # 额外导出 Excel
  python scripts/save_title_output.py title.json --spec spec.json  # 用户规格覆盖 75/125
  cat title.json | python scripts/save_title_output.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from listing_spec import extract_spec_arg, field_enabled, resolve_limit, tag  # type: ignore

SLUG = "linkfox-listing-title-writer"
# Layer B 缺省值（2026-07-27 新规最佳实践）；用户可用 --spec 覆盖，
# 平台底线（title ≤200）由 listing_spec.PLATFORM_LIMITS 兜底，不可放宽。
TITLE_MAX = 75
HIGHLIGHTS_MAX = 125
CLASSIC_TITLE_MAX = 200
PLATFORM_TITLE_MAX = 200
MEDIA_POLICIES = {"media_exempt"}
WORKBENCH_SCHEMA = "linkfox-listing-title-workbench/v1"
WORKBENCH_TYPE = "tableListWorkbenches"
POLICY_VERSION = "2026-07-27"
TASK_MODES = {"generate", "rewrite", "migrate", "revise", "classic"}
KEYWORD_BUCKETS = ("core", "attribute", "scenario", "pain")
MIGRATION_TARGETS = {"title", "highlights", "bullets", "backend_attributes", "aplus", "dropped"}
HARD_SPEC_RE = re.compile(
    r"(\d+\s?(oz|ml|l|inch|in|cm|mm|ft|w|watt|v|volt|a|amp|hz|gb|tb|mah|pack|count|pcs|"
    r"gallon|qt|lb|lbs|kg|g)\b)|stainless|silicone|bpa|usb[-\s]?c|type[-\s]?c|gan",
    re.I,
)
DUP_PHRASE_WORDS = 4

# 共享列契约：Excel 导出（export_title_xlsx.py）与前端 TitleWorkbenchRenderer
# 都按这一份定义渲染，改这里两边同时生效。只保留复核必需的字段，避免噪音。
WORKBENCH_COLUMNS = [
    {"key": "row_index", "title": "行号", "width": 60, "excelWidth": 6},
    {"key": "sku", "title": "SKU", "width": 120, "excelWidth": 14},
    {"key": "asin", "title": "ASIN", "width": 120, "excelWidth": 13},
    {"key": "legacy_title", "title": "原标题", "width": 260, "excelWidth": 40, "optional": True},
    {"key": "title", "title": "新标题", "width": 300, "excelWidth": 40, "editable": True},
    {
        "key": "title_char_count",
        "title": "标题字符数",
        "width": 110,
        "excelWidth": 11,
        "render": "charMeter",
        "maxFrom": "row.policy.title_max",
    },
    {
        "key": "item_highlights",
        "title": "Item Highlights",
        "width": 300,
        "excelWidth": 40,
        "editable": True,
        "optional": True,
    },
    {
        "key": "item_highlights_char_count",
        "title": "Highlights 字符数",
        "width": 130,
        "excelWidth": 13,
        "render": "charMeter",
        "maxFrom": "row.policy.item_highlights_max",
        "optional": True,
    },
    {"key": "keyword_notes", "title": "埋词说明", "width": 280, "excelWidth": 38, "render": "multiline"},
    {
        "key": "rationale",
        "title": "改写逻辑",
        "width": 240,
        "excelWidth": 34,
        "render": "multiline",
        "optional": True,
    },
    {"key": "status", "title": "状态", "width": 90, "excelWidth": 9, "render": "statusTag"},
    {
        "key": "validation_notes",
        "title": "校验说明",
        "width": 220,
        "excelWidth": 30,
        "render": "multiline",
        "optional": True,
    },
]

BUCKET_LABEL = {"core": "核心词", "attribute": "属性词", "scenario": "场景词", "pain": "痛点词"}
SOURCE_LABEL = {
    "sif": "SIF 流量词",
    "sellersprite_backup": "SellerSprite 备份词",
    "category_seed": "类目推导词",
    "heuristic": "推导词（无流量数据）",
    "none": "无关键词数据",
}

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _read_input(argv: list[str]) -> str:
    if not argv or argv[0] == "-":
        if sys.stdin.isatty():
            print("用法: save_title_output.py '<json>' | save_title_output.py file.json", file=sys.stderr)
            sys.exit(1)
        return sys.stdin.read()
    arg = argv[0]
    if os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return f.read()
    return arg


def _is_media(payload: dict) -> bool:
    meta = payload.get("meta") or {}
    if meta.get("amazon_title_policy") in MEDIA_POLICIES:
        return True
    return bool(payload.get("is_media"))


def _task_mode(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("task_mode") or "").strip()
    if explicit:
        return explicit
    if payload.get("source_mode") == "split_legacy":
        return "migrate"
    product = payload.get("product") if isinstance(payload.get("product"), dict) else {}
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    platform = str(
        _first_value(
            payload.get("platform"),
            payload.get("target_platform"),
            product.get("platform"),
            policy.get("platform"),
            "",
        )
        or ""
    ).strip().lower()
    non_amazon_platform = bool(platform) and "amazon" not in platform
    if (
        non_amazon_platform
        or payload.get("title_only") is True
        or payload.get("include_item_highlights") is False
    ):
        return "classic"
    if str(payload.get("legacy_title") or "").strip():
        return "migrate"
    return "generate"


def _validate(payload: dict, spec: dict | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return [f"顶层必须是对象，实际为 {type(payload).__name__}"], warnings

    task_mode = _task_mode(payload)
    if task_mode not in TASK_MODES:
        errors.append("task_mode 必须是 generate、rewrite、migrate、revise 或 classic")

    source_mode = payload.get("source_mode")
    if source_mode is None:
        source_mode = "split_legacy" if task_mode == "migrate" else "generate"
        payload["source_mode"] = source_mode
    if source_mode not in ("generate", "split_legacy"):
        errors.append("source_mode 必须是 generate 或 split_legacy")

    title = str(payload.get("title") or "")
    if not title.strip():
        errors.append("缺少 title")
    else:
        payload["title_char_count"] = len(title)

    highlights = str(payload.get("item_highlights") or "")
    payload["item_highlights_char_count"] = len(highlights)

    media = _is_media(payload)
    if task_mode == "classic":
        incoming_policy = _dict(payload.get("policy"))
        configured_title_max = _first_value(
            incoming_policy.get("title_max"),
            incoming_policy.get("titleMax"),
            payload.get("title_max"),
            CLASSIC_TITLE_MAX,
        )
        if isinstance(configured_title_max, bool) or not isinstance(configured_title_max, int) or configured_title_max <= 0:
            errors.append("classic 模式 policy.title_max 必须是正整数")
        elif len(title) > configured_title_max:
            errors.append(f"title 超长：{len(title)} > {configured_title_max}")
        if highlights:
            errors.append("classic 模式 item_highlights 必须为空")
    elif not media:
        title_max, title_layer = resolve_limit(spec, "title", "max", TITLE_MAX)
        if len(title) > PLATFORM_TITLE_MAX:
            errors.append(
                f"{tag('platform')} title 超出平台硬限制：{len(title)} > {PLATFORM_TITLE_MAX}"
            )
        elif len(title) > title_max:
            errors.append(f"{tag(title_layer)} title 超长：{len(title)} > {title_max}")
        if field_enabled(spec, "item_highlights"):
            hl_max, hl_layer = resolve_limit(spec, "item_highlights", "max", HIGHLIGHTS_MAX)
            if highlights and len(highlights) > hl_max:
                errors.append(
                    f"{tag(hl_layer)} item_highlights 超长：{len(highlights)} > {hl_max}"
                )
        elif highlights:
            errors.append(f"{tag('user_spec')} 用户规格已禁用 item_highlights，该字段必须为空")

    if task_mode in {"rewrite", "migrate", "revise"}:
        if not str(payload.get("legacy_title") or "").strip():
            errors.append(f"{task_mode} 模式缺少 legacy_title")

    if task_mode == "migrate":
        migration = payload.get("migration_map")
        strategy = payload.get("strategy") if isinstance(payload.get("strategy"), dict) else {}
        if not isinstance(migration, list) or not migration:
            if not _list(strategy.get("migration_map")):
                warnings.append("migrate 模式建议提供 migration_map")
        migration_errors, migration_warnings = _audit_migration(payload)
        errors.extend(migration_errors)
        warnings.extend(migration_warnings)

    if (
        task_mode == "generate"
        and not media
        and not highlights
        and field_enabled(spec, "item_highlights")
    ):
        warnings.append("generate 模式未产出 item_highlights，建议补充场景/收益句")

    if task_mode != "classic":
        warnings.extend(_audit_keywords(payload, title, highlights))

    return errors, warnings


def _phrases(text: str, size: int) -> set[str]:
    words = [w for w in re.split(r"[^A-Za-z0-9]+", text.lower()) if w]
    return {" ".join(words[i : i + size]) for i in range(0, max(0, len(words) - size + 1))}


def _keyword_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    strategy = payload.get("strategy") if isinstance(payload.get("strategy"), dict) else {}
    raw = _first_value(strategy.get("used_keywords"), payload.get("used_keywords"), [])
    return [k for k in _list(raw) if isinstance(k, dict)]


def _keyword_text(entry: dict[str, Any]) -> str:
    for key in ("kw", "keyword", "text"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _audit_keywords(payload: dict[str, Any], title: str, highlights: str) -> list[str]:
    """零成本埋词自检。只产出 warning，不阻断落盘，也不改写文案。"""
    warnings: list[str] = []
    title_lc = title.lower()
    entries = _keyword_entries(payload)

    primary = str(
        _first_value(
            (payload.get("strategy") or {}).get("primary_keyword") if isinstance(payload.get("strategy"), dict) else None,
            payload.get("primary_keyword"),
            "",
        )
        or ""
    ).strip()
    core_terms = [
        _keyword_text(k) for k in entries if str(k.get("bucket") or "").lower() == "core"
    ]
    if primary:
        core_terms.insert(0, primary)
    core_terms = [t for t in core_terms if t]
    if core_terms and not any(t.lower() in title_lc for t in core_terms):
        warnings.append(
            f"title_missing_core_keyword: 标题未包含核心词（{core_terms[0]}），AI 可能判不准品类"
        )

    if title and len(title) > 50:
        head = title[:50].lower()
        if core_terms and not any(t.lower() in head for t in core_terms):
            warnings.append("title_core_keyword_after_50c: 核心词未出现在标题前 50 字符")

    if highlights:
        shared = _phrases(title, DUP_PHRASE_WORDS) & _phrases(highlights, DUP_PHRASE_WORDS)
        if shared:
            warnings.append(
                f"title_highlights_duplicate_phrase: Title 与 Item Highlights 重复短语「{sorted(shared)[0]}」"
            )
        labeled = [k for k in entries if str(k.get("bucket") or "").strip()]
        buckets = {
            str(k.get("bucket") or "").lower()
            for k in labeled
            if str(k.get("field") or "").lower() in {"highlights", "item_highlights"}
        }
        if labeled and not (buckets & {"scenario", "attribute"}):
            warnings.append("highlights_missing_scenario: Item Highlights 未埋入场景词或属性词")

    if entries and any(
        str(k.get("bucket") or "").lower() == "pain" and str(k.get("field") or "").lower() == "title"
        for k in entries
    ):
        warnings.append("pain_keyword_in_title: 痛点词应交给五点，不占用 75 字符标题")

    meta = _dict(payload.get("meta"))
    # 未声明 keyword_source 时保持沉默（兼容旧调用）；显式声明为无数据才提醒。
    if str(meta.get("keyword_source") or "").lower() in {"none", "heuristic"}:
        warnings.append("keyword_source_unavailable: 未接入 SIF/流量词数据，埋词为推导结果，禁止对外声称搜索量")
    fetch_count = meta.get("keyword_fetch_count")
    if isinstance(fetch_count, int) and fetch_count > 0:
        warnings.append(f"keyword_fetch_used: 本次额外发起了 {fetch_count} 次关键词检索（默认应为 0）")

    return warnings


def _keyword_notes(payload: dict[str, Any], title: str, highlights: str) -> str:
    """埋词说明：一格讲清「哪个词埋在哪、什么桶、什么词源、哪些词交给了下游」。

    Excel 与前端工作台都直接渲染这一段字符串，保证两边口径一致。
    """
    entries = _keyword_entries(payload)
    strategy = _dict(payload.get("strategy"))
    meta = _dict(payload.get("meta"))

    def _label(entry: dict[str, Any]) -> str:
        text = _keyword_text(entry)
        bucket = BUCKET_LABEL.get(str(entry.get("bucket") or "").lower(), "")
        return f"{text}（{bucket}）" if bucket else text

    def _field_of(entry: dict[str, Any]) -> str:
        field = str(entry.get("field") or "").lower()
        if field in {"highlights", "item_highlights"}:
            return "highlights"
        if field == "title":
            return "title"
        text = _keyword_text(entry).lower()
        if text and text in highlights.lower() and text not in title.lower():
            return "highlights"
        return "title"

    lines: list[str] = []
    for field, prefix in (("title", "标题"), ("highlights", "Highlights")):
        picked = [_label(e) for e in entries if _field_of(e) == field and _keyword_text(e)]
        if picked:
            lines.append(f"{prefix}：{'、'.join(picked)}")

    handoff = _dict(_first_value(strategy.get("handoff_keywords"), payload.get("handoff_keywords"), {}))
    for key, prefix in (("bullets", "交五点"), ("backend", "交后台")):
        words = [str(w).strip() for w in _list(handoff.get(key)) if str(w).strip()]
        if words:
            lines.append(f"{prefix}：{'、'.join(words)}")

    source = str(meta.get("keyword_source") or "").lower()
    if source:
        note = SOURCE_LABEL.get(source, source)
        fetch = meta.get("keyword_fetch_count")
        if isinstance(fetch, int) and fetch > 0:
            note += f" · 额外检索 {fetch} 次"
        lines.append(f"词源：{note}")

    return "\n".join(lines)


def _audit_migration(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """migration_map 去向审计：硬规格不得被 dropped。"""
    errors: list[str] = []
    warnings: list[str] = []
    strategy = payload.get("strategy") if isinstance(payload.get("strategy"), dict) else {}
    entries = [
        m
        for m in _list(_first_value(strategy.get("migration_map"), payload.get("migration_map"), []))
        if isinstance(m, dict)
    ]
    for item in entries:
        target = str(item.get("to") or "").strip().lower()
        segment = str(item.get("segment") or "").strip()
        if target and target not in MIGRATION_TARGETS:
            warnings.append(
                f"migration_target_unknown: 「{segment or target}」的去向 {target} 不在 "
                f"title/highlights/bullets/backend_attributes/aplus/dropped 之内"
            )
        if target == "dropped":
            if not str(item.get("reason") or "").strip():
                warnings.append(f"migration_dropped_without_reason: 「{segment}」被丢弃但未写明原因")
            if segment and HARD_SPEC_RE.search(segment):
                errors.append(f"migration_hard_spec_dropped: 硬规格「{segment}」不允许直接丢弃，请迁往五点或后台属性")
    return errors, warnings


def _first_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _normalize_product(payload: dict[str, Any]) -> dict[str, Any]:
    product = _dict(payload.get("product"))
    facts = _dict(payload.get("product_facts"))
    target = _dict(payload.get("target_detail"))
    return {
        "product_id": _first_value(product.get("product_id"), product.get("productId"), payload.get("product_id"), payload.get("productId")),
        "sku_id": _first_value(product.get("sku_id"), product.get("skuId"), payload.get("sku_id"), payload.get("skuId")),
        "listing_id": _first_value(product.get("listing_id"), product.get("listingId"), payload.get("listing_id"), payload.get("listingId")),
        "sku": _first_value(product.get("sku"), facts.get("sku"), payload.get("sku")),
        "asin": _first_value(product.get("asin"), target.get("asin"), facts.get("asin"), payload.get("asin")),
        "product_name": _first_value(
            product.get("product_name"),
            product.get("productName"),
            facts.get("product_name"),
            facts.get("productName"),
            facts.get("name"),
            payload.get("product_name"),
        ),
        "brand": _first_value(product.get("brand"), facts.get("brand"), payload.get("brand")),
        "marketplace": _first_value(product.get("marketplace"), facts.get("marketplace"), payload.get("marketplace")),
        "category": _first_value(product.get("category"), facts.get("category"), payload.get("category")),
    }


def _normalize_policy(payload: dict[str, Any]) -> dict[str, Any]:
    incoming = _dict(payload.get("policy"))
    meta = _dict(payload.get("meta"))
    media = _is_media(payload)
    classic = _task_mode(payload) == "classic"
    default_policy_id = "classic_title_only" if classic else "compact_75"
    default_policy_version = "platform-configured" if classic else POLICY_VERSION
    default_title_max = CLASSIC_TITLE_MAX if classic else (None if media else TITLE_MAX)
    default_highlights_max = 0 if classic or media else HIGHLIGHTS_MAX
    return {
        "policy_id": default_policy_id if classic else _first_value(incoming.get("policy_id"), incoming.get("policyId"), meta.get("amazon_title_policy"), default_policy_id),
        "policy_version": _first_value(incoming.get("policy_version"), incoming.get("policyVersion"), default_policy_version),
        "marketplace": _first_value(incoming.get("marketplace"), payload.get("platform"), _normalize_product(payload).get("marketplace")),
        "title_max": _first_value(incoming.get("title_max"), incoming.get("titleMax"), payload.get("title_max"), default_title_max),
        "item_highlights_max": 0 if classic else _first_value(
            incoming.get("item_highlights_max"), incoming.get("itemHighlightsMax"), default_highlights_max
        ),
        "media_exempt": media,
    }


def _normalize_row(
    payload: dict[str, Any],
    *,
    row_index: int,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    task_mode = _task_mode(payload)
    product = _normalize_product(payload)
    source_block = _dict(payload.get("source"))
    result_block = _dict(payload.get("result"))
    strategy_block = _dict(payload.get("strategy"))
    meta = _dict(payload.get("meta"))

    legacy_title = str(
        _first_value(
            source_block.get("title"),
            payload.get("legacy_title"),
            payload.get("source_title"),
            "",
        )
        or ""
    )
    title = str(_first_value(result_block.get("title"), payload.get("title"), "") or "")
    item_highlights = str(
        _first_value(
            result_block.get("item_highlights"),
            result_block.get("itemHighlights"),
            payload.get("item_highlights"),
            payload.get("itemHighlights"),
            "",
        )
        or ""
    )
    migration_map = _list(
        _first_value(strategy_block.get("migration_map"), payload.get("migration_map"), [])
    )
    used_keywords = _list(
        _first_value(strategy_block.get("used_keywords"), payload.get("used_keywords"), [])
    )
    rationale = str(
        _first_value(strategy_block.get("rationale"), payload.get("rationale"), "") or ""
    )
    status = "failed" if errors else ("review" if warnings else str(payload.get("status") or "ok"))
    validation_notes = [*errors, *warnings]
    source_mode = str(
        payload.get("source_mode")
        or ("split_legacy" if task_mode == "migrate" else "generate")
    )

    row = {
        "row_id": str(
            _first_value(
                payload.get("row_id"),
                product.get("listing_id"),
                product.get("sku_id"),
                product.get("asin"),
                f"row_{row_index}",
            )
        ),
        "row_index": row_index,
        # 写回原表时的目标工作表行号（表头占第 1 行）；批量保存脚本负责解析
        "target_row": payload.get("target_row"),
        "writeback_blocked": payload.get("writeback_blocked") is True,
        "batch_id": payload.get("batch_id"),
        "task_mode": task_mode,
        "source_mode": source_mode,
        "policy": _normalize_policy(payload),
        "product": product,
        "source": {
            "title": legacy_title or None,
            "title_char_count": len(legacy_title) if legacy_title else 0,
            "item_highlights": _first_value(
                source_block.get("item_highlights"),
                source_block.get("itemHighlights"),
                payload.get("legacy_item_highlights"),
            ),
        },
        "result": {
            "title": title,
            "title_char_count": len(title),
            "item_highlights": item_highlights,
            "item_highlights_char_count": len(item_highlights),
        },
        "strategy": {
            "primary_keyword": _first_value(
                strategy_block.get("primary_keyword"),
                payload.get("primary_keyword"),
            ),
            "used_keywords": used_keywords,
            "required_terms": _list(
                _first_value(strategy_block.get("required_terms"), payload.get("required_terms"), [])
            ),
            "rationale": rationale,
            "migration_map": migration_map,
            "keyword_plan": _first_value(
                strategy_block.get("keyword_plan"),
                strategy_block.get("keyword_plan_used"),
                payload.get("keyword_plan_used"),
                payload.get("keyword_plan"),
                {},
            ),
            "handoff_keywords": _first_value(
                strategy_block.get("handoff_keywords"), payload.get("handoff_keywords"), {}
            ),
            "ai_question_coverage": _list(
                _first_value(
                    strategy_block.get("ai_question_coverage"),
                    payload.get("ai_question_coverage"),
                    [],
                )
            ),
        },
        "validation": {
            "status": status,
            "errors": errors,
            "warnings": warnings,
        },
        "meta": meta,
        # Flat fields are intentionally retained for existing renderers and downstream writers.
        "product_id": product.get("product_id"),
        "sku_id": product.get("sku_id"),
        "listing_id": product.get("listing_id"),
        "sku": product.get("sku"),
        "asin": product.get("asin"),
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "marketplace": product.get("marketplace"),
        "category": product.get("category"),
        "legacy_title": legacy_title,
        "title": title,
        "title_char_count": len(title),
        "item_highlights": item_highlights,
        "item_highlights_char_count": len(item_highlights),
        "migration_map": migration_map,
        "used_keywords": used_keywords,
        "rationale": rationale,
        "keyword_notes": _keyword_notes(payload, title, item_highlights),
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "validation_notes": validation_notes,
    }
    return row


def build_workbench_payload(
    rows_with_validation: list[tuple[dict[str, Any], list[str], list[str]]],
    *,
    source_file: str | None = None,
) -> dict[str, Any]:
    rows = [
        _normalize_row(payload, row_index=int(payload.get("row_index") or position), errors=errors, warnings=warnings)
        for position, (payload, errors, warnings) in enumerate(rows_with_validation, start=1)
    ]
    statuses = [row["status"] for row in rows]
    task_modes = sorted({row["task_mode"] for row in rows})
    task_mode = task_modes[0] if len(task_modes) == 1 else "mixed"
    row_policies = [row["policy"] for row in rows]
    if row_policies and all(policy == row_policies[0] for policy in row_policies[1:]):
        policy = row_policies[0]
    elif row_policies:
        versions = sorted({str(item.get("policy_version") or "") for item in row_policies})
        policy = {
            "policy_id": "mixed",
            "policy_version": versions[0] if len(versions) == 1 else "mixed",
            "marketplace": "mixed",
            "title_max": None,
            "item_highlights_max": None,
            "media_exempt": None,
        }
    else:
        policy = _normalize_policy({})
    primary = rows[0] if len(rows) == 1 else None

    payload: dict[str, Any] = {
        "schema": WORKBENCH_SCHEMA,
        "type": WORKBENCH_TYPE,
        "workbench_title": "多平台 Title 工作台" if task_mode == "classic" else "Amazon Title 工作台",
        "task_mode": task_mode,
        "policy": policy,
        "summary": {
            "total": len(rows),
            "ok": statuses.count("ok"),
            "review": statuses.count("review"),
            "failed": statuses.count("failed"),
        },
        "columns": WORKBENCH_COLUMNS,
        "rows": rows,
        "view": {
            "component": "titleWorkbench",
            "single": "card",
            "batch": "table",
        },
        "source_file": source_file,
        # Excel 交付物路径由导出器回填；前端据此提供「下载 Excel」入口。
        "artifacts": {"xlsx": None},
        # Fixed compatibility aliases. Existing consumers can keep reading the old flat shape.
        "source_mode": primary.get("source_mode") if primary else "mixed",
        "legacy_title": primary.get("legacy_title") if primary else None,
        "title": primary.get("title") if primary else None,
        "item_highlights": primary.get("item_highlights") if primary else None,
        "title_char_count": primary.get("title_char_count") if primary else None,
        "item_highlights_char_count": primary.get("item_highlights_char_count") if primary else None,
        "migration_map": primary.get("migration_map") if primary else [],
        "used_keywords": primary.get("used_keywords") if primary else [],
        "rationale": primary.get("rationale") if primary else None,
        "meta": primary.get("meta") if primary else {},
    }
    payload["generated_title"] = primary.get("title") if primary else None
    payload["row_count"] = len(rows)
    payload["ok_count"] = statuses.count("ok")
    payload["review_count"] = statuses.count("review")
    payload["failed_count"] = statuses.count("failed")
    return payload


def attach_xlsx_artifact(
    workbench_payload: dict[str, Any],
    *,
    source_file: str | None = None,
    out: str | None = None,
    strict: bool = False,
) -> str | None:
    """导出 Excel 并回填路径；strict=True 时导出失败即终止默认交付。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    try:
        from export_title_xlsx import export  # type: ignore

        path = str(export(workbench_payload, out=out, source_file=source_file))
    except Exception as exc:  # noqa: BLE001 — strict 决定失败是终止还是保留 JSON
        if strict:
            raise RuntimeError(f"XLSX 导出失败: {exc}") from exc
        print(f"⚠️ XLSX 导出失败（JSON 仍会落盘）: {exc}", file=sys.stderr)
        return None
    artifacts = workbench_payload.setdefault("artifacts", {})
    if isinstance(artifacts, dict):
        artifacts["xlsx"] = path
    return path


def apply_spec_to_policy(payload: dict[str, Any], spec: dict | None) -> None:
    """把用户 spec 的限值同步进 policy，让 Excel 与工作台 charMeter 按真实上限渲染。"""
    if not spec:
        return
    policy = payload.setdefault("policy", {})
    if not isinstance(policy, dict):
        return
    title_max, title_layer = resolve_limit(spec, "title", "max", TITLE_MAX)
    if title_layer == "user_spec":
        policy["title_max"] = title_max
        policy["policy_id"] = "user_spec"
    if not field_enabled(spec, "item_highlights"):
        policy["item_highlights_max"] = 0
        policy["policy_id"] = "user_spec"
    else:
        hl_max, hl_layer = resolve_limit(spec, "item_highlights", "max", HIGHLIGHTS_MAX)
        if hl_layer == "user_spec":
            policy["item_highlights_max"] = hl_max
            policy["policy_id"] = "user_spec"


def main() -> None:
    argv, spec = extract_spec_arg(sys.argv[1:])
    export_xlsx = "--xlsx" in argv
    argv = [a for a in argv if a != "--xlsx"]

    try:
        payload = json.loads(_read_input(argv))
    except json.JSONDecodeError as e:
        print(f"输入不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    apply_spec_to_policy(payload, spec)
    errors, warnings = _validate(payload, spec)
    if errors:
        print(f"❌ schema 校验未通过（{len(errors)} 处，未落盘）:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from linkfox_save import save_json_payload  # type: ignore

    workbench_payload = build_workbench_payload([(payload, errors, warnings)])
    if export_xlsx:
        attach_xlsx_artifact(workbench_payload)
    primary = workbench_payload["rows"][0]
    summary = [
        "已落盘 Title + Item Highlights。",
        f"  task_mode: {primary.get('task_mode')}",
        f"  title: {primary.get('title_char_count')}c — {str(primary.get('title', ''))[:80]}",
        f"  item_highlights: {primary.get('item_highlights_char_count')}c — {str(primary.get('item_highlights', ''))[:80]}",
    ]
    if warnings:
        summary.append(f"⚠️ {len(warnings)} 条提醒（已落盘）")
        for w in warnings[:5]:
            summary.append(f"  - {w}")

    xlsx_path = _dict(workbench_payload.get("artifacts")).get("xlsx")
    if xlsx_path:
        summary.append(f"  xlsx: {xlsx_path}")

    save_json_payload(SLUG, workbench_payload, summary_lines=summary)

    if xlsx_path:
        print(f"XLSX artifact: {xlsx_path}")


if __name__ == "__main__":
    main()
