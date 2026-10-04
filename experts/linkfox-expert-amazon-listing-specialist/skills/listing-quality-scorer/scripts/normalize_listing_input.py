#!/usr/bin/env python3
"""normalize_listing_input — 把任意来源的 Listing 归一成可评分输入，并锁死字段归属。

存在的理由：外部 Listing（Amazon 商品详情、用户粘贴文案）只有一个 `title` 字段，
而本 Skill 的评分契约里 Title 与 Item Highlights 是两个字段。历史上评估者会把
一整条线上标题按 `|` 切成「Title + Item Highlights」再评分——74 字符的前半段稳稳
落在 75c 以内，`title>75c → 标题维度 cap 59` 的门禁就此失效，186 字符的真实标题
拿到 92 分。

本脚本的硬规则：

1. `title` 逐字来自来源的单一标题字段，不截断、不按分隔符拆分。
2. `item_highlights` 只能来自来源里**另一个独立字段**；来源没有该字段就是
   `unavailable`，不允许从标题里切出来「承接」。
3. 每个字段都带 `field_provenance`（来源字段路径 + 状态），下游脚本据此判断
   证据是真实字段还是被人为构造的。
4. 字符数由脚本计算并写进 `field_metrics`，不依赖评估者自己数。

用法：

    python normalize_listing_input.py <source.json> --out listing-normalized.json \\
        [--source-kind auto|amazon_product_detail|user_listing|listing_core] \\
        [--asin B00XXXXXXX] [--marketplace US] [--spec spec.json]

输出 JSON 直接作为 `score_quality.py` 输入 payload 的 `listing` / `field_provenance`
/ `field_metrics` 三个块。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from listing_spec import extract_spec_arg, resolve_limit  # noqa: E402

SCHEMA_VERSION = 1

# 来源里可能存在的、真正独立的 Item Highlights 字段名。不在这个名单里的一律不认。
_HIGHLIGHT_SOURCE_KEYS = (
    "itemHighlights",
    "item_highlights",
    "aboutItemHighlights",
    "highlights",
)

_BULLET_SOURCE_KEYS = ("aboutItemFivePoint", "bulletPoints", "bullets", "bullet_points")

class NormalizationError(ValueError):
    """来源与产物不自洽时抛出——宁可停下来，也不要评一个被改过的 Listing。"""


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        out = []
        for item in value:
            text = _text(item)
            if text:
                out.append(text)
        return out
    return []


def _flatten_description(value: Any) -> str | None:
    """A+ / 结构化描述取其中的文本；只有图片没有文字时返回 None。"""
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, dict):
        parts = [_flatten_description(v) for k, v in value.items() if k not in {"image", "images", "url", "src"}]
        joined = "\n".join(p for p in parts if p)
        return joined or None
    if isinstance(value, list):
        parts = [_flatten_description(item) for item in value]
        joined = "\n".join(p for p in parts if p)
        return joined or None
    return None


def _provenance(source_field: str | None, state: str, reason: str = "") -> dict[str, Any]:
    return {"source_field": source_field, "state": state, "reason": reason}


def _pick_product(payload: Any, asin: str | None) -> tuple[dict[str, Any], int]:
    products = payload.get("products") if isinstance(payload, dict) else None
    if not isinstance(products, list) or not products:
        raise NormalizationError("amazon_product_detail 来源里没有 products[]")
    if asin:
        for index, product in enumerate(products):
            if isinstance(product, dict) and str(product.get("asin") or "").upper() == asin.upper():
                return product, index
        raise NormalizationError(f"products[] 中找不到 ASIN {asin}")
    first = products[0]
    if not isinstance(first, dict):
        raise NormalizationError("products[0] 不是对象")
    return first, 0


def _highlights_from_source(source: dict[str, Any], prefix: str) -> tuple[list[str] | None, dict[str, Any]]:
    """只认来源里独立存在的 highlights 字段；找不到就是 unavailable。"""
    for key in _HIGHLIGHT_SOURCE_KEYS:
        if key in source:
            values = _text_list(source.get(key))
            if values:
                return values, _provenance(f"{prefix}{key}", "verified")
            return None, _provenance(f"{prefix}{key}", "unavailable", "来源字段存在但为空")
    return None, _provenance(
        None,
        "unavailable",
        "来源没有独立的 Item Highlights 字段；禁止从标题中拆分补齐",
    )


def _from_amazon_product_detail(payload: Any, asin: str | None) -> dict[str, Any]:
    product, product_index = _pick_product(payload, asin)
    prefix = f"products[{product_index}]."

    title = _text(product.get("title"))
    if not title:
        raise NormalizationError("products[0].title 为空，无法评分")

    highlights, highlights_prov = _highlights_from_source(product, prefix)

    bullets: list[str] = []
    bullets_prov = _provenance(None, "unavailable", "来源没有五点字段")
    for key in _BULLET_SOURCE_KEYS:
        values = _text_list(product.get(key))
        if values:
            bullets, bullets_prov = values, _provenance(f"{prefix}{key}", "verified")
            break

    description = _flatten_description(product.get("productDescription"))
    description_prov = (
        _provenance(f"{prefix}productDescription", "verified")
        if description
        else _provenance(f"{prefix}productDescription", "unavailable", "描述为空或只有图片")
    )

    return {
        "source_kind": "amazon_product_detail",
        "asin": _text(product.get("asin")),
        "listing": {
            "title": title,
            "item_highlights": highlights,
            "bullets": bullets,
            "description": description,
            "search_terms": None,
        },
        "field_provenance": {
            "title": _provenance(f"{prefix}title", "verified"),
            "item_highlights": highlights_prov,
            "bullets": bullets_prov,
            "description": description_prov,
            # 后台字段前台抓不到，永远不能凭前台文案推断
            "search_terms": _provenance(None, "unavailable", "后台 Search Terms 前台不可见"),
        },
    }


def _from_user_listing(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise NormalizationError("user_listing 来源必须是对象")
    source = payload.get("listing") if isinstance(payload.get("listing"), dict) else payload

    title = _text(source.get("title"))
    if not title:
        raise NormalizationError("listing.title 为空，无法评分")

    highlights, highlights_prov = _highlights_from_source(source, "listing.")

    bullets: list[str] = []
    bullets_prov = _provenance(None, "unavailable", "来源没有五点字段")
    for key in _BULLET_SOURCE_KEYS:
        values = _text_list(source.get(key))
        if values:
            bullets, bullets_prov = values, _provenance(f"listing.{key}", "verified")
            break

    description = _flatten_description(source.get("description"))
    search_terms = _text(source.get("search_terms")) or _text(source.get("searchTerms"))

    return {
        "source_kind": "user_listing",
        "asin": _text(source.get("asin")),
        "listing": {
            "title": title,
            "item_highlights": highlights,
            "bullets": bullets,
            "description": description,
            "search_terms": search_terms,
        },
        "field_provenance": {
            "title": _provenance("listing.title", "verified"),
            "item_highlights": highlights_prov,
            "bullets": bullets_prov,
            "description": _provenance("listing.description", "verified" if description else "unavailable"),
            "search_terms": _provenance(
                "listing.search_terms", "verified" if search_terms else "unavailable"
            ),
        },
    }


def _detect_source_kind(payload: Any) -> str:
    if isinstance(payload, dict):
        if isinstance(payload.get("products"), list):
            return "amazon_product_detail"
        if isinstance(payload.get("listing"), dict) or "title" in payload:
            return "user_listing"
    raise NormalizationError("无法识别来源类型，请显式传 --source-kind")


def _assert_title_not_split(title: str, highlights: list[str] | None, provenance: dict[str, Any]) -> None:
    """Highlights 有值时必须能回到来源里的独立字段。"""
    if not highlights:
        return
    if provenance.get("item_highlights", {}).get("state") != "verified":
        raise NormalizationError(
            "item_highlights 有值但来源字段未验证——疑似从标题拆分而来，拒绝生成评分输入"
        )


def _metrics(listing: dict[str, Any], spec: dict[str, Any] | None) -> dict[str, Any]:
    title = listing.get("title") or ""
    highlights = listing.get("item_highlights") or []
    bullets = listing.get("bullets") or []
    description = listing.get("description") or ""

    title_limit, title_layer = resolve_limit(spec, "title", "max", default=75)
    highlights_limit, highlights_layer = resolve_limit(spec, "item_highlights", "max", default=125)

    return {
        "title_chars": len(title),
        "title_limit": title_limit,
        "title_limit_layer": title_layer,
        "title_over_limit": bool(title_limit is not None and len(title) > title_limit),
        "item_highlights_chars": [len(h) for h in highlights],
        "item_highlights_limit": highlights_limit,
        "item_highlights_limit_layer": highlights_layer,
        "item_highlights_over_limit": bool(
            highlights_limit is not None and any(len(h) > highlights_limit for h in highlights)
        ),
        "bullets_count": len(bullets),
        "bullets_chars": [len(b) for b in bullets],
        "bullets_total_chars": sum(len(b) for b in bullets),
        "description_chars": len(description),
    }


def normalize(payload: Any, source_kind: str = "auto", asin: str | None = None,
              marketplace: str | None = None, spec: dict[str, Any] | None = None) -> dict[str, Any]:
    kind = source_kind if source_kind and source_kind != "auto" else _detect_source_kind(payload)
    if kind == "amazon_product_detail":
        result = _from_amazon_product_detail(payload, asin)
    elif kind in {"user_listing", "listing_core"}:
        result = _from_user_listing(payload)
    else:
        raise NormalizationError(f"不支持的来源类型: {kind}")

    _assert_title_not_split(
        result["listing"]["title"], result["listing"].get("item_highlights"), result["field_provenance"]
    )

    result["kind"] = "listingScoringInput"
    result["schema_version"] = SCHEMA_VERSION
    result["marketplace"] = marketplace
    result["field_metrics"] = _metrics(result["listing"], spec)
    return result


def main() -> None:
    argv, spec = extract_spec_arg(sys.argv[1:])
    parser = argparse.ArgumentParser(description="把任意来源的 Listing 归一成可评分输入")
    parser.add_argument("source", help="来源 JSON：商品详情响应 / 用户提供的 listing")
    parser.add_argument("--out", required=True, help="归一化结果输出路径")
    parser.add_argument(
        "--source-kind", default="auto",
        choices=["auto", "amazon_product_detail", "user_listing", "listing_core"],
    )
    parser.add_argument("--asin", default=None, help="products[] 中要评分的 ASIN")
    parser.add_argument("--marketplace", default=None)
    args = parser.parse_args(argv)

    with open(args.source, encoding="utf-8") as f:
        payload = json.load(f)

    try:
        result = normalize(payload, args.source_kind, args.asin, args.marketplace, spec)
    except NormalizationError as exc:
        print(f"[归一化失败] {exc}", file=sys.stderr)
        raise SystemExit(2)

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    metrics = result["field_metrics"]
    print(f"Saved full response: {out_path}")
    print(
        f"title {metrics['title_chars']}c / limit {metrics['title_limit']}"
        f"（{metrics['title_limit_layer']}）over_limit={metrics['title_over_limit']}"
    )
    print(f"item_highlights: {result['field_provenance']['item_highlights']['state']}")


if __name__ == "__main__":
    main()
