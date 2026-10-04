#!/usr/bin/env python3
"""build_spec — 写作契约装配（Task 3）。

将 listing_spec 的双层限值（DEFAULTS + 可选 user_spec）、品牌互斥校验、
关键词布局、类目自适应 bullet_plan、风格与合规库路径，装配成 L4 writer
和 Task 4 validate_fields 共用的 listingWritingSpec 结构。

本脚本永不修改文案，只做限值解析与结构装配。

用法（库）：
    from build_spec import assemble_spec
    spec = assemble_spec("benchmark", ["Rocktone"], ["BrandX"], keywords, ["diy"])

用法（CLI）：
    python3 build_spec.py --mode benchmark --out /abs/spec.json \\
        --brands-owned Rocktone --brands-competitor BrandX,BrandY \\
        --keywords /abs/keywords.json --category-flags diy,dimension \\
        --output-language en_US
"""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from listing_spec import resolve_limit, validate_spec
from save_buyer_questions import question_items

_BANNED_LIBRARY_PATH = str(
    (Path(__file__).resolve().parent / "restricted-content-v1.json")
)

_LOCALE_BY_LANGUAGE = {
    "en_US": "en_US",
    "en_GB": "en_GB",
    "en_CA": "en_CA",
    "de_DE": "de_DE",
    "fr_FR": "fr_FR",
    "it_IT": "it_IT",
    "es_ES": "es_ES",
    "es_MX": "es_MX",
    "ja_JP": "ja_JP",
}

_LANGUAGE_BY_MARKETPLACE = {
    "US": "en_US",
    "UK": "en_GB",
    "CA": "en_CA",
    "DE": "de_DE",
    "FR": "fr_FR",
    "IT": "it_IT",
    "ES": "es_ES",
    "MX": "es_MX",
    "JP": "ja_JP",
}

_REWRITE_FIELDS = {
    "title", "item_highlights", "bullets", "description", "search_terms",
    "structured_attributes", "subject_matter",
}


def _normalize_rewrite_handoff(mode: str, handoff: dict[str, Any] | None) -> dict[str, Any] | None:
    if handoff is None:
        return None
    if mode != "rewrite":
        raise ValueError("audit handoff is only valid for mode=rewrite")
    if handoff.get("kind") == "listingAuditReport" and isinstance(handoff.get("auditHandoff"), dict):
        handoff = handoff["auditHandoff"]
    if handoff.get("kind") != "listingAuditHandoff" or handoff.get("schema_version") != 1:
        raise ValueError("invalid listingAuditHandoff kind/schema_version")
    actions = handoff.get("field_actions") or []
    if not isinstance(actions, list):
        raise ValueError("listingAuditHandoff.field_actions must be an array")
    normalized_actions = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or action.get("field") not in _REWRITE_FIELDS:
            raise ValueError(f"invalid field_actions[{index}].field")
        normalized_actions.append({
            "field": action["field"],
            "priority": action.get("priority") or "medium",
            "problem": action.get("problem") or "",
            "evidence": list(action.get("evidence") or []),
            "objective": action.get("objective") or "",
            "constraints": list(action.get("constraints") or []),
            "expected_direction": action.get("expected_direction") or "",
            "confidence": action.get("confidence") or "partial",
        })
    locked = handoff.get("locked_fields") or []
    if not isinstance(locked, list) or any(field not in _REWRITE_FIELDS for field in locked):
        raise ValueError("listingAuditHandoff.locked_fields contains an invalid field")
    if set(locked) & {action["field"] for action in normalized_actions}:
        raise ValueError("a field cannot be both locked and targeted for rewrite")
    return {
        "kind": "listingAuditHandoff",
        "schema_version": 1,
        "target": dict(handoff.get("target") or {}),
        "source_listing_path": handoff.get("source_listing_path") or "",
        "evidence_paths": dict(handoff.get("evidence_paths") or {}),
        "score_panel_path": handoff.get("score_panel_path") or "",
        "field_actions": normalized_actions,
        "operational_actions": list(handoff.get("operational_actions") or []),
        "locked_fields": locked,
        "data_freshness": dict(handoff.get("data_freshness") or {}),
    }


def _keyword_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("word") or value.get("keyword") or value.get("text") or "").strip()
    return ""


def _keyword_values(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values if isinstance(values, list) else []:
        text = _keyword_text(value)
        folded = text.casefold()
        if text and folded not in seen:
            result.append(text)
            seen.add(folded)
    return result


def _keyword_evidence(keywords: dict[str, Any]) -> list[dict[str, Any]]:
    config = {
        "core": ("P0", ["Title"]),
        "scene": ("P1", ["Bullet Points"]),
        "pain": ("P1", ["Bullet Points"]),
        "attribute": ("P2", ["Item Highlights", "Attributes"]),
    }
    rows: list[dict[str, Any]] = []
    for group, (priority, fields) in config.items():
        for item in keywords.get(group) if isinstance(keywords.get(group), list) else []:
            term = _keyword_text(item)
            if not term:
                continue
            record = item if isinstance(item, dict) else {}
            rows.append({
                "term": term,
                "priority": str(record.get("priority") or priority),
                "fields": list(record.get("fields") or fields),
                "volume": record.get("search_volume") or record.get("volume"),
                "source": str(record.get("source") or "sif"),
                "insight": str(record.get("insight") or ""),
            })
    return rows


def _resolve_user_spec(user_spec: dict[str, Any] | None) -> dict[str, Any] | None:
    """校验 user_spec dict（若提供）不越过平台底线；越线抛 ValueError。"""
    if user_spec is None:
        return None
    errors = validate_spec(user_spec)
    if errors:
        raise ValueError("; ".join(errors))
    return user_spec


def _build_limits(spec: dict[str, Any] | None) -> dict[str, int | None]:
    title_max, _ = resolve_limit(spec, "title", "max")
    bullet_each_max, _ = resolve_limit(spec, "bullets", "each_max")
    bullet_count, _ = resolve_limit(spec, "bullets", "count")
    bullet_total_max, _ = resolve_limit(spec, "bullets", "total_max")
    description_max, _ = resolve_limit(spec, "description", "max")
    search_terms_bytes_max, _ = resolve_limit(spec, "search_terms", "bytes_max")
    item_highlights_max, _ = resolve_limit(spec, "item_highlights", "max")
    # subject_matter 无 Amazon 统一平台上限；用户 spec 未给值时为 None＝只做内容安检、不做字数裁定
    subject_matter_max, _ = resolve_limit(spec, "subject_matter", "max")
    return {
        "title_max": title_max,
        "bullet_each_max": bullet_each_max,
        "bullet_count": bullet_count,
        "bullet_total_max": bullet_total_max,
        "description_max": description_max,
        "search_terms_bytes_max": search_terms_bytes_max,
        "item_highlights_max": item_highlights_max,
        "subject_matter_max": subject_matter_max,
    }


def _generation_targets(
    limits: dict[str, int | None], spec: dict[str, Any] | None
) -> dict[str, int | None]:
    """给语义 Writer 预留少量字符/字节余量；不改变任何硬校验上限。"""
    reserves = {
        "title_max": 5,
        "item_highlights_max": 10,
        "bullet_each_max": 10,
        "description_max": 50,
        "search_terms_bytes_max": 20,
    }
    targets: dict[str, int | None] = {}
    for key, reserve in reserves.items():
        limit = limits.get(key)
        targets[key] = max(1, limit - reserve) if isinstance(limit, int) else None
    # 200 是移动端扫读友好的写作建议，不是平台硬限制。默认首稿仍瞄准 190，
    # 但用户显式传 each_max 时尊重其规格并保留 10 字符余量。
    explicit_bullet_max = bool(
        spec and isinstance(spec.get("bullets"), dict) and "each_max" in spec["bullets"]
    )
    if not explicit_bullet_max:
        targets["bullet_each_max"] = 190
    return targets


def _reserved_front_tokens(keywords: dict[str, Any]) -> list[str]:
    """预告计划进入前台的词元，帮助 Writer 首稿避免浪费后台字节。"""
    text = " ".join(
        _keyword_text(value)
        for group in ("core", "scene", "pain", "attribute")
        for value in (keywords.get(group) if isinstance(keywords.get(group), list) else [])
    )
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return list(dict.fromkeys(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)))


def _build_bullet_plan(category_flags: list[str]) -> list[str]:
    """AI 四问映射五槽（spec §12.1）：你是什么 / 谁用+场景 / 痛点方案 / 信任 / 边界。"""
    flags = {str(f).strip().lower() for f in (category_flags or [])}

    bullet_1 = "第1条：核心用途与基本性能（你是什么；含最强卖点，来自 Gap 切入点）"

    if "diy" in flags:
        bullet_2 = "第2条：适用场景与目标人群，必含使用方法/操作步骤"
    else:
        bullet_2 = "第2条：适用场景与目标人群（按对象×场景×用途细分，禁裸罗列）"

    if "dimension" in flags:
        bullet_3 = "第3条：关键功能与痛点方案（痛点→方案→效果；尺寸/规格必须延伸为使用收益）"
    else:
        bullet_3 = "第3条：关键功能与痛点方案（痛点→方案→效果）"

    bullet_4 = "第4条：材质安全、耐用度与认证（信任信号与差异化）"
    bullet_5 = (
        "第5条：使用边界与注意事项（兼容列表/参数上限/『不适用于…』排除声明，"
        "边界越清晰 AI 越敢推荐；质保/售后一句收尾，禁保证语）"
    )

    return [bullet_1, bullet_2, bullet_3, bullet_4, bullet_5]


def assemble_spec(
    mode: str,
    brands_owned: list[str],
    brands_competitor: list[str],
    keywords: dict[str, Any],
    category_flags: list[str],
    user_spec: dict[str, Any] | None = None,
    style_angle: str | None = None,
    output_language: str | None = None,
    buyer_questions: list[Any] | dict[str, Any] | None = None,
    marketplace: str = "US",
    category: str = "",
    product_type: str = "",
    profile: str = "standard",
    rewrite_handoff: dict[str, Any] | None = None,
    evidence_mode: str = "external",
    banned_terms: list[str] | None = None,
) -> dict[str, Any]:
    owned = list(brands_owned or [])
    competitor = list(brands_competitor or [])

    owned_cf = {b.casefold() for b in owned}
    competitor_cf = {b.casefold() for b in competitor}
    overlap = owned_cf & competitor_cf
    if overlap:
        raise ValueError(
            f"品牌互斥冲突：owned 与 competitor 存在重叠（大小写不敏感）：{sorted(overlap)}"
        )

    resolved_user_spec = _resolve_user_spec(user_spec)
    limits = _build_limits(resolved_user_spec)

    if evidence_mode not in {"external", "facts_only"}:
        raise ValueError(f"unsupported evidence_mode: {evidence_mode}")
    kw = keywords or {}
    has_keyword_evidence = bool(_keyword_evidence(kw))
    keywords_block = {
        "core_to_title": _keyword_values(kw.get("core")),
        "scene_to_bullets": _keyword_values(kw.get("scene")),
        "pain_to_bullets": _keyword_values(kw.get("pain")),
        # 四维分流第 4 维：属性词（材质/兼容/尺寸）进 Item Highlights 与后台属性
        "attribute_to_highlights": _keyword_values(kw.get("attribute")),
        # 词表工作台锁定词：writer 必须逐字埋入，validate 按覆盖率校验
        "locked": [w for w in (kw.get("locked") or []) if isinstance(w, str) and w.strip()],
        "integrity": has_keyword_evidence,
        "coverage_targets": {
            "title_core_pct": 100,
            "bullets_scene_pain_pct": 60,
            "search_terms_no_front_dup": True,
        },
    }

    bullet_plan = _build_bullet_plan(category_flags)

    normalized_marketplace = (marketplace or "US").strip().upper()
    resolved_language = output_language or _LANGUAGE_BY_MARKETPLACE.get(
        normalized_marketplace, "en_US"
    )
    locale = _LOCALE_BY_LANGUAGE.get(resolved_language, resolved_language)
    style = {
        "caps_lead_phrase": True,
        "arabic_numerals": True,
        "locale": locale,
        "title_formula": "品牌+核心产品词+关键属性+核心场景；前50字符必须自明产品是什么",
    }
    if style_angle:
        style["style_angle"] = style_angle

    # fast 档已 deprecate：任何 profile 取值一律按 standard 展开（兼容旧标记/旧前端）
    resolved_profile = "standard"
    rewrite_contract = _normalize_rewrite_handoff(mode, rewrite_handoff)
    audit_evidence_paths = (rewrite_contract or {}).get("evidence_paths") or {}
    reuse_audit_insight = all(
        isinstance(audit_evidence_paths.get(key), str) and audit_evidence_paths[key]
        for key in ("keywords", "buyer_questions", "insight")
    )
    # 卖家避讳词（`[卖家偏好]` 红线段）与词表工作台禁用词合流，去重保序。
    # 两者强度都等同 Layer A 违禁词，validate 按 banned_term 判 fail。
    user_banned: list[str] = []
    seen_banned: set[str] = set()
    for term in list(banned_terms or []) + list(kw.get("banned") or []):
        if not isinstance(term, str):
            continue
        term = term.strip()
        if not term or term.casefold() in seen_banned:
            continue
        seen_banned.add(term.casefold())
        user_banned.append(term)
    return {
        "kind": "listingWritingSpec",
        "writer_contract_version": 2,
        "limits": limits,
        "generation_targets": _generation_targets(limits, resolved_user_spec),
        "authoring_recommendations": {
            "bullet_each_max": (
                limits["bullet_each_max"]
                if resolved_user_spec
                and isinstance(resolved_user_spec.get("bullets"), dict)
                and "each_max" in resolved_user_spec["bullets"]
                else 200
            )
        },
        "banned_library": _BANNED_LIBRARY_PATH,
        "user_banned_terms": user_banned,
        "brands": {"owned": owned, "competitor": competitor},
        "keywords": keywords_block,
        "keyword_evidence": _keyword_evidence(kw),
        "bullet_plan": bullet_plan,
        # 买家真实问题清单（Stage 2 洞察产出）：writer 要求每条 bullet 显式回答至少一个问题
        "buyer_questions": question_items(buyer_questions) if buyer_questions is not None else [],
        "discovery_contract": {
            # 这些名称用于说明面向何种检索/理解信号写作，不声称掌握平台秘密权重。
            "search_relevance": {
                "model": "A10-facing",
                "rules": [
                    "核心产品词完整进入标题，禁止机械堆词",
                    "场景词和痛点词进入可读句子，后台词去除前台重复",
                    "相关性、可读性、转化解释力同时满足",
                ],
            },
            "semantic_graph": {
                "model": "COSMO-facing",
                "required_edges": [
                    "product_to_attribute",
                    "product_to_audience",
                    "product_to_scene",
                    "pain_to_solution",
                    "claim_to_evidence",
                ],
            },
            "shopping_assistant": {
                "models": ["Alexa for Shopping", "Rufus"],
                "four_pillars": ["what", "who_scene", "pain_solution", "trust_boundary"],
                "question_coverage_required": True,
                "boundary_statement_required": True,
            },
        },
        "field_roles": {
            "title": "说明产品是什么；前50字符自明，承接核心词",
            "item_highlights": "补充材质、用途、场景、兼容和关键差异",
            "bullets": "逐条回答买家问题；痛点→方案→证据/效果；末条写边界",
            "description": "补全使用方法、场景解释和可比较事实，不重复堆词",
            "search_terms": "承接尚未在前台出现的相关词，不含品牌词和标点",
            "structured_attributes": "输出可写入后台的事实属性，值必须可追溯",
            "subject_matter": "后台主题词，补充前台未覆盖的用途/人群/场景类目词；不含品牌词与标点",
        },
        "search_terms_contract": {
            "generation_order": "先完成 title 与 bullets，再生成 search_terms",
            "normalization": "Unicode NFKC + casefold + Unicode完整词元",
            "reserved_front_tokens": _reserved_front_tokens(kw),
            "rule": "search_terms 的任一词元若已出现在最终 title 或 bullets，必须省略；不要等待 QA 再替换",
        },
        "claim_policy": {
            "fact_source": "product-facts.md 的本品事实段",
            "competitor_context_role": "只用于结构、问题和关键词，不得作为本品事实",
            "visual_observation_role": "只描述可见外观，不推断内部结构、性能、护理或耐用度",
            "forbidden_without_explicit_fact": [
                "内部填充或厚度", "承重与稳固性", "人体工学或姿势收益",
                "护理方式", "耐用度", "认证", "价格优势或竞品比较",
            ],
        },
        "style": style,
        "fact_source": "product-facts.md",
        "mode": mode,
        "rewrite_contract": rewrite_contract,
        "profile": resolved_profile,
        "evidence_mode": evidence_mode,
        "performance_contract": {
            "provided_evidence_only": True,
            "detailed_reviews_source": "user_or_host_provided",
            "keyword_evidence_optional": True,
            "keyword_top_n": 50,
            "max_semantic_calls": 1 if reuse_audit_insight else 2,
            "max_targeted_retries": 1,
            "reuse_audit_evidence": bool(rewrite_contract),
            "reuse_audit_insight": reuse_audit_insight,
            "portable_outputs": ["json", "markdown"],
        },
        "marketplace": normalized_marketplace,
        "category": category,
        "product_type": product_type,
        "output_language": resolved_language,
    }


def _parse_csv_arg(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _load_json_file(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="build_spec — 写作契约装配")
    parser.add_argument("--mode", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--brands-owned", default="")
    parser.add_argument("--brands-competitor", default="")
    parser.add_argument("--keywords", default=None, help="keywords JSON 文件路径；facts_only 可省略")
    parser.add_argument("--category-flags", default="")
    parser.add_argument("--spec", default=None, help="user_spec JSON 文件路径")
    parser.add_argument("--style-angle", default=None)
    parser.add_argument("--output-language", default=None)
    parser.add_argument("--marketplace", default="US")
    parser.add_argument("--category", default="")
    parser.add_argument("--product-type", default="")
    parser.add_argument("--profile", choices=("fast", "standard"), default="standard")
    parser.add_argument(
        "--evidence-mode", choices=("external", "facts_only"), default="external",
        help="外部证据路径；rewrite 无 ASIN 时使用 facts_only",
    )
    parser.add_argument(
        "--buyer-questions", default=None, help="买家真实问题清单 JSON 文件路径（字符串数组）"
    )
    parser.add_argument(
        "--audit-handoff", default=None,
        help="listingAuditHandoff JSON 文件；仅 mode=rewrite 有效",
    )
    parser.add_argument(
        "--banned-terms", default="",
        help="卖家避讳词，逗号分隔；与 keywords.json 的 banned 合流，强度等同违禁词",
    )
    args = parser.parse_args()

    if args.evidence_mode == "external" and not args.keywords:
        parser.error("--keywords is required when --evidence-mode=external")
    keywords = _load_json_file(args.keywords) if args.keywords else {}
    user_spec = _load_json_file(args.spec) if args.spec else None
    buyer_questions = _load_json_file(args.buyer_questions) if args.buyer_questions else None
    rewrite_handoff = _load_json_file(args.audit_handoff) if args.audit_handoff else None

    spec = assemble_spec(
        mode=args.mode,
        brands_owned=_parse_csv_arg(args.brands_owned),
        brands_competitor=_parse_csv_arg(args.brands_competitor),
        keywords=keywords,
        category_flags=_parse_csv_arg(args.category_flags),
        user_spec=user_spec,
        style_angle=args.style_angle,
        output_language=args.output_language,
        buyer_questions=buyer_questions,
        marketplace=args.marketplace,
        category=args.category,
        product_type=args.product_type,
        profile=args.profile,
        rewrite_handoff=rewrite_handoff,
        evidence_mode=args.evidence_mode,
        banned_terms=_parse_csv_arg(args.banned_terms),
    )

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    print(f"Saved full response: {out_path}")


if __name__ == "__main__":
    main()
