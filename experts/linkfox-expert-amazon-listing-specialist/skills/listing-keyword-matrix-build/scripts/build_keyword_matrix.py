#!/usr/bin/env python3
"""
listing-keyword-matrix-build 单入口：SIF 拉数 → SellerSprite 备份 → 分层 → 打分 → 落盘。

⛔ 禁止 agent 用 curl / /tmp / python3 -c 绕过本脚本。
⛔ 本 skill 只产出 scored_table，禁止在此阶段写 Listing 文案。

Usage:
  python scripts/build_keyword_matrix.py '{"asin":"B07JB964VX","region":"US"}'
  python scripts/build_keyword_matrix.py '{"category_node":{"name":"Capsule Coffee Machines"},"seed_keywords":["capsule coffee machine"]}'
  python scripts/build_keyword_matrix.py params.json
  cat params.json | python scripts/build_keyword_matrix.py
  python scripts/build_keyword_matrix.py '<json>' --no-cache
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# 文件名须符合 skill-output-protocol：linkfox-<slug>-<数字>.json
SLUG = "linkfox-listing-keyword-matrix-build"
CACHE_TTL_SEC = 24 * 3600
SIF_API_PATH = "/sif/asinKeywords"
SELLERSPRITE_API_PATH = "/sellersprite/traffic/keyword"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _load_modules():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from linkfox_paths import get_api_base, resolve_data_path, writable_root  # type: ignore
    import score_keywords as sk  # type: ignore

    return get_api_base, resolve_data_path, sk, writable_root


def _get_api_key() -> str:
    key = os.environ.get("LINKFOX_AGENT_API_KEY") or os.environ.get("LINKFOXAGENT_API_KEY")
    if not key:
        print(
            "未配置 API Key。请设置环境变量 LINKFOX_AGENT_API_KEY 或 LINKFOXAGENT_API_KEY。",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _read_input(argv: list[str]) -> str:
    if not argv or argv[0] == "-":
        if sys.stdin.isatty():
            print(
                "用法: build_keyword_matrix.py '<json>' | build_keyword_matrix.py params.json",
                file=sys.stderr,
            )
            sys.exit(1)
        return sys.stdin.read()
    arg = argv[0]
    if os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return f.read()
    return arg


def _cache_key(params: dict[str, Any]) -> str:
    banned = params.get("banned_terms") or []
    brand = params.get("exclude_competitor_brand") or params.get("exclude_brand") or ""
    category_node = params.get("category_node") or params.get("category") or ""
    raw = json.dumps(
        {
            "asin": params.get("asin"),
            "cache_version": 2,
            "category_node": category_node,
            "product_type": params.get("product_type"),
            "seed_keywords": params.get("seed_keywords"),
            "region": params.get("region", "US"),
            "time_window": params.get("time_window", "latelyDay_30"),
            "banned_terms": sorted(banned),
            "exclude_brand": brand,
            "top_n": params.get("top_n") or params.get("top_n_keywords", 50),
            "scoring_weights": params.get("scoring_weights"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cache_dir() -> str:
    _, _, _, writable_root = _load_modules()
    root = writable_root()
    path = os.path.join(root, "linkfox", ".cache", "keyword-matrix")
    os.makedirs(path, exist_ok=True)
    return path


def _cache_path(digest: str) -> str:
    return os.path.join(_cache_dir(), f"kw-matrix-{digest}.json")


def _load_cache(path: str) -> dict[str, Any] | None:
    if not os.path.isfile(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > CACHE_TTL_SEC:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(path: str, payload: dict[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def call_sif_api(params: dict[str, Any], sk) -> dict[str, Any]:
    asin = str(params.get("asin") or "").strip()
    if not asin:
        return {"error": "缺少 asin"}

    region = params.get("region", "US")
    time_window = params.get("time_window", "latelyDay_30")
    piece_type, piece_value = sk.parse_time_window(str(time_window))

    body = {
        "country": sk.region_to_country(str(region)),
        "asin": asin,
        "pageSize": min(100, max(10, int(params.get("page_size") or 100))),
        "pageNum": 1,
        "sortBy": "searchesRank",
        "desc": True,
        "timePieceType": piece_type,
    }
    if piece_value:
        body["timePieceValue"] = piece_value

    get_api_base, _, _, _ = _load_modules()
    url = get_api_base() + SIF_API_PATH
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": _get_api_key(),
        "Content-Type": "application/json",
        "User-Agent": "LinkFox-Skill/2.0",
        "SESSION_ID": os.environ.get("SESSION_ID", ""),
    }
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=120) as resp:
            body_text = resp.read().decode("utf-8")
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                return {
                    "error": "SIF returned an invalid JSON response",
                    "details": body_text[:500],
                }
    except HTTPError as e:
        body_text = e.read().decode("utf-8") if e.fp else ""
        try:
            return json.loads(body_text) if body_text else {"error": f"HTTP {e.code}: {e.reason}"}
        except json.JSONDecodeError:
            return {"error": f"HTTP {e.code}: {e.reason}", "details": body_text}
    except URLError as e:
        return {"error": f"Connection failed: {e.reason}"}


def call_sellersprite_api(params: dict[str, Any], sk) -> dict[str, Any]:
    asin = str(params.get("asin") or "").strip()
    if not asin:
        return {"error": "缺少 asin"}

    region = str(params.get("region") or "US").upper()
    supported = {"US", "JP", "UK", "DE", "FR", "IT", "ES", "CA", "IN"}
    if region not in supported:
        return {"error": f"SellerSprite backup does not support region: {region}"}

    body: dict[str, Any] = {
        "marketplace": region,
        "asin": asin,
        "page": 1,
        "size": min(100, max(10, int(params.get("page_size") or 100))),
        "orderField": "searches",
        "orderDesc": True,
    }
    time_window = str(params.get("time_window") or "latelyDay_30")
    if time_window.startswith("month_"):
        month = time_window.split("_", 1)[1].replace("-", "")
        if len(month) == 6 and month.isdigit():
            body["month"] = month

    get_api_base, _, _, _ = _load_modules()
    url = get_api_base() + SELLERSPRITE_API_PATH
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": _get_api_key(),
        "Content-Type": "application/json",
        "User-Agent": "LinkFox-Skill/2.0",
        "SESSION_ID": os.environ.get("SESSION_ID", ""),
    }
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=120) as resp:
            body_text = resp.read().decode("utf-8")
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                return {
                    "error": "SellerSprite returned an invalid JSON response",
                    "details": body_text[:500],
                }
    except HTTPError as e:
        body_text = e.read().decode("utf-8") if e.fp else ""
        try:
            return json.loads(body_text) if body_text else {"error": f"HTTP {e.code}: {e.reason}"}
        except json.JSONDecodeError:
            return {"error": f"HTTP {e.code}: {e.reason}", "details": body_text}
    except URLError as e:
        return {"error": f"Connection failed: {e.reason}"}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return ""


def _iter_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_iter_text_values(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_iter_text_values(item))
        return out
    return []


def _category_name(params: dict[str, Any]) -> str:
    node = params.get("category_node")
    if isinstance(node, dict):
        for key in ("name", "browse_node_name", "category", "leaf"):
            text = _as_text(node.get(key))
            if text:
                return text
        path = node.get("path")
        if isinstance(path, list) and path:
            text = _as_text(path[-1])
            if text:
                return text
    return _as_text(params.get("category") or params.get("product_category"))


def _category_path(params: dict[str, Any]) -> list[str]:
    node = params.get("category_node")
    if isinstance(node, dict):
        path = node.get("path")
        if isinstance(path, list):
            return [_as_text(item) for item in path if _as_text(item)]
        name = _category_name(params)
        return [name] if name else []
    name = _category_name(params)
    return [name] if name else []


def _seed_keyword_candidates(params: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def add(text: str, source: str, field: str, priority: int) -> None:
        keyword = " ".join(text.strip().split())
        if not keyword:
            return
        candidates.append({
            "keyword": keyword,
            "source": source,
            "field": field,
            "priority": priority,
        })

    for idx, item in enumerate(params.get("seed_keywords") or []):
        if isinstance(item, dict):
            text = _as_text(item.get("keyword") or item.get("text") or item.get("query"))
            source = _as_text(item.get("source")) or "user_seed"
            field = _as_text(item.get("field")) or "seed_keywords"
            add(text, source, field, idx)
        else:
            add(_as_text(item), "user_seed", "seed_keywords", idx)

    category = _category_name(params)
    if category:
        add(category, "category_node", "Title", 100)

    product_type = _as_text(params.get("product_type") or params.get("product_name"))
    if product_type:
        add(product_type, "product_type", "Title", 110)

    facts = params.get("product_facts") or params.get("known_facts") or {}
    if isinstance(facts, dict):
        for field, source in (
            ("core_terms", "product_core"),
            ("features", "product_feature"),
            ("selling_points", "product_feature"),
            ("use_scenarios", "product_scenario"),
            ("target_person", "product_audience"),
            ("material", "product_attribute"),
            ("color", "product_attribute"),
            ("compatibility", "product_attribute"),
        ):
            for value in _iter_text_values(facts.get(field)):
                add(value, source, field, 200 + len(candidates))

    return candidates


def run_seed_pipeline(params: dict[str, Any]) -> dict[str, Any]:
    _, _, sk, _ = _load_modules()
    region = str(params.get("region") or "US")
    time_window = str(params.get("time_window") or "latelyDay_30")
    top_n = int(params.get("top_n") or params.get("top_n_keywords") or 50)
    banned = params.get("banned_terms") or []
    exclude_brand = params.get("exclude_competitor_brand") or params.get("exclude_brand")
    candidates = _seed_keyword_candidates(params)

    raw_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        key = sk.dedupe_key(item.get("keyword", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        raw_rows.append({
            "keyword": item["keyword"],
            "translate_keyword": None,
            "searches_rank": None,
            "natural_rank": None,
            "weekly_search_volume": None,
            "conversion_score": None,
            "is_growing": False,
            "is_declining": False,
            "is_long_tail": len(item["keyword"].split()) >= 3,
            "markers": ["category_inferred"],
            "display_positions": [],
            "source": item["source"],
            "field": item["field"],
            "priority": item["priority"],
        })

    kept, filtered_count = sk.filter_keywords(raw_rows, banned, exclude_brand)
    top_rows = kept[: max(1, top_n)]
    scored_table = []
    for idx, entry in enumerate(top_rows, 1):
        scored_table.append({
            "keyword": entry["keyword"],
            "text": entry["keyword"],
            "value_score": None,
            "search_volume_rank": None,
            "natural_rank": None,
            "weekly_search_volume": None,
            "conversion_score": None,
            "is_growing": False,
            "is_long_tail": bool(entry.get("is_long_tail")),
            "markers": entry.get("markers") or [],
            "source": entry.get("source") or "category_inferred",
            "field": entry.get("field") or "",
            "priority": idx,
            "reason": "类目/商品事实推导词，未经 SIF 搜索量或转化数据验证",
        })

    raw_matrix = {
        "natural_traffic": [],
        "sp_ads": [],
        "brand_ads": [],
        "video_ads": [],
        "ac_recommended": [],
        "conversion_top": [],
        "long_tail": [row for row in top_rows if row.get("is_long_tail")],
        "growing": [],
        "declining": [],
        "multi_variant": [],
        "category_seed": top_rows,
    }
    stats = {
        "source_mode": "category_seed",
        "category_node": params.get("category_node") or _category_name(params),
        "category_path": _category_path(params),
        "total_raw_keywords": len(raw_rows),
        "unique_keywords": len(raw_rows),
        "filtered_count": filtered_count,
        "scored_count": len(scored_table),
        "coverage_warning": "seed_only",
        "disclaimer": "关键词由商品事实和亚马逊类目节点推导，未经过 SIF 搜索量、排名或转化验证。",
    }
    return sk.build_output_payload("NEW", region, time_window, raw_matrix, scored_table, stats)


def _summarize_stdout(payload: dict[str, Any], out_path: str, size_bytes: int) -> None:
    scored = payload.get("scored_table") or []
    stats = payload.get("stats") or {}
    abs_path = os.path.abspath(out_path)
    print(f"Saved full response: {abs_path} ({size_bytes} bytes)")
    print(f"关键词布局已落盘：raw={stats.get('total_raw_keywords', 0)} scored={len(scored)} filtered={stats.get('filtered_count', 0)}")
    if stats.get("from_cache"):
        print("  (24h 缓存命中)")
    if stats.get("coverage_warning"):
        print(f"  ⚠️ {stats['coverage_warning']}")
    print("\nTop 5 scored keywords:")
    for i, row in enumerate(scored[:5], 1):
        score = row.get("value_score")
        score_label = "—" if score is None else score
        print(f"  {i}. [{score_label}] {row.get('text')} — {row.get('reason', '')[:80]}")


def run_pipeline(params: dict[str, Any], use_cache: bool = True) -> dict[str, Any]:
    _, _, sk, _ = _load_modules()

    asin = str(params.get("asin") or "").strip()
    if not asin:
        return run_seed_pipeline(params)

    region = str(params.get("region") or "US")
    time_window = str(params.get("time_window") or "latelyDay_30")
    top_n = int(params.get("top_n") or params.get("top_n_keywords") or 50)
    weights = params.get("scoring_weights")
    banned = params.get("banned_terms") or []
    exclude_brand = params.get("exclude_competitor_brand") or params.get("exclude_brand")

    digest = _cache_key(params)
    cache_file = _cache_path(digest)
    if use_cache:
        cached = _load_cache(cache_file)
        if cached:
            cached.setdefault("stats", {})["from_cache"] = True
            return cached

    source_mode = "asin_sif"
    sif_result: dict[str, Any] = {}
    sellersprite_result: dict[str, Any] | None = None

    force_source = str(params.get("force_keyword_source") or "").strip().lower()
    use_sellersprite_backup = params.get("enable_sellersprite_backup", True) is not False

    if force_source == "sellersprite":
        rows = []
    else:
        sif_result = call_sif_api(params, sk)
        rows = sk.extract_keyword_rows(sif_result)

    if not rows and use_sellersprite_backup:
        sellersprite_result = call_sellersprite_api(params, sk)
        backup_rows = sk.extract_sellersprite_keyword_rows(sellersprite_result)
        if backup_rows:
            rows = backup_rows
            source_mode = "asin_sellersprite_backup"

    if not rows and sif_result.get("error"):
        payload = sk.build_output_payload(
            asin,
            region,
            time_window,
            {k: [] for k in ("natural_traffic", "sp_ads", "brand_ads", "video_ads", "ac_recommended",
                             "conversion_top", "long_tail", "growing", "declining", "multi_variant")},
            [],
            {
                "total_raw_keywords": 0,
                "filtered_count": 0,
                "coverage_warning": "sif_error",
                "sif_error": sif_result.get("error"),
                "sellersprite_backup_error": (
                    sellersprite_result.get("error") if isinstance(sellersprite_result, dict) else None
                ),
            },
        )
        if use_cache:
            _save_cache(cache_file, payload)
        return payload

    raw_matrix = sk.build_raw_matrix(rows)
    flat_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for bucket in raw_matrix.values():
        for entry in bucket:
            key = sk.dedupe_key(entry.get("keyword", ""))
            if key not in seen:
                seen.add(key)
                flat_rows.append(entry)

    kept, filtered_count = sk.filter_keywords(flat_rows, banned, exclude_brand)
    scored_table = sk.build_scored_table(kept, weights, top_n)

    coverage_warning = None
    if not rows:
        coverage_warning = "sif_no_data"
    elif len(scored_table) < 10:
        coverage_warning = "low_keyword_coverage"
    if kept and not scored_table:
        coverage_warning = "all_filtered"

    stats = {
        "source_mode": source_mode,
        "total_raw_keywords": len(rows),
        "unique_keywords": len(flat_rows),
        "filtered_count": filtered_count,
        "scored_count": len(scored_table),
        "coverage_warning": coverage_warning,
        "sif_cost_token": sif_result.get("costToken"),
        "sif_cost_time_ms": sif_result.get("costTime"),
        "sif_error": sif_result.get("error"),
        "sellersprite_backup_used": source_mode == "asin_sellersprite_backup",
        "sellersprite_backup_error": (
            sellersprite_result.get("error") if isinstance(sellersprite_result, dict) else None
        ),
        "sellersprite_cost_token": (
            sellersprite_result.get("costToken") if isinstance(sellersprite_result, dict) else None
        ),
    }

    payload = sk.build_output_payload(asin, region, time_window, raw_matrix, scored_table, stats)
    if use_cache:
        _save_cache(cache_file, payload)
    return payload


def main() -> None:
    argv = sys.argv[1:]
    use_cache = True
    if "--no-cache" in argv:
        use_cache = False
        argv = [a for a in argv if a != "--no-cache"]

    raw = _read_input(argv)
    try:
        params = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"输入不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not str(params.get("asin") or "").strip():
        has_seed_context = bool(
            params.get("seed_keywords")
            or params.get("category_node")
            or params.get("category")
            or params.get("product_facts")
            or params.get("known_facts")
        )
        if not has_seed_context:
            print("缺少 asin；无 ASIN 的 create 场景请传 category_node/category、product_facts 或 seed_keywords。", file=sys.stderr)
            sys.exit(1)

    payload = run_pipeline(params, use_cache=use_cache)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)

    _, resolve_data_path, _, _ = _load_modules()
    ts = time.time()
    out_path = resolve_data_path(SLUG, ts)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(serialized)
    except OSError as e:
        print(f"落盘失败 {out_path}: {e}", file=sys.stderr)
        sys.exit(1)

    size_bytes = len(serialized.encode("utf-8"))
    _summarize_stdout(payload, out_path, size_bytes)



if __name__ == "__main__":
    main()
