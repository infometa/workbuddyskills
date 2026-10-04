#!/usr/bin/env python3
"""Create the compact, source-faithful Product Detail evidence bundle for Core."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

BULLET_KEYS = ("aboutItemFivePoint", "aboutItem", "bulletPoints", "bullets")
REVIEW_KEYS = ("title", "text", "rating", "date", "verifiedPurchase", "helpfulVotes", "position")
PASS_KEYS = (
    "asin", "title", "brand", "category", "price", "extractedPrice", "rating", "reviews",
    "productDescription", "description", "dimension", "weight", "productDetails",
    "itemSpecifications", "itemIngredients", "productImageUrls", "imageUrl", "mainImageUrl",
    "reviewsSummary", "customerReviews", "variants", "sourceTool", "sourceType",
)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _project_review(review: Any) -> dict[str, Any] | None:
    if not isinstance(review, dict):
        return None
    projected = {key: review[key] for key in REVIEW_KEYS if review.get(key) not in (None, "", [])}
    return projected or None


def project_product(product: dict[str, Any], review_limit: int = 8) -> dict[str, Any]:
    projected = {key: product[key] for key in PASS_KEYS if product.get(key) not in (None, "", [])}
    bullets: list[str] = []
    bullet_source = None
    for key in BULLET_KEYS:
        bullets = _texts(product.get(key))
        if bullets:
            bullet_source = key
            break
    projected["aboutItemFivePoint"] = bullets
    projected["field_provenance"] = {"bullets": bullet_source}
    reviews = [
        item for item in (_project_review(review) for review in (product.get("authorsReviews") or []))
        if item is not None
    ][:review_limit]
    projected["authorsReviews"] = reviews
    projected["evidence_strength"] = {
        "title": "verified" if _text(product.get("title")) else "unavailable",
        "bullets": "verified" if bullets else "unavailable",
        "reviews": "verified" if reviews else "weak",
        "specifications": "verified" if product.get("itemSpecifications") or product.get("productDetails") else "partial",
    }
    return projected


def _by_asin(products: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        str(product.get("asin") or "").upper(): product
        for product in products if isinstance(product, dict) and product.get("asin")
    }


def _missing_competitor(asin: str) -> dict[str, Any]:
    """保留请求顺序并显式标弱；竞品缺失不能阻断本品交付或触发备用案例。"""
    return {
        "asin": asin.strip().upper(),
        "aboutItemFivePoint": [],
        "authorsReviews": [],
        "field_provenance": {"bullets": None},
        "evidence_strength": {
            "title": "unavailable",
            "bullets": "unavailable",
            "reviews": "weak",
            "specifications": "unavailable",
        },
        "missing_from_response": True,
    }


def _normalize_asin_args(values: list[str]) -> list[str]:
    """兼容 argparse append 的标准形式和历史逗号拼接形式。"""
    normalized: list[str] = []
    for value in values:
        normalized.extend(part.strip() for part in value.split(",") if part.strip())
    return list(dict.fromkeys(normalized))


def build_bundle(
    payload: Any,
    target_asin: str | None,
    competitor_asins: list[str],
    review_limit: int,
    own_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    products = payload.get("products") if isinstance(payload, dict) else None
    if not isinstance(products, list):
        raise ValueError("Product Detail response must contain products[]")
    index = _by_asin(products)
    target_key = (target_asin or "").strip().upper()
    if target_key and target_key not in index:
        raise ValueError(f"target ASIN not found: {target_asin}")
    if not target_key and not own_facts:
        raise ValueError("create projection requires --own-facts when --target-asin is absent")
    if target_key:
        target = project_product(index[target_key], review_limit)
        target["factSource"] = "product_detail"
    else:
        target = {
            "factSource": "provided_product_facts",
            "confirmedFacts": own_facts,
            "evidence_strength": {
                "product_facts": "partial",
                "product_detail": "unavailable",
            },
        }
    competitors = [
        project_product(index[key], review_limit) if key in index else _missing_competitor(key)
        for asin in competitor_asins
        if (key := asin.strip().upper())
    ]
    return {
        "kind": "listingProductEvidence",
        "schema_version": 1,
        "target": target,
        "competitors": competitors,
        "validation": {
            "target_valid": (
                bool(_text(target.get("title")) and target.get("aboutItemFivePoint"))
                if target_key else bool(own_facts)
            ),
            "valid_competitors": sum(
                bool(_text(item.get("title")) and item.get("aboutItemFivePoint"))
                for item in competitors
            ),
            "requested_competitors": len(competitor_asins),
        },
    }


def _facts_markdown(bundle: dict[str, Any]) -> str:
    target = bundle["target"]
    lines = ["# 商品事实", ""]
    if target.get("factSource") == "provided_product_facts":
        lines += [
            "## 本品已确认/已观察事实",
            "```json",
            json.dumps(target.get("confirmedFacts") or {}, ensure_ascii=False, indent=2),
            "```",
        ]
    else:
        lines += [
            f"- ASIN: {target.get('asin', '')}",
            f"- 标题: {target.get('title', '')}",
            f"- 品牌: {target.get('brand', '')}",
            f"- 价格: {target.get('price', target.get('extractedPrice', ''))}",
            f"- 评分/评论数: {target.get('rating', '')} / {target.get('reviews', '')}",
            f"- 尺寸: {target.get('dimension', '')}",
            f"- 重量: {target.get('weight', '')}",
            "",
            "## 本品五点原文",
        ]
        lines.extend(f"- {item}" for item in target.get("aboutItemFivePoint", []))
        lines += [
            "",
            "## 本品规格（原始字段）",
            "```json",
            json.dumps({
                "productDetails": target.get("productDetails"),
                "itemSpecifications": target.get("itemSpecifications"),
                "itemIngredients": target.get("itemIngredients"),
            }, ensure_ascii=False, indent=2),
            "```",
        ]
    lines += [
        "",
        "## 证据边界",
        "- 只有本品事实段可作为参数、材质、认证、兼容、护理和效果主张的事实源。",
        "- 图片观察只能描述可见外观；不可据此推断内部填充、承重、人体工学、护理方式或耐用度。",
        "- 竞品字段仅供结构、问题和关键词参考，不得移植为本品事实。",
    ]
    for product in bundle["competitors"]:
        lines += ["", f"## 竞品 {product.get('asin', '')}", f"- 标题: {product.get('title', '')}"]
        lines.extend(f"- {item}" for item in product.get("aboutItemFivePoint", []))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="project Product Detail for listing-core")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--target-asin", default=None)
    parser.add_argument(
        "--own-facts", type=Path, default=None,
        help="create 模式的本品结构化事实 JSON；没有本品 ASIN 时必填",
    )
    parser.add_argument("--competitor-asin", action="append", default=[])
    parser.add_argument(
        "--reference-asin", action="append", default=[],
        help="create 模式参考 ASIN；等价于 competitor-asin，名称用于避免误当成本品",
    )
    parser.add_argument("--review-limit", type=int, default=8)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        payload = json.loads(args.source.read_text(encoding="utf-8"))
        own_facts = json.loads(args.own_facts.read_text(encoding="utf-8")) if args.own_facts else None
        if own_facts is not None and not isinstance(own_facts, dict):
            raise ValueError("--own-facts must contain a JSON object")
        references = _normalize_asin_args(args.competitor_asin + args.reference_asin)
        bundle = build_bundle(
            payload, args.target_asin, references, args.review_limit, own_facts=own_facts,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"product evidence projection failed: {exc}", file=sys.stderr)
        return 2
    validation = bundle["validation"]
    if not validation["target_valid"]:
        print(f"product evidence validation failed: {validation}", file=sys.stderr)
        return 3
    out_dir = Path(os.path.abspath(args.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / "product-detail.json"
    facts_path = out_dir / "product-facts.md"
    detail_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    facts_path.write_text(_facts_markdown(bundle), encoding="utf-8")
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    print(f"JSON artifact: {detail_path}")
    print(f"Markdown artifact: {facts_path}")
    print(f"Projection timing: {elapsed_ms}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
