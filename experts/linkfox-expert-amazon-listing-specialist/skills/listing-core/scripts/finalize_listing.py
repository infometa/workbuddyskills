#!/usr/bin/env python3
"""Finalize one portable listing-core run to JSON and Markdown artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_manifest import set_final


def _load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def _require_draft(draft: dict[str, Any]) -> None:
    required_types = {
        "title": str,
        "item_highlights": list,
        "bullets": list,
        "description": str,
        "search_terms": str,
    }
    for field, expected in required_types.items():
        if field not in draft:
            raise ValueError(f"missing draft field: {field}")
        if not isinstance(draft[field], expected):
            raise TypeError(f"draft.{field} must be {expected.__name__}")
    if any(not draft[field].strip() for field in ("title", "description", "search_terms")):
        raise ValueError("title, description and search_terms must not be empty")
    if len(draft["bullets"]) != 5 or any(
        not isinstance(item, str) or not item.strip() for item in draft["bullets"]
    ):
        raise ValueError("draft.bullets must contain exactly five non-empty strings")
    if len(draft["item_highlights"]) != 1 or any(
        not isinstance(item, str) or not item.strip() for item in draft["item_highlights"]
    ):
        raise ValueError("draft.item_highlights must contain exactly one non-empty string")
    if re.match(r"^\s*(?:[-*•‣▪●]|\d+[.)])\s+", draft["item_highlights"][0]) or any(
        char in draft["item_highlights"][0] for char in "\r\n"
    ):
        raise ValueError("draft.item_highlights must be one line without bullet prefixes")


def _require_qa_pass(report: dict[str, Any]) -> None:
    failed = [
        field
        for field, result in (report.get("fields") or {}).items()
        if isinstance(result, dict) and result.get("status") == "fail"
    ]
    unsupported = (report.get("fact_faithfulness") or {}).get("unsupported_claims") or []
    if failed:
        raise ValueError(f"quality gate failed fields: {', '.join(failed)}")
    if unsupported:
        raise ValueError("unsupported factual claims remain: " + ", ".join(map(str, unsupported)))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _keyword_report(spec: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = _as_list(spec.get("keyword_evidence"))
    if evidence:
        return [item for item in evidence if isinstance(item, dict) and item.get("term")]
    fields = {
        "core_to_title": ("P0", ["Title"]),
        "scene_to_bullets": ("P1", ["Bullet Points"]),
        "pain_to_bullets": ("P1", ["Bullet Points"]),
        "attribute_to_highlights": ("P2", ["Item Highlights", "Attributes"]),
    }
    rows: list[dict[str, Any]] = []
    for key, (priority, target_fields) in fields.items():
        for term in _as_list((spec.get("keywords") or {}).get(key)):
            if isinstance(term, str) and term.strip():
                rows.append({
                    "term": term,
                    "priority": priority,
                    "fields": target_fields,
                    "source": "keyword_plan",
                })
    return rows


def _risk_report(report: dict[str, Any]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for field, result in (report.get("fields") or {}).items():
        if not isinstance(result, dict):
            continue
        for issue in _as_list(result.get("issues")):
            if not isinstance(issue, dict):
                continue
            risks.append({
                "type": field,
                "word": str(issue.get("code") or "check"),
                "state": str(result.get("status") or "warn"),
                "reason": str(issue.get("detail") or ""),
                "recommendation": str(issue.get("replacement") or ""),
            })
    return risks


def _score_panel(report: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    issues = []
    for field, result in (report.get("fields") or {}).items():
        if not isinstance(result, dict):
            continue
        state = str(result.get("status") or "warn")
        evidence.append(f"{field}: {state}")
        issues.extend(
            str(issue.get("detail") or "")
            for issue in _as_list(result.get("issues"))
            if isinstance(issue, dict) and issue.get("detail")
        )
    gate_state = "warn" if issues else "ok"
    return {
        "overall": None,
        "grade": "—",
        "gradeText": "未运行独立质量评分",
        "basis": "Core 基础字段质量门；非 canonical quality score",
        "insufficientData": True,
        "hardGates": [],
        "items": [{
            "key": "core_field_gate",
            "name": "基础字段质量门",
            "score": None,
            "weight": None,
            "state": gate_state,
            "note": "; ".join(issues) if issues else "字段结构与本地门禁已通过",
            "evidence": evidence,
            "deductions": [],
            "recommendation": "需要数字评分时调用 listing-quality-scorer",
        }],
    }


def build_ai_readiness(draft: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    questions = []
    for item in _as_list(draft.get("question_coverage")):
        if not isinstance(item, dict) or not item.get("question"):
            continue
        questions.append({
            "question": str(item["question"]),
            "source": str(item.get("source") or "insight"),
            "answered_by": list(item.get("answered_by") or []),
            "strength": item.get("strength") if item.get("strength") in {"explicit", "weak"} else "weak",
            "alexa_probe": {"probed": False},
        })
    supplied = draft.get("four_pillars") or {}
    allowed = {"pass", "weak", "miss"}
    structural = {
        "what": "pass" if draft.get("title") else "miss",
        "who_scene": "weak" if draft.get("item_highlights") else "miss",
        "pain_solution": "weak" if len(draft.get("bullets") or []) >= 3 else "miss",
        "trust_boundary": "weak" if len(draft.get("bullets") or []) >= 5 else "miss",
    }
    pillars = {
        key: supplied.get(key) if supplied.get(key) in allowed else value
        for key, value in structural.items()
    }
    fixes = list(draft.get("fix_suggestions") or [])
    if not questions:
        fixes.append({
            "field": "bullets",
            "reason": "未提供买家问题承接映射",
            "suggestion": "根据 Product Detail 评论摘要补齐 question_coverage",
        })
    return {
        "kind": "listingAiReadiness",
        "schema_version": 1,
        "marketplace": spec.get("marketplace") or "US",
        "four_pillars": pillars,
        "questions": questions,
        "fix_suggestions": fixes,
    }


def _agent_listing_bundle(
    draft: dict[str, Any],
    spec: dict[str, Any],
    report: dict[str, Any],
    ai: dict[str, Any],
    score_panel: dict[str, Any] | None = None,
) -> dict[str, Any]:
    brands = (spec.get("brands") or {}).get("owned") or []
    product_name = str(draft.get("product_name") or spec.get("product_type") or draft["title"])
    seller_sku = str(draft.get("seller_sku") or draft.get("sku") or "")
    listing = {
        "title": draft["title"],
        "itemHighlights": draft["item_highlights"],
        "bullets": draft["bullets"],
        "description": draft["description"],
        "backendTerms": draft["search_terms"],
        "subjectMatter": draft.get("subject_matter") or [],
        "marketplace": spec.get("marketplace") or "US",
        "doc": {
            "backendTerms": draft["search_terms"],
            "subjectMatter": draft.get("subject_matter") or [],
            "status": "Draft",
        },
    }
    bundle = {
        "kind": "listingFinalBundle",
        "schema_version": 1,
        "mode": spec.get("mode"),
        "product": {
            "name": product_name,
            "brand": str(draft.get("brand") or (brands[0] if brands else "")),
            "category": str(spec.get("category") or ""),
            "market": str(spec.get("marketplace") or "US"),
        },
        "listing": listing,
        "researchReport": {
            "keywords": _keyword_report(spec),
            "riskTerms": _risk_report(report),
            "recommendations": [],
        },
        "scorePanel": score_panel or _score_panel(report),
        "aiReadiness": ai,
        "validation": {
            "status": "pass",
            "check_report": os.path.abspath(str(report.get("_path") or "")),
        },
    }
    if seller_sku:
        bundle["listing"]["sellerSku"] = seller_sku
    return bundle


_PDP_IMAGE_LIST_KEYS = (
    "images", "imageUrls", "image_urls", "imageList", "gallery", "productImageUrls",
)
_PDP_MAIN_IMAGE_KEYS = ("mainImage", "main_image", "image", "imageUrl", "image_url")
_PDP_PRICE_KEYS = ("price", "currentPrice", "current_price", "buyboxPrice", "buybox_price")
_PDP_LIST_PRICE_KEYS = ("listPrice", "list_price", "originalPrice", "original_price")
_PDP_NEST_KEYS = ("product", "data", "result", "detail", "projection")


def _image_src(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, dict):
        for key in ("src", "url", "link", "hiRes", "large", "media_location"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _parse_price(value: Any) -> tuple[float | None, str | None]:
    """价格既可能是数字，也可能是 '$19.99' / 'USD 19.99' 这类展示串。"""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value), None
    if isinstance(value, dict):
        amount, currency = _parse_price(value.get("value") or value.get("amount"))
        raw_currency = value.get("currency") or value.get("currencyCode")
        return amount, (str(raw_currency) if raw_currency else currency)
    if isinstance(value, str):
        match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
        if not match:
            return None, None
        currency = value.replace(match.group(), "").replace(",", "").strip() or None
        return float(match.group()), currency
    return None, None


def _pdp_media_from_product_detail(
    detail: dict[str, Any], mode: str = "",
) -> dict[str, Any]:
    """从 S1 的 product-detail 最小投影里宽进抽取图片与价格。

    投影由 agent 落盘、无固定 schema，这里只认常见字段名，认不出就留空——
    详情页预览允许无图/无价降级渲染，不允许编造。
    """
    if detail.get("kind") == "listingProductEvidence":
        target = detail.get("target")
        competitors = [
            item for item in (detail.get("competitors") or []) if isinstance(item, dict)
        ]
        # rewrite 使用本品媒体；benchmark/create 只使用参考竞品媒体，避免把本品图
        # 错标成竞品参考图。旧的裸 Product Detail 形状继续走通用分支。
        roots = [target] if mode == "rewrite" and isinstance(target, dict) else competitors
    else:
        roots = [detail]
    containers = [
        container
        for root in roots
        if isinstance(root, dict)
        for container in [root] + [
            root[key] for key in _PDP_NEST_KEYS if isinstance(root.get(key), dict)
        ]
    ]
    images: list[dict[str, str]] = []
    price: float | None = None
    list_price: float | None = None
    currency: str | None = None
    for container in containers:
        if not images:
            for key in _PDP_IMAGE_LIST_KEYS:
                value = container.get(key)
                if isinstance(value, list):
                    images = [{"src": src} for src in map(_image_src, value) if src]
                    if images:
                        break
            if not images:
                for key in _PDP_MAIN_IMAGE_KEYS:
                    src = _image_src(container.get(key))
                    if src:
                        images = [{"src": src}]
                        break
        if price is None:
            for key in _PDP_PRICE_KEYS:
                if key in container:
                    price, currency = _parse_price(container[key])
                    if price is not None:
                        break
        if list_price is None:
            for key in _PDP_LIST_PRICE_KEYS:
                if key in container:
                    list_price, list_currency = _parse_price(container[key])
                    currency = currency or list_currency
                    if list_price is not None:
                        break
    result: dict[str, Any] = {}
    if images:
        result["images"] = images
    if price is not None:
        result["price"] = price
    if list_price is not None:
        result["listPrice"] = list_price
    if currency:
        result["currency"] = currency
    return result


def _detail_preview_envelope(
    bundle: dict[str, Any],
    draft: dict[str, Any],
    spec: dict[str, Any],
    run_id: str | None,
    media: dict[str, Any],
) -> dict[str, Any]:
    """amazon-detail-preview.json（handoff §8 形态 A 信封）。

    前端 AmazonDetailPreviewRenderer 按文件名接管渲染成 Amazon 前台详情页；
    只放真实产物字段，rating/badges 这类预览无据字段一律不写。
    """
    listing = bundle["listing"]
    product = bundle["product"]
    sku = str(product.get("skuId") or "")
    entry: dict[str, Any] = {
        "id": sku or "listing-final",
        "title": listing["title"],
        "itemHighlights": " | ".join(listing["itemHighlights"]),
        "brand": product.get("brand") or None,
        "bullets": listing["bullets"],
        "description": listing["description"],
        "searchTerms": listing["backendTerms"],
        "images": [],
    }
    if sku:
        entry["sku"] = sku
    entry.update(media)
    return {
        "kind": "amazonDetailPreview",
        "schema_version": 1,
        "preview": bundle["preview"],
        "draftId": run_id,
        "marketplace": listing.get("marketplace") or "US",
        "status": "Draft",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "products": [entry],
    }


def _preview_contract(
    spec: dict[str, Any],
    listing: dict[str, Any],
    media: dict[str, Any],
) -> dict[str, Any]:
    """声明前端可展示的 PDP 能力，避免 UI 从价格或图片来源反推业务关系。"""
    mode = str(spec.get("mode") or "")
    if mode == "rewrite":
        source_relation = "own_listing"
    elif media.get("imagesSource") == "reference" or mode == "benchmark":
        source_relation = "reference"
    else:
        source_relation = "product_info"
    has_commerce_data = any(
        key in listing
        for key in ("price", "delivery", "inStock", "quantity", "soldBy", "shipsFrom")
    )
    show_commerce = source_relation == "own_listing" and has_commerce_data
    return {
        "mode": "commerce" if show_commerce else "copy",
        "sourceRelation": source_relation,
        "capabilities": {"showCommerce": show_commerce},
    }


def _format_data_confidence(value: Any) -> str:
    """data_confidence 既可能是字符串，也可能是 data-confidence-protocol 的对象形态。"""
    if isinstance(value, dict):
        overall = value.get("overall") or value.get("execution_mode") or "facts_only"
        warnings = [str(w) for w in _as_list(value.get("warnings")) if w]
        return f"{overall}（{', '.join(warnings)}）" if warnings else str(overall)
    return str(value or "facts_only")


def build_markdown(
    draft: dict[str, Any], spec: dict[str, Any], report: dict[str, Any], ai: dict[str, Any]
) -> str:
    highlights = " | ".join(draft["item_highlights"])
    bullets = "\n".join(f"{index}. {item}" for index, item in enumerate(draft["bullets"], start=1))
    subject = " ".join(draft.get("subject_matter") or [])
    coverage = report.get("coverage") or {}
    pillars = ai["four_pillars"]
    return f"""# Listing 文案

## Title
{draft['title']}

## Item Highlights
{highlights}

## Bullet Points
{bullets}

## Product Description
{draft['description']}

## Search Terms
{draft['search_terms']}

## Subject Matter
{subject}

## 算法与 AI 导购验收摘要
- Marketplace：{spec.get('marketplace', 'US')}
- A10 相关性：标题核心词命中 {len(coverage.get('title_core_hit') or [])}，缺失 {len(coverage.get('title_core_miss') or [])}
- 场景/痛点词覆盖：{coverage.get('bullets_scene_pain_pct', 'N/A')}%
- AI 导购内容四柱：what={pillars['what']}；who_scene={pillars['who_scene']}；pain_solution={pillars['pain_solution']}；trust_boundary={pillars['trust_boundary']}（内容结构检查，不代表平台在线实测）
- 数据置信度：{_format_data_confidence(draft.get('data_confidence'))}
"""


def _load_score_panel(score_result_path: str | None) -> dict[str, Any] | None:
    if not score_result_path:
        return None
    score_result = _load_json(score_result_path)
    panel = score_result.get("scorePanel")
    if not isinstance(panel, dict):
        raise ValueError("score result must contain scorePanel")
    if "overall" not in panel or not isinstance(panel.get("items"), list):
        raise ValueError("scorePanel must contain overall and items")
    return panel


def finalize(
    manifest_path: str,
    draft_path: str,
    spec_path: str,
    check_report_path: str,
    output_dir: str | None = None,
    seller_sku: str | None = None,
    brand_name: str | None = None,
    product_detail_path: str | None = None,
    score_result_path: str | None = None,
) -> dict[str, str]:
    manifest_abs = os.path.abspath(manifest_path)
    draft = _load_json(draft_path)
    if seller_sku:
        draft["seller_sku"] = seller_sku
    if brand_name:
        draft["brand"] = brand_name
    spec = _load_json(spec_path)
    report = _load_json(check_report_path)
    report["_path"] = os.path.abspath(check_report_path)
    _require_draft(draft)
    _require_qa_pass(report)

    out_dir = Path(output_dir).resolve() if output_dir else Path(manifest_abs).parent / "03-write"
    out_dir.mkdir(parents=True, exist_ok=True)
    final_json = out_dir / "listing-final.json"
    final_md = out_dir / "listing-final.md"
    ai_json = out_dir / "ai-readiness.json"
    detail_preview_json = out_dir / "amazon-detail-preview.json"

    ai = build_ai_readiness(draft, spec)
    score_panel = _load_score_panel(score_result_path)
    # 详情页预览的图片/价格来源按模式区分：
    # rewrite（本品 ASIN）→ 图片+价格照常注入，imagesSource=own；
    # benchmark/create（参考竞品）→ 只注入图片且逐张标注「参考图」、imagesSource=reference，
    #   价格丢弃——竞品价格冒充本品定价比竞品图更误导。
    media: dict[str, Any] = {}
    detail_path = Path(
        product_detail_path
        or Path(manifest_abs).parent / "01-facts" / "product-detail.json"
    )
    if detail_path.is_file():
        try:
            media = _pdp_media_from_product_detail(
                _load_json(str(detail_path)), str(spec.get("mode") or ""),
            )
        except (ValueError, json.JSONDecodeError):
            media = {}
    if media:
        if str(spec.get("mode") or "") == "rewrite":
            media["imagesSource"] = "own"
        else:
            images = media.get("images") or []
            for image in images:
                image["alt"] = "参考图（竞品）"
            media = {"images": images, "imagesSource": "reference"} if images else {}

    bundle = _agent_listing_bundle(draft, spec, report, ai, score_panel)
    # rewrite 的本品图片/价格进入最终 bundle；benchmark/create 的竞品参考图只留在
    # 详情预览信封，不得混进正式 Listing。
    if media.get("imagesSource") == "own":
        for key in ("images", "price", "listPrice", "currency", "imagesSource"):
            if key in media:
                bundle["listing"][key] = media[key]
    bundle["preview"] = _preview_contract(spec, bundle["listing"], media)

    _write_json(final_json, bundle)
    _write_json(ai_json, ai)
    final_md.write_text(build_markdown(draft, spec, report, ai), encoding="utf-8")
    try:
        manifest_doc = _load_json(manifest_abs)
    except (ValueError, json.JSONDecodeError):
        manifest_doc = {}
    _write_json(
        detail_preview_json,
        _detail_preview_envelope(bundle, draft, spec, manifest_doc.get("run_id"), media),
    )

    set_final(
        manifest_abs,
        listing_json=str(final_json),
        listing_md=str(final_md),
        check_report=os.path.abspath(check_report_path),
        ai_readiness=str(ai_json),
        detail_preview=str(detail_preview_json),
        score_report=os.path.abspath(score_result_path) if score_result_path else None,
    )
    paths = {
        "listing_json": str(final_json),
        "listing_md": str(final_md),
        "check_report": os.path.abspath(check_report_path),
        "ai_readiness": str(ai_json),
        "detail_preview": str(detail_preview_json),
        "manifest": manifest_abs,
    }
    if score_result_path:
        paths["score_report"] = os.path.abspath(score_result_path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize portable listing-core outputs")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--check-report", required=True)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--seller-sku", default=None)
    parser.add_argument("--brand-name", default=None)
    parser.add_argument("--product-detail", default=None)
    parser.add_argument("--score-result", default=None)
    args = parser.parse_args()
    paths = finalize(
        manifest_path=args.manifest,
        draft_path=args.draft,
        spec_path=args.spec,
        check_report_path=args.check_report,
        output_dir=args.out_dir,
        seller_sku=args.seller_sku,
        brand_name=args.brand_name,
        product_detail_path=args.product_detail,
        score_result_path=args.score_result,
    )
    # 传输层协议：一次 Bash 输出只允许一行 `Saved full response:`，bridge 只认第一行。
    # 主产物走该行，其余伴生产物走扩展名 artifact 行。
    print(f"Saved full response: {paths['listing_json']}")
    print(f"Markdown artifact: {paths['listing_md']}")
    print(f"JSON artifact: {paths['ai_readiness']}")
    print(f"JSON artifact: {paths['detail_preview']}")
    if paths.get("score_report"):
        print(f"JSON artifact: {paths['score_report']}")
    print(f"JSON artifact: {paths['manifest']}")


if __name__ == "__main__":
    main()
