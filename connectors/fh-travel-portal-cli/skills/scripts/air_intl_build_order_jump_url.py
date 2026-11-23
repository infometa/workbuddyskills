#!/usr/bin/env python3
"""Build a Feihe order-page (下单页) jump link from the selected-flight/cabin result.

国际机票「选航班 → 选舱位」两步走完后，把产出的标识拼成下单页
`#/bookingPricing` 的路由，供 `/oauth2/forward` 免登跳转使用。
编码与包装实现见 `scripts/sso_forward.py` / `references/sso-forward.md`。

下单页 URL 结构（来自真实页面观察，2026-09-02 更新）：
  #/bookingPricing?flightList=<urlencoded-json-array>&flyType=1&adultCount=1
      &payType=1&agent=1[&applicationId=][&dh=]

其中 flightList 是**整体 JSON 数组编码一次**，数组每一项是二元组：
  {serialNumber, priceId}
  - serialNumber : 来自同一次 intl_shopping（组合查询会话标识）
  - priceId      : 来自 intl_shopping_all_cab（选舱后某舱位的 priceId，三段式
                   "36056399531212808/100000/6" 这种）

不再需要 pricingId：bookingPricing 页只接 serialNumber + priceId；验价能力当前未在
MCP 暴露，下单页跳转也不经过验价。

必传字段：
  - flightList  : [{serialNumber, priceId}]（可多段，往返/多程按出行原始顺序）
  - flyType     : 1=单程，2=往返，3=多程
  - adultCount  : 查询时的同行人数
  - payType     : 1=公费（因公挂账），0=自费
  - agent       : '1'（agent 内置环境）
非必传：
  - applicationId : 出差单 id
  - dh            : 出差单号

本脚本只负责「拼接路由」，不调 MCP、不读 CLI 凭据、不知道任何具体城市/日期。

Usage:
  # 单个航段（单程 / 一个已选组合）
  python3 scripts/air_intl_build_order_jump_url.py \
      --serial-number 260902162025A0000001 \
      --price-id "36056399531212808/100000/6" \
      --adult 1 --pay-type 1 --fly-type 1 \
      --forward-code <forwardCode>

  # 多个航段（往返 / 多程）：--flight 可重复，顺序即出行原始顺序
  python3 scripts/air_intl_build_order_jump_url.py \
      --flight '{"serialNumber":"A","priceId":"x/y/1"}' \
      --flight '{"serialNumber":"B","priceId":"m/n/2"}' \
      --adult 1 --fly-type 2 \
      --forward-code <forwardCode>

  # 直接给整段 JSON 数组（与 --flight 二选一）
  python3 scripts/air_intl_build_order_jump_url.py \
      --flight-list '[{"serialNumber":"A","priceId":"x/y/1"}]' \
      --adult 1 --forward-code <forwardCode>

  python3 scripts/air_intl_build_order_jump_url.py ... --json
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

from sso_forward import (
    assemble_route,
    build_forward_url,
    join_query,
)
from portal_config import portal_host as _portal_host


# 下单页相对路径（hash 之前的部分）。国际下单页路由固定。
FRONTEND_PAGE = "/VuePage/international/index.html"
# 下单页 hash 里的路由名（不是列表页的 "/?"）
ORDER_ROUTE = "/bookingPricing"


def _encode_flight_list(items: list[dict[str, str]]) -> str:
    """整体编码 flightList JSON 数组，复刻下单页 URL 形态。

    服务端/前端期望 `[`→`%5B`、`{`→`%7B`、`"`→`%22`、`:`→`%3A`，
    但 `,` 和 `/` 保持原样（裸字符，逗号与斜杠都是 fragment 里的合法字符）。
    对齐真实下单页 URL：`,` 裸、priceId 里的 `/` 裸。
    """
    raw = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    return quote(raw, safe=",/")


def build_order_route(
    flight_items: list[dict[str, str]],
    adult: str = "1",
    pay_type: str = "1",
    fly_type: str = "1",
    agent: str = "1",
    application_id: str = "",
    dh: str = "",
) -> str:
    """Assemble the full order-page route: page path + '#' + '/bookingPricing' + query."""
    fields = {
        "flightList": _encode_flight_list(flight_items),
        "flyType": fly_type,
        "adultCount": adult,
        "payType": pay_type,
        "agent": agent,
    }
    # 非必传字段：仅当有值才带上（applicationId/dh 都是可选，留空则省略）
    if application_id:
        fields["applicationId"] = application_id
    if dh:
        fields["dh"] = dh
    # flightList 已经 quote 过；encode=True 会把 %5B 变成 %255B，下单页解析失败。
    return assemble_route(FRONTEND_PAGE, ORDER_ROUTE, join_query(fields, encode=False))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，priceId 里虽是 ASCII，JSON 输出的中文说明仍会崩。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    # 二元组：既支持逐字段传，也支持整段 JSON
    parser.add_argument("--serial-number", dest="serial_number", help="serialNumber（单航段时用）")
    parser.add_argument("--price-id", dest="price_id", help="舱位 priceId（单航段时用）")
    parser.add_argument("--flight", action="append", default=[], help="单段二元组 JSON，可重复")
    parser.add_argument("--flight-list", dest="flight_list", help="整段 JSON 数组（与 --flight 二选一）")
    # 下单页字段
    parser.add_argument("--adult", default="1", help="同行人数（adultCount）")
    parser.add_argument("--pay-type", dest="pay_type", default="1", help="1=公费（因公挂账），0=自费")
    parser.add_argument("--fly-type", dest="fly_type", default="1", help="1=单程，2=往返，3=多程")
    parser.add_argument("--agent", default="1", help="agent 内置环境（固定 1）")
    parser.add_argument("--application-id", dest="application_id", default="", help="出差单 id（可选）")
    parser.add_argument("--dh", default="", help="出差单号（可选）")
    # 输出形态
    parser.add_argument("--portal-host", dest="portal_host", default=_portal_host(), help="portal 主机（默认读 config.json）")
    parser.add_argument("--forward-code", dest="forward_code", default="", help="当次 intl_shopping 的 forwardCode（拼入 query authCode）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出 route + url")
    args = parser.parse_args()

    # 组装二元组列表。三种入口可叠加：先 --flight-list，再重复 --flight，最后单段字段。
    flight_items: list[dict[str, str]] = []
    if args.flight_list:
        try:
            flight_items = json.loads(args.flight_list)
        except json.JSONDecodeError as exc:
            print(f"[错误] --flight-list 不是合法 JSON：{exc}", file=sys.stderr)
            return 1
        if not isinstance(flight_items, list):
            print("[错误] --flight-list 必须是 JSON 数组", file=sys.stderr)
            return 1
    for item in args.flight:
        try:
            flight_items.append(json.loads(item))
        except json.JSONDecodeError as exc:
            print(f"[错误] --flight 不是合法 JSON：{exc}", file=sys.stderr)
            return 1
    if args.serial_number is not None:
        flight_items.append({
            "serialNumber": args.serial_number,
            "priceId": args.price_id or "",
        })

    if not flight_items:
        print("[错误] 至少提供一段二元组（--serial-number/--price-id 或 --flight 或 --flight-list）", file=sys.stderr)
        return 1
    for item in flight_items:
        if not isinstance(item, dict) or not item.get("serialNumber") or not item.get("priceId"):
            print(f"[错误] 二元组缺少 serialNumber/priceId：{item}", file=sys.stderr)
            return 1

    route = build_order_route(
        flight_items, args.adult, args.pay_type, args.fly_type, args.agent,
        args.application_id, args.dh,
    )
    if not args.forward_code:
        print("[错误] 需要 --forward-code（当次 intl_shopping 最外层 forwardCode）", file=sys.stderr)
        return 1
    url = build_forward_url(route, args.portal_host, args.forward_code)

    if args.json:
        print(json.dumps({"route": route, "url": url, "flightList": flight_items}, ensure_ascii=False, indent=2))
    else:
        print(url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
