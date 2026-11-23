#!/usr/bin/env python3
"""Build a Feihe frontend jump link (免登跳转) from query context — never hardcode a route.

The Feihe CRM frontend reads identity from the URL hash query after
`/oauth2/forward` injects login (query `authCode` = 当次 shopping 的 `forwardCode`)。
This script only *assembles the target route* from real query facts (cities,
dates, passenger count, fee type, trip shape). It does not fetch tokens, call
MCP, or know any specific city/date.

The assembled route is wrapped as HTTPS
  `https://<portal-host>/api/portal/mcp/oauth2/forward?redirectPage=<encoded-route>&authCode=<forwardCode>`.

Two encoding pitfalls are handled automatically (see references/sso-forward.md;
implementation is `scripts/sso_forward.py`, shared with the order-page builder):
  1. Chinese in redirectPage → the server decodes it, Tomcat drops non-ASCII
     Location headers → a 302 with no Location. Chinese values are double-encoded.
  2. A bare space (e.g. "Baoan Airport") → server `new URI()` throws
     "Illegal character in fragment", forward degrades to error_code=login_error.
     Space must stay percent-encoded, never decoded to a raw space.

Usage:
  python3 scripts/air_intl_build_jump_url.py --from "深圳" --from-code SZX --from-en Shenzhen \
      --from-airport 宝安机场 --from-airport-en "Baoan Airport" --from-country 中国 --from-country-en China \
      --to "巴厘岛" --to-code DPS --to-en "Bali Island" --to-airport 努拉莱伊机场 --to-airport-en "Nuralei Airport" \
      --to-country 印度尼西亚 --to-country-en Indonesia \
      --date 2026-09-02 --adult 1 --fee-type 公费出行 \
      --forward-code <当次 intl_shopping 的 forwardCode>

  # 只给最小字段（其余用页面表单默认态）：
  python3 scripts/air_intl_build_jump_url.py --from 深圳 --from-code SZX --to 巴厘岛 --to-code DPS --date 2026-09-02 \
      --forward-code <forwardCode>
"""

from __future__ import annotations

import argparse
import json
import sys

from sso_forward import assemble_route, build_forward_url, join_query
from portal_config import portal_host as _portal_host


# 目标页 hash 路由里"表单默认态"的固定字段。这些不是业务数据，是前端搜索页的
# 初始控件状态，跳过去让页面按预设条件展示即可，故收敛为常量。
# allianceCode 留空键是为了和页面字段表对齐；join_query 会省略空值，URL 里不会出现 allianceCode=。
DEFAULT_FORM_STATE = {
    "level": "不限",
    "isText": "0",
    "isTurn": "0",
    "allianceCode": "",
}

# 目标页相对路径（hash 之前的部分）。国际/国内用同一入口，路径固定。
# 不要在这里写死任何城市/日期/机场——那些走参数。
FRONTEND_PAGE = "/VuePage/international/index.html"
LIST_HASH = "/?"


def build_route(fields: dict[str, str]) -> str:
    """Assemble the full frontend route: page path + '#' + '/?' + encoded query."""
    # 列表页字段是裸中文/空格，必须 encode=True 走双重编码；下单页 flightList 已编过，那边是 False。
    return assemble_route(FRONTEND_PAGE, LIST_HASH, join_query(fields, encode=True))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，城市中文/机场名打印会崩。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    # 出发地
    parser.add_argument("--from", dest="from_city", help="出发城市中文名")
    parser.add_argument("--from-code", dest="from_code", help="出发机场/城市码（如 SZX）")
    parser.add_argument("--from-en", dest="from_en", help="出发城市英文名")
    parser.add_argument("--from-airport", dest="from_airport", help="出发机场中文名")
    parser.add_argument("--from-airport-en", dest="from_airport_en", help="出发机场英文名")
    parser.add_argument("--from-country", dest="from_country", help="出发国家中文名")
    parser.add_argument("--from-country-en", dest="from_country_en", help="出发国家英文名")
    # 目的地
    parser.add_argument("--to", dest="to_city", help="目的城市中文名")
    parser.add_argument("--to-code", dest="to_code", help="目的机场/城市码（如 DPS）")
    parser.add_argument("--to-en", dest="to_en", help="目的城市英文名")
    parser.add_argument("--to-airport", dest="to_airport", help="目的机场中文名")
    parser.add_argument("--to-airport-en", dest="to_airport_en", help="目的机场英文名")
    parser.add_argument("--to-country", dest="to_country", help="目的国家中文名")
    parser.add_argument("--to-country-en", dest="to_country_en", help="目的国家英文名")
    # 通用
    parser.add_argument("--date", help="出发日期 yyyy-MM-dd")
    parser.add_argument("--adult", default="1", help="成人数")
    parser.add_argument("--fee-type", dest="fee_type", default="公费出行", help="费用类型（公费出行/私费出行）")
    parser.add_argument("--trip-mode", dest="trip_mode", choices=["单程", "往返", "多程"], default="单程")
    # --trip-mode 目前未写入 fields：列表页行程类型走页面默认控件，URL 观察里没有对应键。
    # 输出形态
    parser.add_argument("--portal-host", dest="portal_host", default=_portal_host(), help="portal 主机（默认读 config.json）")
    parser.add_argument("--forward-code", dest="forward_code", default="", help="当次 intl_shopping 的 forwardCode（拼入 query authCode）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出 route + url")
    args = parser.parse_args()

    # 目标页字段顺序与命名对齐前端（来自真实页面 URL 观察），仅当有值才带上。
    fields: dict[str, str] = {}
    fields.update(DEFAULT_FORM_STATE)
    fields["adultCount"] = args.adult
    fields["startDate"] = args.date
    fields["startCity"] = args.from_city
    fields["startCityEn"] = args.from_en
    fields["startCode"] = args.from_code
    fields["startCountry"] = args.from_country
    fields["startCountryEn"] = args.from_country_en
    fields["startAirPort"] = args.from_airport
    fields["startAirPortEn"] = args.from_airport_en
    # 前端字段名就是 array 不是 arrive，按页面 URL 原样拼，改成 arrive 页面读不到。
    fields["arrayCity"] = args.to_city
    fields["arrayCityEn"] = args.to_en
    fields["arrayCode"] = args.to_code
    fields["arrayCountry"] = args.to_country
    fields["arrayCountryEn"] = args.to_country_en
    fields["arrayAirPort"] = args.to_airport
    fields["arrayAirPortEn"] = args.to_airport_en
    fields["feeType"] = args.fee_type

    route = build_route(fields)
    if not args.forward_code:
        print("[错误] 需要 --forward-code（当次 intl_shopping 最外层 forwardCode）", file=sys.stderr)
        return 1
    url = build_forward_url(route, args.portal_host, args.forward_code)

    if args.json:
        print(json.dumps({"route": route, "url": url}, ensure_ascii=False, indent=2))
    else:
        print(url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
