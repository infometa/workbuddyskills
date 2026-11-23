#!/usr/bin/env python3
"""Resolve intl city/airport codes from a local cache, never by model memory.

`air_city` (scope=INTERNATIONAL) is a keyword-search tool: pass `keyword`
(city name / pinyin / airport name / three-letter code) and it returns top-N
candidates (small response, safe to read). This script keeps a local compact
cache so repeat lookups skip the MCP call entirely.

Usage:
  python3 scripts/air_intl_resolve_city.py 北京 新加坡
      Query cache; on miss auto-call air_city (INTERNATIONAL), merge into cache,
      then return. Exit 0 if all found, 1 if any still missing.

  python3 scripts/air_intl_resolve_city.py --ingest <saved air_city response> [--save <cache.json>]
      Merge a saved air_city (scope=INTERNATIONAL) keyword-search response into
      the existing cache (default: references/air-intl-city-cache.json). Does not
      wipe cities already on disk. Historical intl_city responses also accepted.

  python3 scripts/air_intl_resolve_city.py --show
      Print cache statistics without dumping all rows.

Rules:
- The cache is a script-consumed dictionary. Never read the whole cache into
  chat context; `air_city` keyword responses are small and safe to read.
- Canonical city/airport code is `code` (air_city). Legacy intl_city rows used
  `cityCode`; ingest accepts both, preferring `code`.
- Aggregate rows: `aggregate=true`, or `airPort` is 所有机场, or `cityCodeList`
  is non-empty. Their code (e.g. BJS1/SIN1/SHA1) is what intl_shopping accepts
  with isFromCity/isToCity=true. Member airport codes come from `cityCodeList`.
- If no aggregate row exists for a city (single-airport city like HKG), the
  script prints the airport rows; the airport code itself is the query code.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp_envelope import unwrap, decode

SCRIPTS = Path(__file__).resolve().parent
CACHE_NOTE = (
    "国际城市码紧凑缓存（air_city scope=INTERNATIONAL），"
    "供 scripts/air_intl_resolve_city.py 查询；禁止直接读取全文进对话上下文"
)


def default_cache() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "air-intl-city-cache.json"


def empty_cache() -> dict[str, Any]:
    return {
        "schema": "fh-travel-city-cache/v1",
        "note": CACHE_NOTE,
        "count": 0,
        "cities": [],
    }


def load_cache(path: Path) -> dict[str, Any]:
    """Load cache; missing file → empty cache (auto-fetch path needs this)."""
    if not path.exists():
        return empty_cache()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cities"), list):
        raise ValueError(f"缓存格式无效: {path}")
    return data


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cache = dict(cache)
    cache["count"] = len(cache.get("cities") or [])
    cache.setdefault("schema", "fh-travel-city-cache/v1")
    cache.setdefault("note", CACHE_NOTE)
    # indent=1：进 git 时比 indent=2 省空间
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def extract_city_rows(raw: Any) -> list[Any]:
    """Accept a bare list, content envelope, or JSON-RPC tools/call payload."""
    # air_city 成功时业务结果是数组；信封失败 unwrap 得到 None，不能当成空列表静默吞掉。
    payload = unwrap(raw)
    if isinstance(payload, list):
        return payload
    raise ValueError("无法从输入中解析城市数组")


def group_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group raw air_city (or legacy intl_city) rows by city name."""
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("cityName") or "").strip()
        if not name:
            continue
        # air_city canonical field is `code`; legacy intl_city used `cityCode`.
        code = str(item.get("code") or item.get("cityCode") or "").strip()
        airport = str(item.get("airPort") or "").strip()
        if not code:
            continue
        entry = grouped.setdefault(name, {"name": name, "aggregate": "", "airportCodes": "", "airports": []})
        flagged = item.get("aggregate")
        if isinstance(flagged, bool):
            is_agg = flagged
        else:
            is_agg = airport == "所有机场" or bool(item.get("cityCodeList"))
        if is_agg and not entry["aggregate"]:
            # 同一城市多条聚合行只留第一条；BJS1 这种才是 intl_shopping 的 isFromCity=true 用码。
            entry["aggregate"] = code
            entry["airportCodes"] = str(item.get("cityCodeList") or "")
        if not any(a["code"] == code for a in entry["airports"]):
            entry["airports"].append({"code": code, "name": airport})
    return sorted(grouped.values(), key=lambda c: c["name"])


def merge_cities(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge city entries by name; keep existing aggregate/airports, add new ones."""
    by_name: dict[str, dict[str, Any]] = {str(c.get("name") or ""): dict(c) for c in existing if c.get("name")}
    for city in incoming:
        name = str(city.get("name") or "").strip()
        if not name:
            continue
        if name not in by_name:
            by_name[name] = {
                "name": name,
                "aggregate": city.get("aggregate") or "",
                "airportCodes": city.get("airportCodes") or "",
                "airports": list(city.get("airports") or []),
            }
            continue
        old = by_name[name]
        if city.get("aggregate") and not old.get("aggregate"):
            old["aggregate"] = city["aggregate"]
            old["airportCodes"] = city.get("airportCodes") or old.get("airportCodes") or ""
        old_airports = list(old.get("airports") or [])
        for ap in city.get("airports") or []:
            code = str(ap.get("code") or "")
            if code and not any(str(a.get("code") or "") == code for a in old_airports):
                old_airports.append(ap)
        old["airports"] = old_airports
    return sorted(by_name.values(), key=lambda c: c["name"])


def ingest_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a compact cache dict from raw rows only (no merge with disk)."""
    cities = group_items(items)
    return {
        "schema": "fh-travel-city-cache/v1",
        "note": CACHE_NOTE,
        "count": len(cities),
        "cities": cities,
    }


def merge_raw_into_cache(cache: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge raw air_city rows into an existing cache without dropping other cities."""
    incoming = group_items(items)
    cities = merge_cities(list(cache.get("cities") or []), incoming)
    out = dict(cache) if cache else empty_cache()
    out["cities"] = cities
    out["count"] = len(cities)
    out.setdefault("schema", "fh-travel-city-cache/v1")
    out.setdefault("note", CACHE_NOTE)
    return out


def match_cities(cache: dict[str, Any], query: str) -> list[dict[str, Any]]:
    q = query.strip().lower()
    exact: list[dict[str, Any]] = []
    code_hits: list[dict[str, Any]] = []
    loose: list[dict[str, Any]] = []
    seen: set[int] = set()
    for city in cache.get("cities") or []:
        name = str(city.get("name") or "")
        n = name.lower()
        if n == q:
            exact.append(city)
            seen.add(id(city))
        for ap in city.get("airports") or []:
            if q == str(ap.get("code") or "").lower():
                code_hits.append(city)
                seen.add(id(city))
                break
    if exact:
        return exact
    if code_hits:
        # 三字码优先于「名称包含」：输入 PEK 应落到首都机场那条，而不是名字里碰巧含 pek 的城市。
        return code_hits
    for city in cache.get("cities") or []:
        if id(city) in seen:
            continue
        name = str(city.get("name") or "")
        if name and q in name.lower():
            loose.append(city)
            seen.add(id(city))
    return loose


def _air_city_mcp(keyword: str) -> list[dict] | None:
    """调 air_city(scope=INTERNATIONAL)；失败返回 None。"""
    params = json.dumps(
        {"name": "air_city", "arguments": {"keyword": keyword, "scope": "INTERNATIONAL"}},
        ensure_ascii=False,
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "fh_travel.py"), "tools/call", params],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(SCRIPTS),
            timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        rpc = json.loads(proc.stdout)
        payload = unwrap(rpc)
        return payload if isinstance(payload, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def format_hit(city: dict[str, Any]) -> str:
    agg = city.get("aggregate") or ""
    airports = city.get("airports") or []
    # 聚合行自己也在 airports[] 里（名是「所有机场」），再列一遍会和聚合码重复。
    airport_desc = "、".join(f"{a.get('name')}({a.get('code')})" for a in airports if a.get("code") != agg)
    if agg:
        codes = city.get("airportCodes") or ""
        line = f"{city['name']}: 聚合码 {agg} (所有机场: {codes})"
        if airport_desc:
            line += f" | 机场: {airport_desc}"
        return line
    line = f"{city['name']}: 无聚合码"
    if airport_desc:
        line += f" | 机场: {airport_desc}"
    return line


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，城市中文打印会崩。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="城市名（中文/拼音/机场码）")
    parser.add_argument("--ingest", metavar="FILE", help="把 air_city（scope=INTERNATIONAL）检索响应并入缓存")
    parser.add_argument("--save", type=Path, help="缓存写出路径（默认 references/air-intl-city-cache.json）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出查询结果")
    parser.add_argument("--no-mcp", action="store_true", help="只查缓存，不调 air_city")
    args = parser.parse_args()

    cache_path = args.save or default_cache()

    if args.ingest:
        raw = decode(Path(args.ingest).read_text(encoding="utf-8"))
        items = extract_city_rows(raw)
        cache = merge_raw_into_cache(load_cache(cache_path), items)
        save_cache(cache_path, cache)
        print(f"[信息] 已合并写入缓存: {cache_path}（{cache['count']} 个城市）", file=sys.stderr)
        return 0

    if args.names and args.names[0] == "--show":
        # 没有注册 argparse --show：直接 `python ... --show` 会被当成未知开关。
        # 要统计请写成 `python ... -- --show`（-- 之后的词才进 names）。
        cache = load_cache(cache_path)
        aggregates = sum(1 for c in cache["cities"] if c.get("aggregate"))
        print(f"缓存: {cache_path} | 城市 {cache['count']} | 含聚合码 {aggregates}")
        return 0

    if not args.names:
        parser.print_usage()
        return 2

    cache = load_cache(cache_path)
    results = []
    missing = []
    dirty = False
    for name in args.names:
        hits = match_cities(cache, name)
        if not hits and not args.no_mcp:
            cands = _air_city_mcp(name)
            if cands:
                cache = merge_raw_into_cache(cache, cands)
                dirty = True
                hits = match_cities(cache, name)
        if not hits:
            missing.append(name)
            results.append({"query": name, "found": False})
        else:
            results.append({"query": name, "found": True, "cities": hits})

    if dirty:
        try:
            save_cache(cache_path, cache)
            print(f"[信息] 已回写国际城市缓存: {cache_path}（{cache['count']} 个城市）", file=sys.stderr)
        except OSError as exc:
            print(f"[信息] 城市已解析，但缓存回写失败（不影响本次）: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r["found"]:
                for city in r["cities"]:
                    print(format_hit(city))
            else:
                print(
                    f"{r['query']}: 未解析（缓存未命中且 air_city 无可用候选）",
                    file=sys.stderr,
                )
    if missing:
        print(
            f"[信息] 未命中: {', '.join(missing)}。检查城市名/登录态后重试；"
            f"勿并行多次 --ingest（现已自动合并，一条龙会自行补缓存）。",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
