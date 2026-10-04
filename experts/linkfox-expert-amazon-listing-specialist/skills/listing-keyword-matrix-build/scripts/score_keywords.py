#!/usr/bin/env python3
"""关键词布局解析、分层、过滤与价值打分（纯逻辑，无 I/O）。"""

from __future__ import annotations

import math
import re
from typing import Any

# displayPositionTypes → conditions 标志的映射
_DISPLAY_TO_MARKER = {
    "natural": "nfPosition",
    "sp": "isSpAd",
    "top": "isBrandAd",
    "bottom": "isBrandAd",
    "vedio": "isVedioAd",
    "ac": "isAC",
}

_SELLERSPRITE_BADGE_TO_MARKER = {
    "naturalSearching": "nfPosition",
    "ads": "isSpAd",
    "amazonChoice": "isAC",
    "sponsorBrand": "isBrandAd",
    "sponsorVideo": "isVedioAd",
}

_SELLERSPRITE_TRAFFIC_TYPE_TO_MARKER = {
    "primary": "isAccurateKw",
    "precise": "isAccurateKw",
    "preciseLongTail": "isAccurateTailKw",
}

_SELLERSPRITE_CONVERSION_TYPE_TO_MARKER = {
    "excellent": "isQualityKw",
    "stable": "isStableKw",
    "lost": "isLossKw",
    "invalid": "isInvalidKw",
}

_MATRIX_BUCKETS: list[tuple[str, str]] = [
    ("natural_traffic", "isAccurateKw"),  # OR nfPosition，见 _in_bucket
    ("sp_ads", "isSpAd"),
    ("brand_ads", "isBrandAd"),
    ("video_ads", "isVedioAd"),
    ("ac_recommended", "isAC"),
    ("conversion_top", "isQualityKw"),
    ("long_tail", "isAccurateTailKw"),
    ("growing", "isSearchVolUpKw"),
    ("declining", "isSearchVolDownKw"),
    ("multi_variant", "isMultiVariantKw"),
]

_DEFAULT_WEIGHTS = {
    "search_volume": 0.3,
    "conversion": 0.3,
    "natural_rank": 0.2,
    "growth": 0.2,
}


def parse_time_window(time_window: str) -> tuple[str, str]:
    """将 latelyDay_30 / month_2026-04 / week_2026-04-13 转为 SIF API 参数。"""
    tw = (time_window or "latelyDay_30").strip()
    if tw.startswith("latelyDay_"):
        val = tw.split("_", 1)[1]
        if val not in ("7", "30"):
            val = "30"
        return "latelyDay", val
    if tw.startswith("month_"):
        return "month", tw.split("_", 1)[1]
    if tw.startswith("week_"):
        return "week", tw.split("_", 1)[1]
    # 兼容裸 latelyDay / month / week
    if tw in ("latelyDay", "month", "week"):
        defaults = {"latelyDay": "30", "month": "", "week": ""}
        return tw, defaults[tw]
    return "latelyDay", "30"


def region_to_country(region: str) -> str:
    r = (region or "US").upper()
    supported = {
        "US", "UK", "DE", "CA", "JP", "FR", "ES", "IT", "MX", "AU", "AE", "BR", "SA",
    }
    return r if r in supported else "US"


def extract_keyword_rows(sif_result: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(sif_result, dict):
        return []
    if sif_result.get("error"):
        return []
    err = sif_result.get("errcode") or sif_result.get("errorCode") or sif_result.get("code")
    if err not in (None, 200, "200", "ok", "success", True):
        # 部分网关用 code 字符串
        if str(err).lower() not in ("200", "ok", "success"):
            return []
    data = sif_result.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


def extract_sellersprite_keyword_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []
    if result.get("error"):
        return []
    err = result.get("errcode") or result.get("errorCode") or result.get("code")
    if err not in (None, 200, "200", "ok", "success", True):
        if str(err).lower() not in ("200", "ok", "success"):
            return []
    data = result.get("data")
    if not isinstance(data, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        keyword = str(item.get("keyword") or "").strip()
        if not keyword:
            continue

        markers: set[str] = set()
        badges = item.get("badges") or []
        if isinstance(badges, str):
            badges = [badges]
        if isinstance(badges, list):
            for badge in badges:
                mapped = _SELLERSPRITE_BADGE_TO_MARKER.get(str(badge))
                if mapped:
                    markers.add(mapped)

        traffic_type = item.get("trafficKeywordType")
        mapped_traffic = _SELLERSPRITE_TRAFFIC_TYPE_TO_MARKER.get(str(traffic_type))
        if mapped_traffic:
            markers.add(mapped_traffic)

        conversion_type = item.get("conversionKeywordType")
        mapped_conversion = _SELLERSPRITE_CONVERSION_TYPE_TO_MARKER.get(str(conversion_type))
        if mapped_conversion:
            markers.add(mapped_conversion)

        natural_rank = _position_value(item.get("rankPosition"))
        ad_rank = _position_value(item.get("adPosition"))
        if natural_rank is not None:
            markers.add("nfPosition")
        if ad_rank is not None:
            markers.add("isSpAd")

        rows.append({
            "keyword": keyword,
            "translateKeyword": item.get("keywordCn"),
            "keywordPopularityRank": _int_or_none(item.get("searchesRank")),
            "productNaturalRank": natural_rank,
            "weeklySearchVolume": _weekly_search_volume(item),
            "clickToPurchaseConversionRate": item.get("purchaseRate"),
            "trafficCharacteristicMarkers": sorted(markers),
            "conversionPerformanceMarkers": [],
            "displayPositionTypes": _sellersprite_display_positions(item),
            "source": "SellerSprite",
            "monthlySearchVolume": _int_or_none(item.get("searches")),
            "monthlyPurchases": _int_or_none(item.get("purchases")),
            "adRank": ad_rank,
            "bid": item.get("bid"),
            "trafficPercentage": item.get("trafficPercentage"),
        })
    return rows


def _collect_markers(row: dict[str, Any]) -> set[str]:
    markers: set[str] = set()
    for key in ("trafficCharacteristicMarkers", "conversionPerformanceMarkers"):
        val = row.get(key)
        if isinstance(val, list):
            markers.update(str(m) for m in val if m)
    display = row.get("displayPositionTypes") or []
    if isinstance(display, list):
        for pos in display:
            mapped = _DISPLAY_TO_MARKER.get(str(pos))
            if mapped:
                markers.add(mapped)
    return markers


def _position_value(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("position", "index"):
            pos = _int_or_none(value.get(key))
            if pos is not None:
                return pos
    return _int_or_none(value)


def _weekly_search_volume(row: dict[str, Any]) -> int | None:
    weekly = _int_or_none(row.get("calculatedWeeklySearches"))
    if weekly is not None:
        return weekly
    monthly = _int_or_none(row.get("searches"))
    if monthly is None:
        return None
    return max(1, round(monthly / 4))


def _sellersprite_display_positions(row: dict[str, Any]) -> list[str]:
    out: list[str] = []
    badges = row.get("badges") or []
    if isinstance(badges, str):
        badges = [badges]
    if isinstance(badges, list):
        badge_set = {str(b) for b in badges}
        if "naturalSearching" in badge_set:
            out.append("natural")
        if "ads" in badge_set:
            out.append("sp")
        if "amazonChoice" in badge_set:
            out.append("ac")
        if "sponsorBrand" in badge_set:
            out.append("top")
        if "sponsorVideo" in badge_set:
            out.append("vedio")
    return out


def _in_bucket(markers: set[str], bucket_key: str, marker: str) -> bool:
    if bucket_key == "natural_traffic":
        return "isAccurateKw" in markers or "nfPosition" in markers
    return marker in markers


def normalize_keyword(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _singularize(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def dedupe_key(text: str) -> str:
    norm = normalize_keyword(text)
    tokens = [_singularize(t) for t in norm.split()]
    return " ".join(tokens)


def build_raw_matrix(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    matrix: dict[str, list[dict[str, Any]]] = {k: [] for k, _ in _MATRIX_BUCKETS}
    seen: dict[str, dict[str, Any]] = {}

    for row in rows:
        kw_text = str(row.get("keyword") or "").strip()
        if not kw_text:
            continue
        key = dedupe_key(kw_text)
        if key in seen:
            continue

        markers = _collect_markers(row)
        entry = {
            "keyword": kw_text,
            "translate_keyword": row.get("translateKeyword"),
            "searches_rank": _int_or_none(row.get("keywordPopularityRank")),
            "natural_rank": _int_or_none(row.get("productNaturalRank")),
            "weekly_search_volume": _int_or_none(row.get("weeklySearchVolume")),
            "conversion_score": _conversion_pct(row.get("clickToPurchaseConversionRate")),
            "is_growing": "isSearchVolUpKw" in markers,
            "is_declining": "isSearchVolDownKw" in markers,
            "is_long_tail": "isAccurateTailKw" in markers,
            "markers": sorted(markers),
            "display_positions": row.get("displayPositionTypes") or [],
            "source": row.get("source") or "SIF",
            "monthly_search_volume": row.get("monthlySearchVolume"),
            "monthly_purchases": row.get("monthlyPurchases"),
            "ad_rank": row.get("adRank"),
            "bid": row.get("bid"),
            "traffic_percentage": row.get("trafficPercentage"),
        }
        seen[key] = entry

        for bucket_key, marker in _MATRIX_BUCKETS:
            if _in_bucket(markers, bucket_key, marker):
                matrix[bucket_key].append(entry)

    return matrix


def _int_or_none(val: Any) -> int | None:
    try:
        if val is None or val == "":
            return None
        return int(val)
    except (TypeError, ValueError):
        return None


def _conversion_pct(rate: Any) -> float:
    try:
        if rate is None:
            return 0.0
        r = float(rate)
        # API 可能返回 0-1 或已是百分比
        if 0 <= r <= 1:
            return round(r * 100, 2)
        return round(r, 2)
    except (TypeError, ValueError):
        return 0.0


def filter_keywords(
    rows: list[dict[str, Any]],
    banned_terms: list[str] | None,
    exclude_brand: str | None,
) -> tuple[list[dict[str, Any]], int]:
    banned = [normalize_keyword(t) for t in (banned_terms or []) if t]
    brand = normalize_keyword(exclude_brand) if exclude_brand else ""
    kept: list[dict[str, Any]] = []
    filtered = 0

    for row in rows:
        kw = str(row.get("keyword") or "")
        norm = normalize_keyword(kw)
        if any(b and b in norm for b in banned):
            filtered += 1
            continue
        if brand and brand in norm:
            filtered += 1
            continue
        kept.append(row)
    return kept, filtered


def _build_reason(entry: dict[str, Any], sv: float, cv: float, nr: float, gr: float) -> str:
    parts: list[str] = []
    rank = entry.get("searches_rank")
    if rank:
        parts.append(f"搜索排名 #{rank}")
    if entry.get("conversion_score"):
        parts.append(f"转化 {entry['conversion_score']:.0f}%")
    nr_val = entry.get("natural_rank")
    if nr_val:
        parts.append(f"自然位 #{nr_val}")
    if entry.get("is_growing"):
        parts.append("搜索量增长")
    elif entry.get("is_declining"):
        parts.append("搜索量下降")
    if entry.get("is_long_tail"):
        parts.append("精准长尾")
    parts.append(f"分项 sv={sv:.0f} cv={cv:.0f} nr={nr:.0f} gr={gr:.0f}")
    return " · ".join(parts)


def score_keyword(entry: dict[str, Any], weights: dict[str, float]) -> dict[str, Any]:
    w = {**_DEFAULT_WEIGHTS, **(weights or {})}
    searches_rank = entry.get("searches_rank") or 999999
    natural_rank = entry.get("natural_rank") or 9999

    sv_score = 1 / (1 + math.log10(max(searches_rank, 1))) * 100
    conv_score = float(entry.get("conversion_score") or 0)
    if conv_score <= 1:
        conv_score *= 100
    nr_score = 1 / (1 + math.log10(max(natural_rank, 1))) * 100

    if entry.get("is_growing"):
        growth_score = 80.0
    elif entry.get("is_declining"):
        growth_score = 20.0
    else:
        growth_score = 50.0

    value = (
        w["search_volume"] * sv_score
        + w["conversion"] * conv_score
        + w["natural_rank"] * nr_score
        + w["growth"] * growth_score
    )
    if entry.get("is_long_tail"):
        value += 10  # 长尾铺货小幅加分

    reason = _build_reason(entry, sv_score, conv_score, nr_score, growth_score)
    kw = entry["keyword"]
    return {
        "keyword": kw,
        "text": kw,
        "value_score": round(value, 1),
        "search_volume_rank": entry.get("searches_rank"),
        "natural_rank": entry.get("natural_rank"),
        "weekly_search_volume": entry.get("weekly_search_volume"),
        "conversion_score": entry.get("conversion_score", 0),
        "is_growing": bool(entry.get("is_growing")),
        "is_long_tail": bool(entry.get("is_long_tail")),
        "markers": entry.get("markers") or [],
        "source": entry.get("source"),
        "monthly_search_volume": entry.get("monthly_search_volume"),
        "monthly_purchases": entry.get("monthly_purchases"),
        "ad_rank": entry.get("ad_rank"),
        "bid": entry.get("bid"),
        "traffic_percentage": entry.get("traffic_percentage"),
        "reason": reason,
    }


def build_scored_table(
    rows: list[dict[str, Any]],
    weights: dict[str, float] | None,
    top_n: int,
) -> list[dict[str, Any]]:
    flat: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = dedupe_key(row.get("keyword", ""))
        if key and key not in flat:
            flat[key] = row

    scored = [score_keyword(entry, weights or {}) for entry in flat.values()]
    scored.sort(key=lambda x: x["value_score"], reverse=True)
    n = max(1, int(top_n or 50))
    return scored[:n]


def _scored_row_to_keyword_item(row: dict[str, Any]) -> dict[str, Any]:
    """将 scored_table 行映射为前端 keyword_list / SIF 兼容字段。"""
    conv_raw = row.get("conversion_score")
    conv = None if conv_raw is None else conv_raw
    return {
        "keyword": row.get("keyword") or row.get("text"),
        "keywordPopularityRank": row.get("search_volume_rank"),
        "productNaturalRank": row.get("natural_rank"),
        "weeklySearchVolume": row.get("weekly_search_volume"),
        "clickToPurchaseConversionRate": conv / 100.0 if isinstance(conv, (int, float)) and conv > 1 else conv,
        "value_score": row.get("value_score"),
        "source": row.get("source"),
        "field": row.get("field"),
        "priority": row.get("priority"),
        "trafficCharacteristicMarkers": row.get("markers") or [],
        "is_growing": row.get("is_growing"),
        "is_long_tail": row.get("is_long_tail"),
        "reason": row.get("reason"),
    }


def build_output_payload(
    asin: str,
    region: str,
    time_window: str,
    raw_matrix: dict[str, list[dict[str, Any]]],
    scored_table: list[dict[str, Any]],
    stats: dict[str, Any],
) -> dict[str, Any]:
    keywords = [_scored_row_to_keyword_item(row) for row in scored_table]
    return {
        "asin": asin,
        "region": region,
        "time_window": time_window,
        "total": len(keywords),
        "keywords": keywords,
        "scored_table": scored_table,
        "raw_matrix": raw_matrix,
        "stats": stats,
    }
