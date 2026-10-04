#!/usr/bin/env python3
"""
listing-title-writer 埋词规划器 — 把 SIF / SellerSprite / category_seed 关键词
按「核心词 / 属性词 / 场景词 / 痛点词」四维分流，供 Title + Item Highlights 埋词。

设计目标是**零额外检索成本**：
  - 只消费 listing-keyword-matrix-build 已经落盘的关键词 JSON（SIF 24h 缓存内）
  - 纯本地正则分桶，不调 LLM、不调网关
  - 一次规划的结果可被同一 ASIN 的 first_draft / retry / 批量同款行复用

Usage:
  python3 scripts/plan_keywords.py <matrix.json> [--top 6] [--brand ExampleBrand]
      [--banned "best,cheapest"] [--exclude-brand HYDAWAY] [--out plan.json]
  cat matrix.json | python3 scripts/plan_keywords.py -

输出（stdout，紧凑 JSON，可直接贴进 prompt 的 {keyword_plan_block}）:
  {
    "keyword_source": "sif",
    "keyword_plan": {
      "core":      [{"kw": "...", "score": 88.1, "signal": "..."}],
      "attribute": [...],
      "scenario":  [...],
      "pain":      [...]
    },
    "primary_keyword": "dog water bottle",
    "title_pool":      ["..."],   # 建议进 Title
    "highlights_pool": ["..."],   # 建议进 Item Highlights
    "bullets_pool":    ["..."],   # 交接给 listing-bullet-writer，不进 Title
    "stats": {...}
  }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

# --- 四维分桶线索词 ------------------------------------------------------

PAIN_CUES = [
    r"\bleak\s?proof\b", r"\bleakproof\b", r"\bno\s+leak\b", r"\bnon[-\s]?slip\b",
    r"\banti[-\s]?\w+", r"\bwater\s?proof\b", r"\bspill\s?proof\b", r"\bshatterproof\b",
    r"\bunbreakable\b", r"\bodorless\b", r"\bodor\s+free\b", r"\bno\s+mess\b",
    r"\bmess\s?free\b", r"\bquiet\b", r"\bnoiseless\b", r"\beasy\s+to\s+clean\b",
    r"\beasy\s+clean\b", r"\bdishwasher\s+safe\b", r"\bheavy\s?duty\b",
    r"\btangle\s?free\b", r"\bwrinkle\s?free\b", r"\bfast\s+charg\w*", r"\bquick\s+dry\w*",
    r"\bdoesn'?t\s+\w+", r"\bwon'?t\s+\w+", r"\bwithout\s+\w+", r"\bno\s+\w+ing\b",
    r"\bsafe\b", r"\bdurable\b", r"\bcomfortable\b",
]

SCENARIO_CUES = [
    r"\bfor\s+", r"\btravel\w*", r"\bhiking\b", r"\bcamping\b", r"\bgym\b", r"\boffice\b",
    r"\boutdoor\w*", r"\bindoor\b", r"\bcar\b", r"\bhome\b", r"\bkitchen\b", r"\bdorm\b",
    r"\bgift\w*", r"\bwedding\b", r"\bchristmas\b", r"\bhalloween\b", r"\bbirthday\b",
    r"\bbaby\b", r"\bkids?\b", r"\btoddler\b", r"\bwomen'?s?\b", r"\bmen'?s?\b",
    r"\bgirls?\b", r"\bboys?\b", r"\bseniors?\b", r"\bbeginners?\b", r"\bpuppy\b",
    r"\bdogs?\b", r"\bcats?\b", r"\bparty\b", r"\bschool\b", r"\bbedroom\b",
    r"\bbathroom\b", r"\bdesk\b", r"\bpatio\b", r"\bcommut\w*", r"\bworkout\b",
    r"\bwalking\b", r"\bbeach\b", r"\bwinter\b", r"\bsummer\b", r"\brv\b", r"\bapartment\b",
]

ATTRIBUTE_CUES = [
    r"\d+\s?(oz|ml|l|liter|litre|inch|in|cm|mm|ft|w|watt|v|volt|a|amp|hz|gb|tb|mah|"
    r"pack|count|pcs|piece|pieces|gallon|qt|lb|lbs|kg|g|degree|°)\b",
    r"\bstainless\s+steel\b", r"\bsilicone\b", r"\bbpa[-\s]?free\b", r"\bcotton\b",
    r"\baluminum\b", r"\balloy\b", r"\bglass\b", r"\bplastic\b", r"\bleather\b",
    r"\bbamboo\b", r"\bceramic\b", r"\btitanium\b", r"\bnylon\b", r"\bpolyester\b",
    r"\bgan\b", r"\busb[-\s]?c\b", r"\btype[-\s]?c\b", r"\bbluetooth\b", r"\bwireless\b",
    r"\brechargeable\b", r"\bcordless\b", r"\bfoldable\b", r"\bcollapsible\b",
    r"\bcompatible\b", r"\bfits\b", r"\breplacement\s+for\b", r"\bstainless\b",
    r"\binsulated\b", r"\bcompact\b", r"\bportable\b", r"\blarge\b", r"\bsmall\b",
    r"\bmini\b", r"\bxl\b", r"\bset\b", r"\bwith\s+\w+",
]

PAIN_RE = [re.compile(p, re.I) for p in PAIN_CUES]
SCENARIO_RE = [re.compile(p, re.I) for p in SCENARIO_CUES]
ATTRIBUTE_RE = [re.compile(p, re.I) for p in ATTRIBUTE_CUES]

SOURCE_MODE_MAP = {
    "asin_sif": "sif",
    "asin_sellersprite_backup": "sellersprite_backup",
    "category_seed": "category_seed",
}

STOP_TOKENS = {"for", "with", "the", "a", "an", "and", "of", "to", "in", "on", "by"}


def _read_input(path: str) -> str:
    if path == "-" or not path:
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("scored_table", "keywords", "keyword_list", "rows"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return [r for r in value if isinstance(r, dict)]
    return []


def _text(row: dict[str, Any]) -> str:
    for key in ("text", "keyword", "kw", "searchTerm", "search_term"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return ""


def _score(row: dict[str, Any]) -> float:
    """value_score 优先；缺失时用搜索量排名 / 自然排名做保守回退，不编造搜索量。"""
    score = _num(row.get("value_score"))
    if score is not None:
        return score
    rank = _num(row.get("search_volume_rank")) or _num(row.get("keywordPopularityRank"))
    if rank and rank > 0:
        import math

        return round(100 / (1 + math.log10(rank)), 1)
    volume = _num(row.get("weeklySearchVolume")) or _num(row.get("search_volume"))
    if volume:
        import math

        return round(min(100.0, 10 * math.log10(volume + 1)), 1)
    return 0.0


def _signal(row: dict[str, Any]) -> str:
    """人类可读的一行流量证据；无真实数据时返回空串，禁止编造。"""
    parts: list[str] = []
    rank = _num(row.get("search_volume_rank")) or _num(row.get("keywordPopularityRank"))
    if rank:
        parts.append(f"SV#{int(rank)}")
    volume = _num(row.get("weeklySearchVolume")) or _num(row.get("search_volume"))
    if volume:
        parts.append(f"{int(volume)}/wk")
    natural = _num(row.get("natural_rank")) or _num(row.get("productNaturalRank"))
    if natural:
        parts.append(f"NR#{int(natural)}")
    conversion = _num(row.get("conversion_score")) or _num(row.get("clickToPurchaseConversionRate"))
    if conversion:
        parts.append(f"CVR{conversion if conversion > 1 else round(conversion * 100, 1)}%")
    if row.get("is_growing"):
        parts.append("growing")
    return " · ".join(parts)


def _markers(row: dict[str, Any]) -> list[str]:
    for key in ("markers", "trafficCharacteristicMarkers", "flags"):
        value = row.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def classify(text: str, row: dict[str, Any]) -> tuple[str, list[str]]:
    """返回 (主桶, 命中的全部桶)。

    判定顺序刻意让「短品类词」先落 core，避免 "dog water bottle" 这类
    核心词因为含有受众词 dog 被误判成场景词：

      1. 含介词意图（for / compatible with）→ scenario
      2. 命中痛点线索 → pain
      3. 词数 ≤3 或 SIF 精准词标志 → core
      4. 命中属性线索 → attribute
      5. 命中场景线索 → scenario
      6. 其余 → core
    """
    matched: list[str] = []
    if any(r.search(text) for r in PAIN_RE):
        matched.append("pain")
    if any(r.search(text) for r in SCENARIO_RE):
        matched.append("scenario")
    if any(r.search(text) for r in ATTRIBUTE_RE):
        matched.append("attribute")

    markers = " ".join(_markers(row)).lower()
    word_count = len(text.split())
    has_intent_prep = bool(re.search(r"(^|\s)for\s+\w", text)) or "compatible with" in text
    is_head = word_count <= 3 or ("isaccuratekw" in markers and word_count <= 4)

    if has_intent_prep:
        primary = "scenario"
    elif "pain" in matched:
        primary = "pain"
    elif is_head:
        primary = "core"
    elif "attribute" in matched:
        primary = "attribute"
    elif "scenario" in matched:
        primary = "scenario"
    else:
        primary = "core"

    if primary not in matched:
        matched.insert(0, primary)
    return primary, matched


def _token_set(text: str) -> frozenset[str]:
    return frozenset(t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in STOP_TOKENS)


def _contains_term(text: str, term: str) -> bool:
    """按词边界匹配英文禁用词/品牌，避免 go 误伤 dog。"""
    if not term:
        return False
    escaped = re.escape(term.strip().lower()).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()))


def plan(
    payload: Any,
    *,
    top: int = 6,
    brand: str | None = None,
    banned: list[str] | None = None,
    exclude_brand: list[str] | None = None,
) -> dict[str, Any]:
    rows = _rows(payload)
    stats_in = payload.get("stats") if isinstance(payload, dict) else {}
    stats_in = stats_in if isinstance(stats_in, dict) else {}
    source_mode = str(stats_in.get("source_mode") or "")
    keyword_source = SOURCE_MODE_MAP.get(source_mode, "unknown" if not rows else "provided")

    banned_lc = {b.strip().lower() for b in (banned or []) if b and b.strip()}
    exclude_lc = {b.strip().lower() for b in (exclude_brand or []) if b and b.strip()}
    _ = (brand or "").strip().lower()  # 自有品牌保留在词组中，不参与竞品过滤。

    buckets: dict[str, list[dict[str, Any]]] = {"core": [], "attribute": [], "scenario": [], "pain": []}
    seen_tokens: list[frozenset[str]] = []
    dropped = {"banned": 0, "competitor_brand": 0, "duplicate": 0, "empty": 0}

    for row in sorted(rows, key=_score, reverse=True):
        text = _text(row)
        if not text:
            dropped["empty"] += 1
            continue
        lower = text.lower()
        if any(_contains_term(lower, b) for b in banned_lc):
            dropped["banned"] += 1
            continue
        # 只排除显式列出的竞品品牌，避免误伤普通词
        if any(_contains_term(lower, b) for b in exclude_lc):
            dropped["competitor_brand"] += 1
            continue

        tokens = _token_set(text)
        if any(tokens and tokens <= prev for prev in seen_tokens):
            dropped["duplicate"] += 1
            continue

        primary, matched = classify(lower, row)
        if len(buckets[primary]) >= top:
            continue
        seen_tokens.append(tokens)
        buckets[primary].append(
            {
                "kw": text,
                "score": _score(row),
                "buckets": matched,
                "signal": _signal(row),
                "source": row.get("source") or keyword_source,
            }
        )
        if all(len(v) >= top for v in buckets.values()):
            break

    primary_keyword = buckets["core"][0]["kw"] if buckets["core"] else (
        buckets["attribute"][0]["kw"] if buckets["attribute"] else None
    )

    title_pool = [k["kw"] for k in buckets["core"][:3]] + [k["kw"] for k in buckets["attribute"][:2]]
    highlights_pool = (
        [k["kw"] for k in buckets["scenario"][:4]]
        + [k["kw"] for k in buckets["attribute"][2:top]]
        + [k["kw"] for k in buckets["pain"][:2]]
    )
    bullets_pool = [k["kw"] for k in buckets["pain"][2:]] + [k["kw"] for k in buckets["scenario"][4:]]

    return {
        "keyword_source": keyword_source,
        "source_mode": source_mode or None,
        "coverage_warning": stats_in.get("coverage_warning"),
        "keyword_plan": buckets,
        "primary_keyword": primary_keyword,
        "title_pool": title_pool,
        "highlights_pool": highlights_pool,
        "bullets_pool": bullets_pool,
        "stats": {
            "input_rows": len(rows),
            "planned": {k: len(v) for k, v in buckets.items()},
            "dropped": dropped,
            "numeric_signals_available": keyword_source in {"sif", "sellersprite_backup"},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="把关键词矩阵分流成 Title / Highlights / Bullets 埋词池")
    parser.add_argument("matrix", nargs="?", default="-", help="listing-keyword-matrix-build 落盘 JSON 路径，或 - 读 stdin")
    parser.add_argument("--top", type=int, default=6, help="每个桶保留的关键词数量（默认 6）")
    parser.add_argument("--brand", default=None, help="自有品牌名")
    parser.add_argument("--banned", default="", help="逗号分隔的禁用词")
    parser.add_argument("--exclude-brand", default="", help="逗号分隔的竞品品牌词")
    parser.add_argument("--out", default=None, help="额外写入的 JSON 文件路径（便于同 ASIN 复用）")
    args = parser.parse_args()

    try:
        payload = json.loads(_read_input(args.matrix))
    except (OSError, json.JSONDecodeError) as e:
        print(f"读取关键词矩阵失败: {e}", file=sys.stderr)
        sys.exit(1)

    result = plan(
        payload,
        top=args.top,
        brand=args.brand,
        banned=[t for t in args.banned.split(",") if t.strip()],
        exclude_brand=[t for t in args.exclude_brand.split(",") if t.strip()],
    )

    if args.out:
        out_path = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Keyword plan cached: {out_path}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
