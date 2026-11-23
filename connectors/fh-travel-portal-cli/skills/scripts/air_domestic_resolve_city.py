#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国内城市码解析：本地缓存优先，未命中自动调 air_city(scope=DOMESTIC) 并回写缓存。

`air_city` 业务在协议层 structuredContent（数组在 data 下）；本脚本用 mcp_envelope.unwrap
拆封后回写 references/domestic-city-cache.json，重复查询零 MCP 往返。

用法:
  python3 scripts/air_domestic_resolve_city.py --json 北京 上海
      查缓存（未命中自动调 air_city 并回写）；输出 JSON 数组：
      [{"name":"北京","found":true,"code":"BJS1","cityName":"北京","source":"cache|mcp"}]
      全部命中 exit 0，任一未解析 exit 1。

  python3 scripts/air_domestic_resolve_city.py 北京 上海
      同上但输出人读行：北京=BJS1(缓存)。

规则:
- code 取 air_city 返回的 `code` 原值（BJS1/CTU1 这类聚合码虽然 aggregate=false，
  但 code 本身就是聚合码，直接用于 domestic_shopping 可带出该城市全部机场）。
- 禁止把三字码改写成聚合码、禁止凭记忆猜码。
- 缓存是脚本消费的字典，不要整份读进对话。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS.parent
CACHE = SKILL_DIR / "references" / "domestic-city-cache.json"

sys.path.insert(0, str(SCRIPTS))
from mcp_envelope import unwrap  # noqa: E402


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _air_city_mcp(keyword: str) -> list[dict] | None:
    """调 air_city(scope=DOMESTIC) 取候选；失败返回 None（不抛，由调用方降级）。"""
    params = json.dumps({"name": "air_city",
                         "arguments": {"keyword": keyword, "scope": "DOMESTIC"}},
                        ensure_ascii=False)
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "fh_travel.py"), "tools/call", params],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(SCRIPTS), timeout=90,
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


def _is_airport(row: dict) -> bool:
    """判断 air_city 候选行是否真是机场。

    air_city 会把同城的港口、汽车站、火车站一并返回，且排序不保证机场在前。
    「所有机场」聚合行天然是机场；否则按 airPort 名称特征判定：
    先排除明确的非机场设施，再要求命中机场特征词。
    """
    port = str(row.get("airPort") or "")
    if port == "所有机场":
        return True
    if any(bad in port for bad in ("港", "码头", "汽车站", "客运站", "火车站", "高铁站")):
        return False
    return any(good in port for good in ("机场", "航站楼"))


def resolve(name: str, *, use_mcp: bool = True) -> dict:
    cache = _load_cache()
    hit = cache.get(name)
    if hit and hit.get("code"):
        return {"name": name, "found": True, "code": hit["code"],
                "cityName": hit.get("cityName") or name, "source": "cache"}
    if not use_mcp:
        return {"name": name, "found": False, "code": "", "cityName": "", "source": ""}
    cands = _air_city_mcp(name)
    if not cands:
        return {"name": name, "found": False, "code": "", "cityName": "", "source": ""}
    # 必须排除港口/码头/汽车站/火车站等非机场设施。
    # 触发场景：air_city 对「广州」默认只返回 NSZ(广州南沙港)、对「杭州」返回 HHL(杭州旅游中心汽车站)，
    # 这些码传给 domestic_shopping 会报「机场三字码不能是国际城市」或查不到航班。
    # 排除后若候选为空，说明该关键词没命中机场，交由调用方重试（如改用机场名）。
    airport_rows = [c for c in cands if _is_airport(c)]
    if not airport_rows:
        return {"name": name, "found": False, "code": "", "cityName": "", "source": ""}
    # 优先聚合码行（airPort=所有机场，覆盖该城全部机场），否则取第一条的 code 原值
    pick = next((c for c in airport_rows if str(c.get("airPort") or "") == "所有机场"),
                airport_rows[0])
    code = str(pick.get("code") or "").strip()
    if not code:
        return {"name": name, "found": False, "code": "", "cityName": "", "source": ""}
    row = {"code": code, "cityName": pick.get("cityName") or name,
           "airPort": pick.get("airPort") or ""}
    cache[name] = row
    cache.setdefault("_meta", {})
    try:
        _save_cache(cache)
    except OSError:
        pass  # 缓存写失败不影响解析结果
    return {"name": name, "found": True, "code": code,
            "cityName": row["cityName"], "source": "mcp"}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="国内城市码解析（缓存优先，air_city 兜底）")
    ap.add_argument("cities", nargs="+", help="城市中文名（用户原文）")
    ap.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON（脚本消费）")
    ap.add_argument("--no-mcp", action="store_true", help="只查缓存，不调 air_city")
    args = ap.parse_args()

    results = [resolve(c, use_mcp=not args.no_mcp) for c in args.cities]
    if args.as_json:
        print(json.dumps(results, ensure_ascii=False))
    else:
        for r in results:
            if r["found"]:
                print(f"{r['name']}={r['code']}({r['cityName']},{'缓存' if r['source'] == 'cache' else 'air_city'})")
            else:
                print(f"{r['name']}=未解析（air_city 无候选）")
    return 0 if all(r["found"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
