#!/usr/bin/env python3
"""Render normalized international flight options as safe interactive HTML.

三种 action：
- select-flight：仅展示航班（air_intl_parse_shopping 产物），无下单动作。
- select-cabin：舱位页（air_intl_book cabins 产物），每个舱位一个「去下单」HTTPS forward 链接。
- inline-cabins（推荐）：航班页内联展开舱位，每个舱位一个「去下单」HTTPS forward 链接。

v2.3.0 起采用「静态预渲染 + HTML 原生交互」架构（参考 feihe-travel 风格）：
- Python 端把全部航班卡/舱位表/KPI 静态写入 HTML，无 JS 也能看首屏（WorkBuddy 预览面板不执行 JS）。
- <details>+<summary> 原生展开舱位，蓝色「去下单」<a href> 按钮（HTTPS forward，点击直接进飞鹤下单页）。
- JS 仅渐进增强（筛选/排序/搜索，用 data 属性显示隐藏，外部浏览器生效）。
- 无 base64 payload：页面只内嵌 shopping 下发的 infoCode / forwardCode，不写 MCP token。
复制指令、自定义协议深链、JS shell 已全部移除。

Usage:
  python3 air_intl_render_flight_options.py parsed.json --action inline-cabins --cabins cabins_by_option.json
  python3 air_intl_render_flight_options.py cabins_normalized.json --action select-cabin
  python3 air_intl_render_flight_options.py parsed.json --output flights.html --map-output flights.selection-map.json
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from air_intl_build_order_jump_url import build_order_route
    from sso_forward import build_forward_url
    from portal_config import mcp_base, portal_host, forward_base, intl_shop_url
except ImportError:  # standalone 渲染（无下单链接）时允许缺拼 URL 基建
    build_order_route = None
    build_forward_url = None
    mcp_base = None
    portal_host = None
    forward_base = None
    intl_shop_url = None


ORDER_DEFAULTS = {
    "adult": "1",
    "pay_type": "1",
    "fly_type": "1",
    "agent": "1",
    # portal_host 在 main 里用 portal_host() 填；这里仅作缺模块时的空默认
    "portal_host": "",
}


def _text(value: Any, default: str = "") -> str:
    return str(value) if value is not None else default


def _public_record(record: dict[str, Any], option_key: str) -> dict[str, Any]:
    # 公开航班卡不带 serialNumber：会话号只进 selection-map 和 forward URL，避免写进可转发的 HTML 正文。
    def public_leg(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "flightNo": _text(raw.get("flightNo")),
            "airline": _text(raw.get("airline")),
            "airlineCode": _text(raw.get("airlineCode")),
            "from": _text(raw.get("from"), "--"),
            "to": _text(raw.get("to"), "--"),
            "fromCode": _text(raw.get("fromCode")),
            "toCode": _text(raw.get("toCode")),
            "fromTerminal": _text(raw.get("fromTerminal")),
            "toTerminal": _text(raw.get("toTerminal")),
            "dep": _text(raw.get("dep"), "--"),
            "arr": _text(raw.get("arr"), "--"),
            "dur": raw.get("dur"),
            "aircraft": _text(raw.get("aircraft")),
            "aircraftName": _text(raw.get("aircraftName")),
            "operatingFlightNo": _text(raw.get("operatingFlightNo")),
        }

    legs = []
    for raw in record.get("legs") or []:
        if not isinstance(raw, dict):
            continue
        legs.append(public_leg(raw))
    journeys = []
    for raw_journey in record.get("journeys") or []:
        if not isinstance(raw_journey, dict):
            continue
        journey_legs = [public_leg(leg) for leg in raw_journey.get("legs") or [] if isinstance(leg, dict)]
        if journey_legs:
            journeys.append({
                "legs": journey_legs,
                "from": _text(raw_journey.get("from") or journey_legs[0].get("from"), "--"),
                "to": _text(raw_journey.get("to") or journey_legs[-1].get("to"), "--"),
                "fromCode": _text(raw_journey.get("fromCode") or journey_legs[0].get("fromCode")),
                "toCode": _text(raw_journey.get("toCode") or journey_legs[-1].get("toCode")),
                "dep": _text(raw_journey.get("dep") or journey_legs[0].get("dep"), "--"),
                "arr": _text(raw_journey.get("arr") or journey_legs[-1].get("arr"), "--"),
                "flightDurationMin": raw_journey.get("flightDurationMin"),
                "layoverMin": raw_journey.get("layoverMin"),
                "stops": raw_journey.get("stops"),
            })
    if not journeys and legs:
        journeys = [{
            "legs": legs,
            "from": legs[0].get("from", "--"),
            "to": legs[-1].get("to", "--"),
            "fromCode": legs[0].get("fromCode", ""),
            "toCode": legs[-1].get("toCode", ""),
            "dep": legs[0].get("dep", "--"),
            "arr": legs[-1].get("arr", "--"),
            "flightDurationMin": sum(int(leg.get("dur") or 0) for leg in legs),
            "layoverMin": record.get("layoverMin"),
            "stops": record.get("stops"),
        }]
    return {
        "optionKey": option_key,
        "rank": record.get("rank"),
        "direct": bool(record.get("direct")),
        "recommended": bool(record.get("recommended")),
        "legs": legs,
        "journeys": journeys,
        "cabin": _text(record.get("cabin"), "--"),
        "fareName": _text(record.get("fareName")),
        "total": record.get("total"),
        "fare": record.get("fare"),
        "tax": record.get("tax"),
        "addPrice": record.get("addPrice"),
        "servicePrice": record.get("servicePrice"),
        "totalDurMin": record.get("totalDurMin"),
        "doorToDoorMin": record.get("doorToDoorMin"),
        "layoverMin": record.get("layoverMin"),
        "stops": record.get("stops"),
        "transferAirports": record.get("transferAirports") or [],
        "sameAirport": bool(record.get("sameAirport", True)),
        "lcc": bool(record.get("lcc")),
        "baggage": record.get("baggage") or {"check": "", "carry": ""},
        "refundable": bool(record.get("refundable")),
        "changeable": bool(record.get("changeable")),
        "upgradable": bool(record.get("upgradable")),
        "agreement": bool(record.get("agreement")),
        # 渠道与大客户字段（v3.19.0）：共享航班/价格来源/代购/大客户协议价
        "codeshare": bool(record.get("codeshare")),
        "operatedBy": record.get("operatedBy") or [],
        "source": _text(record.get("source")),
        "allowTicket": bool(record.get("allowTicket", True)),
        "bigCustomer": _text(record.get("bigCustomer")),
        "selfBig": bool(record.get("selfBig")),
        "bigCustomerPrice": record.get("bigCustomerPrice") is True,
        "specialRate": record.get("specialRate"),
        "priceRules": record.get("priceRules") or [],
        "priceId": record.get("priceId"),
    }


def _selection_record(record: dict[str, Any]) -> dict[str, Any]:
    # map 只留给下一步 all_cab/order 的标识，不要把 legs 整份写进去。
    return {
        key: record.get(key)
        for key in ("serialNumber", "groupId", "priceId", "rank")
        if record.get(key) is not None
    }


def _build_order_url(serial_number: str | None, price_id: Any,
                     forward_code: str, order_params: dict[str, str]) -> str:
    """拼 HTTPS forward 下单链接（/oauth2/forward 换 forwardCode → 302 bookingPricing 已免登）。"""
    if not serial_number or not price_id or build_order_route is None:
        return ""
    route = build_order_route(
        [{"serialNumber": serial_number, "priceId": str(price_id)}],
        adult=order_params["adult"],
        pay_type=order_params["pay_type"],
        fly_type=order_params["fly_type"],
        agent=order_params["agent"],
    )
    return build_forward_url(route, order_params["portal_host"], forward_code or "")


def _cabin_public(cabin: dict[str, Any], serial_number: str | None,
                  forward_code: str, order_params: dict[str, str]) -> dict[str, Any]:
    refund = ["可退" if cabin.get("refundable") else "不可退",
              "可改" if cabin.get("changeable") else "不可改"]
    label = _text(cabin.get("cabin")) or _text(cabin.get("label"))
    return {
        "key": _text(cabin.get("key") or cabin.get("optionKey")),
        "label": label,
        "total": cabin.get("total") if cabin.get("total") is not None else cabin.get("totalPrice"),
        "fare": cabin.get("fare"),
        "tax": cabin.get("tax"),
        "addPrice": cabin.get("addPrice"),
        "servicePrice": cabin.get("servicePrice"),
        "refundText": "/".join(refund),
        "refundable": bool(cabin.get("refundable")),
        "recommend": bool(cabin.get("recommend")),
        "allowTicket": bool(cabin.get("allowTicket", True)),
        "bigCustomer": _text(cabin.get("bigCustomer")),
        "selfBig": bool(cabin.get("selfBig")),
        "bigCustomerPrice": cabin.get("bigCustomerPrice") is True,
        "specialRate": cabin.get("specialRate"),
        "priceRules": cabin.get("priceRules") or [],
        "source": _text(cabin.get("source")),
        "orderUrl": _build_order_url(serial_number, cabin.get("priceId"), forward_code, order_params),
    }


# == 静态预渲染辅助函数（feihe-travel 风格）==

def _esc(s: Any) -> str:
    """HTML 转义。"""
    return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _dur_text(min_val: Any) -> str:
    """时长格式化（分钟 -> Xh Ym）。"""
    try:
        n = float(min_val)
    except (TypeError, ValueError):
        return "--"
    h, m = int(n // 60), int(round(n % 60))
    return f"{h}h{m:02d}m" if h else f"{m}m"


def _money(value: Any) -> str:
    """金额格式化：整数不带小数，空值返回空串。"""
    if value is None or value == "":
        return ""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{f:.0f}" if f == int(f) else f"{f:.2f}"


def _fee_breakdown(tax: Any, service_price: Any = None) -> str:
    """费用拆分小字：只显示税与服务费（v6.0.3 起票价并入总价、附加费一律不展示）。"""
    parts = []
    tax_s, svc_s = _money(tax), _money(service_price)
    if tax_s:
        parts.append(f"税¥{tax_s}")
    if svc_s and float(service_price) > 0:
        parts.append(f"服务费¥{svc_s}")
    return " · ".join(parts)


_CITY_NAMES: dict[str, str] = {}


def _load_city_names() -> dict[str, str]:
    """机场码 → 城市名（references/air-intl-city-cache.json，v6.0.9 中转行用）。

    懒加载且只建索引；缓存文件缺失/损坏时返回空表，调用方退回机场名。"""
    global _CITY_NAMES
    if _CITY_NAMES:
        return _CITY_NAMES
    cache = Path(__file__).resolve().parent.parent / "references" / "air-intl-city-cache.json"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        names: dict[str, str] = {}
        for city in data.get("cities") or []:
            cname = str(city.get("name") or "")
            if not cname:
                continue
            for ap in city.get("airports") or []:
                code = str(ap.get("code") or "")
                if code:
                    names[code] = cname
        _CITY_NAMES = names
    except (OSError, ValueError):
        _CITY_NAMES = {}
    return _CITY_NAMES


_DT_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})")


def _hm(value: Any) -> tuple[str, tuple[int, int, int] | None]:
    """'2026-09-19 08:00:00' -> ('08:00', (2026,9,19))；解析失败原样返回、日期 None。"""
    m = _DT_RE.match(str(value or "").strip())
    if not m:
        return str(value or "--"), None
    return f"{m.group(4)}:{m.group(5)}", (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _rule_label(desc: str) -> str:
    """特殊价规则转写为限制标识：「允许国籍：中国(CN)」→「限中国大陆乘客预订」。"""
    m = re.match(r"允许国籍[：:]\s*(.+?)(?:\(([A-Z]{2})\))?\s*$", desc or "")
    if m:
        nation = m.group(1).strip()
        if nation in ("中国", "CN"):
            nation = "中国大陆"
        return f"限{nation}乘客预订"
    return (desc or "").strip()


def _channel_tags(item: dict[str, Any], *, with_agreement: bool = True) -> list[str]:
    """大客户价格标记（v3.19.1 口径，航班卡与舱位行共用）。

    - 特殊价（specialRate=1）：有特殊规则的协议价 → 「特殊价」+ 限制标识
      （如「限中国大陆乘客预订」，由 ruleList.ruleDesc 转写）。
    - 协议价（bigCustomerPrice 或 customersId/selfBig 非空、无 specialRate）：大客户号价 → 仅显示「大客户协议价」。
    - 渠道来源（同程/NDC/直连）与代购标记按用户要求不在页面展示（数据仍在 parsed.json）。
    """
    tags: list[str] = []
    if not with_agreement:
        return tags
    if item.get("specialRate"):
        tags.append('<span class="tg tg-d">特殊价</span>')
        for rule in item.get("priceRules") or []:
            label = _rule_label(str(rule))
            if label:
                tags.append(f'<span class="tg tg-c">{_esc(label)}</span>')
    elif item.get("agreement") or item.get("bigCustomer") or item.get("selfBig") or item.get("bigCustomerPrice"):
        tags.append('<span class="tg tg-d">大客户协议价</span>')
    return tags


def _static_kpis(flights: list) -> str:
    total = len(flights)
    direct = sum(1 for f in flights if f.get("direct"))
    transfer = total - direct
    airlines = sorted(set(l.get("airline", "") for f in flights for l in f.get("legs", []) if l.get("airline")))
    prices = [f.get("total") for f in flights if f.get("total") is not None]
    min_price = min(prices) if prices else None
    min_flight = next((f for f in flights if f.get("total") == min_price), None)
    parts = [f'<div class="kpi"><div class="v">{total}<em>个</em></div><div class="l">全部方案 直飞{direct}/中转{transfer}</div></div>']
    if min_price is not None and min_flight:
        parts.append(f'<div class="kpi"><div class="v">¥{min_price}<em>起</em></div><div class="l">最低含税价 {min_flight.get("optionKey", "")}</div></div>')
    parts.append(f'<div class="kpi"><div class="v">{len(airlines)}<em>家</em></div><div class="l">执飞航司</div></div>')
    return "".join(parts)


def _static_air_opts(flights: list) -> str:
    airlines = sorted(set(l.get("airline", "") for f in flights for l in f.get("legs", []) if l.get("airline")))
    return '<option value="">全部航司</option>' + "".join(f'<option value="{_esc(a)}">{_esc(a)}</option>' for a in airlines)


def _static_cabin_row(cabin: dict) -> str:
    label = _esc(cabin.get("label", ""))
    refund = _esc(cabin.get("refundText", "—"))
    total = cabin.get("total")
    price_html = f"¥{total}" if total is not None else "—"
    # v6.0.3：舱位行费用拆分只显示税/服务费（票价并入总价、附加费不展示）。
    fee = _fee_breakdown(cabin.get("tax"), cabin.get("servicePrice"))
    fee_html = f'<div class="cab-px">{_esc(fee)}</div>' if fee else ""
    tags = []
    if cabin.get("recommend"):
        tags.append('<span class="tg tg-a">推荐</span>')
    tags.extend(_channel_tags(cabin))
    tags_html = f'<div class="cab-tags">{"".join(tags)}</div>' if tags else ""
    order_url = cabin.get("orderUrl", "")
    if order_url:
        # 新标签打开，noopener 避免预览面板把带 forwardCode 的下单页嵌进 iframe。
        btn = f'<a class="btn-book" href="{_esc(order_url)}" target="_blank" rel="noopener">去下单</a>'
    else:
        btn = '<span class="cab-dim">无链接</span>'
    return (f'<tr><td><span class="cab-code">{label}</span>{tags_html}</td>'
            f'<td><span class="cab-name">{refund}</span></td>'
            f'<td class="prcell"><span class="price-n">{price_html}</span>{fee_html}</td>'
            f'<td style="text-align:right">{btn}</td></tr>')


def _static_leg_row(leg: dict) -> str:
    """展开区航段明细行：航班号 航司 · 起降时刻+航站楼 · 时长 · 机型 · 共享标记。"""
    dep, dep_day = _hm(leg.get("dep"))
    arr, arr_day = _hm(leg.get("arr"))
    arr_html = _esc(arr)
    if dep_day and arr_day:
        day_diff = (date(*arr_day) - date(*dep_day)).days
        if day_diff > 0:
            arr_html += f"<em class='plus1'>+{day_diff}</em>"
    from_t = leg.get("fromTerminal") or ""
    to_t = leg.get("toTerminal") or ""
    from_label = f'{leg.get("from", leg.get("fromCode", ""))}{f" · {from_t}" if from_t else ""}'
    to_label = f'{leg.get("to", leg.get("toCode", ""))}{f" · {to_t}" if to_t else ""}'
    aircraft = leg.get("aircraftName") or leg.get("aircraft") or ""
    if leg.get("aircraftName") and leg.get("aircraft"):
        aircraft = f'{leg["aircraftName"]} {leg["aircraft"]}'
    share = (f'<span class="tg tg-b">实际承运 {_esc(leg["operatingFlightNo"])}</span>'
             if leg.get("operatingFlightNo") else "")
    return (f'<div class="leg-row"><span class="leg-no">{_esc(leg.get("flightNo", ""))}</span>'
            f'<span class="leg-air">{_esc(leg.get("airline", ""))}</span>'
            f'<span class="leg-t">{_esc(dep)} → {arr_html}</span>'
            f'<span class="leg-ap">{_esc(from_label)} → {_esc(to_label)}</span>'
            f'<span class="leg-dur">{_esc(_dur_text(leg.get("dur")))}</span>'
            f'<span class="leg-ac">{_esc(aircraft)}</span>{share}</div>')


def _static_flight_card(flight: dict, idx: int, action: str, serial_number: str = "") -> str:
    legs = flight.get("legs") or []
    if not legs:
        return ""
    journeys = flight.get("journeys") or [{
        "legs": legs,
        "from": legs[0].get("from", "--"),
        "to": legs[-1].get("to", "--"),
        "dep": legs[0].get("dep", "--"),
        "arr": legs[-1].get("arr", "--"),
        "flightDurationMin": sum(int(leg.get("dur") or 0) for leg in legs),
    }]
    first, last = legs[0], legs[-1]
    dep, dep_day = _hm(first.get("dep"))
    arr, arr_day = _hm(last.get("arr"))
    arr_html = _esc(arr)
    if dep_day and arr_day:
        # 跨天到达：08:00→00:45(+1)。用真实日期差，跨月也对。
        day_diff = (date(*arr_day) - date(*dep_day)).days
        if day_diff > 0:
            arr_html += f"<em class='plus1'>+{day_diff}</em>"
    from_city = first.get("from", "--")
    to_city = last.get("to", "--")
    # 主时长只展示飞行时长；中转停留另列在中转信息中。
    dur_text = _dur_text(flight.get("totalDurMin"))
    dur_val = flight.get("totalDurMin") or 0
    flight_no = first.get("flightNo", "")
    airline = first.get("airline", "")
    aircraft = first.get("aircraftName") or first.get("aircraft", "")
    if first.get("aircraftName") and first.get("aircraft"):
        aircraft = f'{first["aircraftName"]} {first["aircraft"]}'
    total = flight.get("total")
    total_html = f"¥{total}" if total is not None else "—"
    direct = flight.get("direct")
    codeshare = bool(flight.get("codeshare"))
    option_key = flight.get("optionKey", "")
    rank = flight.get("rank", idx + 1)
    price_val = total if total is not None else 0

    cabins = flight.get("cabins") or []

    tags = []
    if direct:
        tags.append('<span class="tg tg-a">直飞</span>')
    else:
        tags.append('<span class="tg tg-b">中转</span>')
    if flight.get("lcc"):
        tags.append('<span class="tg tg-b">廉价航</span>')
    if action == "inline-cabins" and cabins:
        tags.append('<span class="tg tg-a">精选·舱位已展开</span>')
    if flight.get("recommended"):
        tags.append('<span class="tg tg-a">推荐</span>')
    # v3.19.0：共享航班/大客户价/价格来源/代购 全量标记。
    if flight.get("codeshare"):
        operated = "、".join(flight.get("operatedBy") or [])
        tags.append(f'<span class="tg tg-b">共享·实际承运{_esc(operated)}</span>')
    tags.extend(_channel_tags(flight))
    tags_html = "".join(tags)

    transfer_html = ""
    if any(len(j.get("legs") or []) > 1 for j in journeys):
        # 中转点显示“城市 · 机场 (三字码)”；停留时间单独列出。
        # 城市名取 references/air-intl-city-cache.json（机场码→城市，1932 码），
        # 查不到时退回机场全名。停留时长逐点精确计算：下一段出发 − 上一段到达。
        via_lines = []
        cities = _load_city_names()
        for journey in journeys:
            journey_legs = journey.get("legs") or []
            for i in range(len(journey_legs) - 1):
                prev, nxt = journey_legs[i], journey_legs[i + 1]
                code = str(prev.get("toCode") or nxt.get("fromCode") or "")
                airport = str(prev.get("to") or nxt.get("from") or code)
                city = cities.get(code) or cities.get(str(nxt.get("fromCode") or "")) or ""
                via = f"{city} · {airport}" if city and city not in airport else airport
                stay = ""
                m1, m2 = _DT_RE.match(str(prev.get("arr") or "")), _DT_RE.match(str(nxt.get("dep") or ""))
                if m1 and m2:
                    t1 = datetime(int(m1[1]), int(m1[2]), int(m1[3]), int(m1[4]), int(m1[5]))
                    t2 = datetime(int(m2[1]), int(m2[2]), int(m2[3]), int(m2[4]), int(m2[5]))
                    mins = int((t2 - t1).total_seconds() // 60)
                    if mins > 0:
                        stay = f" · 停留{_dur_text(mins)}"
                cross_mark = ""
                if prev.get("toCode") and nxt.get("fromCode") and prev["toCode"] != nxt["fromCode"]:
                    cross_mark = " · 跨机场"
                via_lines.append(f"转{_esc(via)}{stay}{cross_mark}")
        if via_lines:
            transfer_html = f'<div class="fl-sub"><span>中转{len(via_lines)}次<br>' + "<br>".join(via_lines) + "</span></div>"

    cabins = flight.get("cabins") or []
    # v3.19.0：展开区固定带航段明细（中转方案可看清每段衔接与航站楼）。
    legs_html = ""
    if len(legs) > 1:
        rows = "".join(_static_leg_row(lg) for lg in legs if isinstance(lg, dict))
        legs_html = f'<div class="legs-wrap">{rows}</div>'
    cab_table = ""
    has_expand = False
    has_query = False
    price_id = flight.get("priceId")
    if action == "inline-cabins" and cabins:
        has_expand = True
        if len(cabins) > 0:
            rows = "".join(_static_cabin_row(c) for c in cabins if isinstance(c, dict))
            cab_table = (f'<div class="cab-wrap"><table class="cab-table">'
                        '<thead><tr><th style="text-align:left">舱位/等级</th>'
                        '<th style="text-align:left">退改</th>'
                        '<th style="text-align:right">合计(含税) / 费用拆分</th>'
                        '<th style="text-align:right">去下单</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>')
        else:
            cab_table = '<div class="cab-wrap"><div class="nocab">该运价无舱位明细（航司接口偶发空舱位）</div></div>'
    elif action == "inline-cabins" and price_id and serial_number:
        # 渲染时无舱位（非精选航班）：「查舱位」按钮——点击页内 fetch busi intlShop（infoCode）
        # 原地渲染舱位表；直调不可用时只显示原因+重试（无复制降级，详见页面顶部说明）。
        has_query = True
        cab_table = f'<div class="cab-wrap-query" id="cwq{idx}"></div>'
    elif action == "select-cabin":
        order_url = flight.get("orderUrl", "")
        if order_url:
            cab_table = f'<div class="cab-wrap" style="padding:12px;text-align:right"><a class="btn-book" href="{_esc(order_url)}" target="_blank" rel="noopener">去下单</a></div>'
            has_expand = True

    # 价格区：合计大字 + 价格属性（特殊价/大客户协议价/含税）+ 费用拆分小字。
    cap_text = "含税总价"
    if flight.get("specialRate"):
        cap_text = "特殊协议价 · 含税"
    elif flight.get("agreement") or flight.get("bigCustomerPrice"):
        cap_text = "大客户协议价 · 含税"
    if action == "inline-cabins" and cabins:
        cap_text += f" · {len(cabins)}个舱位"
    fee = _fee_breakdown(flight.get("tax"), flight.get("servicePrice"))
    fee_html = f'<div class="fl-px">{_esc(fee)}</div>' if fee else ""

    more_btn = ""
    if has_expand:
        more_btn = '<span class="more-btn"><span class="mo">更多</span><span class="mc">收起</span></span>'
    elif has_query:
        more_btn = (f'<button class="btn-query-cab" type="button" '
                    f'data-serial="{_esc(serial_number)}" data-price-id="{_esc(price_id)}">查舱位</button>')

    # data-* 给无 payload 的 JS 筛选/排序用；不把授权码、serialNumber 写进属性。
    # 单程、多程、往返统一使用“时间线行”，只改变左侧标识文案。
    journey_rows = []
    cities = _load_city_names()
    is_roundtrip = False
    if len(journeys) == 2:
        first_journey, second_journey = journeys
        first_legs = first_journey.get("legs") or []
        second_legs = second_journey.get("legs") or []
        is_roundtrip = bool(
            first_legs and second_legs
            and (first_journey.get("fromCode") or first_legs[0].get("fromCode"))
                == (second_journey.get("toCode") or second_legs[-1].get("toCode"))
            and (first_journey.get("toCode") or first_legs[-1].get("toCode"))
                == (second_journey.get("fromCode") or second_legs[0].get("fromCode"))
        )
    for journey_index, journey in enumerate(journeys):
        jlegs = journey.get("legs") or []
        if not jlegs:
            continue
        jdep, jday = _hm(journey.get("dep") or jlegs[0].get("dep"))
        jarr, jarr_day = _hm(journey.get("arr") or jlegs[-1].get("arr"))
        jarr_html = _esc(jarr)
        if jday and jarr_day:
            day_diff = (date(*jarr_day) - date(*jday)).days
            if day_diff > 0:
                jarr_html += f"<em class='plus1'>+{day_diff}</em>"
        flight_items = []
        via_items = []
        for leg_index, leg in enumerate(jlegs):
            aircraft_label = leg.get("aircraftName") or leg.get("aircraft") or ""
            if leg.get("aircraftName") and leg.get("aircraft"):
                aircraft_label = f'{leg["aircraftName"]} {leg["aircraft"]}'
            flight_label = " ".join(
                part for part in (
                    leg.get("flightNo", ""),
                    leg.get("airline", ""),
                    aircraft_label,
                ) if part
            )
            if leg.get("operatingFlightNo"):
                flight_label += f' · 实际承运{leg["operatingFlightNo"]}'
            flight_items.append(f'<span class="journey-flight">{_esc(flight_label)}</span>')
            if leg_index < len(jlegs) - 1:
                next_leg = jlegs[leg_index + 1]
                code = str(leg.get("toCode") or next_leg.get("fromCode") or "")
                airport = str(leg.get("to") or next_leg.get("from") or code)
                city = cities.get(code) or cities.get(str(next_leg.get("fromCode") or "")) or ""
                via = f"{city} · {airport}" if city and city not in airport else airport
                stay = ""
                m1 = _DT_RE.match(str(leg.get("arr") or ""))
                m2 = _DT_RE.match(str(next_leg.get("dep") or ""))
                if m1 and m2:
                    t1 = datetime(int(m1[1]), int(m1[2]), int(m1[3]), int(m1[4]), int(m1[5]))
                    t2 = datetime(int(m2[1]), int(m2[2]), int(m2[3]), int(m2[4]), int(m2[5]))
                    mins = int((t2 - t1).total_seconds() // 60)
                    if mins > 0:
                        stay = f" · 停留{_dur_text(mins)}"
                via_items.append(f"经{via}{stay}")
        stop_count = int(journey.get("stops") or max(len(jlegs) - 1, 0))
        transfer_label = "直飞" if stop_count == 0 else f"中转{stop_count}次"
        if via_items:
            transfer_label += " · " + "；".join(via_items)
        if is_roundtrip:
            direction = "去" if journey_index == 0 else "返"
        elif len(journeys) > 1:
            direction = str(journey_index + 1)
        else:
            direction = ""
        dir_class = "journey-dir journey-dir-empty" if not direction else "journey-dir"
        dep_airport = jlegs[0].get("from") or journey.get("from") or "--"
        arr_airport = jlegs[-1].get("to") or journey.get("to") or "--"
        flight_detail = " · ".join(flight_items)
        journey_rows.append(
            f'<div class="journey-row">'
            f'<span class="{dir_class}">{_esc(direction)}</span>'
            f'<div class="journey-endpoint journey-depart">'
            f'<span class="journey-date">{_esc(jday and f"{jday[1]:02d}-{jday[2]:02d}" or "")}</span>'
            f'<strong>{_esc(jdep)}</strong><span>{_esc(dep_airport)}</span></div>'
            f'<div class="journey-middle">'
            f'<span class="journey-dur">◷ {_esc(_dur_text(journey.get("flightDurationMin")))}</span>'
            f'<span class="journey-arrow"></span>'
            f'<span class="journey-route">{_esc(dep_airport)} → {_esc(arr_airport)}</span>'
            f'<span class="journey-flights">{flight_detail}</span>'
            f'<span class="journey-transfer">{_esc(transfer_label)}</span></div>'
            f'<div class="journey-endpoint journey-arrive">'
            f'<span class="journey-date">{_esc(jarr_day and f"{jarr_day[1]:02d}-{jarr_day[2]:02d}" or "")}</span>'
            f'<strong>{jarr_html}</strong><span>{_esc(arr_airport)}</span></div></div>'
        )
    time_html = '<div class="journey-list">' + "".join(journey_rows) + "</div>"
    card_kind = "card journey-card"
    card = (f'<details class="{card_kind}" id="card{idx}" '
            f'data-no="{_esc(flight_no)}" data-air="{_esc(airline)}" '
            f'data-direct="{str(direct).lower()}" data-cs="{str(codeshare).lower()}" data-price="{price_val}" '
            f'data-dur="{dur_val}" data-rank="{rank}">'
            '<summary class="card-head">'
            f'<div class="fl-time">{time_html}</div>'
            f'<div class="fl-info"><span class="fl-no">{_esc(flight_no)}</span>'
            f'<div class="fl-air">{_esc(airline)}</div>'
            f'<div class="fl-sub"><span>{_esc(aircraft)}</span></div>'
            f'{transfer_html}<div class="tags">{tags_html}</div></div>'
            f'<div class="fl-price"><div class="lp">{total_html}</div><div class="cap">{_esc(cap_text)}</div>{fee_html}</div>'
            f'{more_btn}</summary>{legs_html}{cab_table}</details>')
    return card


# == CSS（feihe-travel 风格：浅色背景、白色卡片、圆角、蓝色主色、红色价格）==

_CSS = """:root{--bg:#f5f6f8;--card:#ffffff;--line:#e4e7ec;--txt:#1f2329;--txt2:#646a73;--txt3:#8f959e;--blue:#185FA5;--red:#d93025;--green:#0f6e56;--greenbg:#e1f5ee;--bluebg:#e6f1fb;--book:#1a6fda;--bookb:#0d4f9e;--bookc:#e3eefb}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--txt);font-size:13px;line-height:1.6}
.wrap{max-width:1100px;margin:0 auto;padding:20px 16px 90px}
header h1{font-size:19px;font-weight:600}
header .sub{color:var(--txt2);font-size:12.5px;margin-top:2px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.kpi .v{font-size:20px;font-weight:600;line-height:1.3}
.kpi .l{font-size:12px;color:var(--txt2)}
.kpi .v em{font-style:normal;font-size:12px;color:var(--txt3);font-weight:400;margin-left:4px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:12px;position:sticky;top:8px;z-index:5}
.toolbar select,.toolbar input{font-size:12.5px;padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--txt);outline:none}
.cnt{margin-left:auto;font-size:12px;color:var(--txt2);white-space:nowrap}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;margin-bottom:10px;overflow:hidden}
.card-head{display:flex;align-items:center;gap:14px;padding:12px 14px;cursor:pointer;flex-wrap:wrap}
summary.card-head{list-style:none}
summary.card-head::-webkit-details-marker{display:none}
.card-head:hover{background:#fafbfc}
.fl-info{flex:1 1 0;min-width:0;padding-left:4px}
.fl-no{font-size:15px;font-weight:600}
.fl-air{font-size:11.5px;color:var(--txt2);margin-top:-2px}
.fl-sub{font-size:11.5px;color:var(--txt3);margin-top:2px;display:flex;gap:8px;flex-wrap:wrap}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:4px}
.tg{display:inline-block;border-radius:4px;padding:0 6px;font-size:11px;line-height:18px}
.tg-a{background:var(--greenbg);color:var(--green)}
.tg-b{background:var(--bluebg);color:var(--blue)}
.tg-c{background:#fde8e4;color:#c5221f}
.tg-d{background:#f3e8fd;color:#7c3aed}
.cab-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:3px}
.fl-px,.cab-px{font-size:11px;color:var(--txt3);line-height:1.5}
.fl-px{margin-top:1px}
.fl-time{display:flex;align-items:center;gap:10px;font-weight:500;min-width:0;max-width:100%;overflow:hidden;flex:0 1 350px}
.fl-time .big{font-size:16px;flex:1}
.fl-time .big.dep{text-align:center}
.fl-time .big.arr{text-align:center}
.fl-time .big .plus1{font-style:normal;font-size:11px;color:var(--txt3);margin-left:2px}
.fl-time .mid{font-size:11px;color:var(--txt3);text-align:center;font-weight:400;flex:none;line-height:1.5}
.fl-time .rt-line{font-size:12px;color:var(--txt2);font-weight:400;white-space:nowrap}
.journey-list{width:100%;display:flex;flex-direction:column;gap:5px}
.journey-card .card-head{display:grid;grid-template-columns:minmax(560px,1fr) minmax(130px,180px) auto;align-items:stretch;gap:24px;padding:0 18px 0 0}
.journey-card .fl-time{width:auto;max-width:none;flex:1 1 auto;overflow:visible;padding:18px 0 18px 14px}
.journey-card .fl-info{display:none}
.journey-card .fl-price{border-left:1px solid var(--line);padding:26px 0 18px 22px;align-self:stretch;display:flex;flex-direction:column;justify-content:center}
.journey-card .more-btn,.journey-card .btn-query-cab{align-self:center}
.roundtrip-list{width:auto;max-width:none;gap:7px}
.journey-row{display:grid;grid-template-columns:30px minmax(70px,92px) minmax(150px,1fr) minmax(86px,105px);align-items:center;gap:13px;font-size:12px;min-width:0;padding:10px 0;border-bottom:1px solid #edf0f4;position:relative}
.journey-row:last-child{border-bottom:0}
.journey-dir{position:relative;width:26px;height:26px;padding:2px 0;border:1px solid var(--book);border-radius:50%;background:#fff;color:var(--book);font-size:12px;line-height:20px;text-align:center;z-index:1}
.journey-dir-empty{visibility:hidden}
.journey-row:not(:last-child):after{content:"";position:absolute;left:13px;top:50%;height:calc(50% + 28px);border-left:1px dashed #7aaaf0;z-index:0}
.journey-row:nth-child(2) .journey-dir{border-color:var(--book);background:var(--book);color:#fff}
.journey-body{display:none}
.journey-endpoint{display:flex;flex-direction:column;min-width:0}
.journey-endpoint strong{font-size:25px;line-height:1.05;color:#253b66;font-weight:700;letter-spacing:0}
.journey-endpoint span:last-child{color:var(--txt2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}
.journey-date{color:var(--txt3);white-space:nowrap;font-size:11px}
.journey-arrive{text-align:right}
.journey-middle{display:flex;flex-direction:column;align-items:center;min-width:0;color:var(--txt3)}
.journey-dur{font-size:11px;white-space:nowrap}
.journey-arrow{position:relative;width:100%;height:12px;margin:1px 0 2px;border-top:1px solid #aeb7c5}
.journey-arrow:after{content:"";position:absolute;right:0;top:-4px;border-width:3px 0 3px 6px;border-style:solid;border-color:transparent transparent transparent #8d98a8}
.journey-route{max-width:100%;color:var(--txt2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px}
.journey-flights{max-width:100%;color:var(--txt2);white-space:normal;text-align:center;overflow-wrap:anywhere;line-height:1.4}
.journey-transfer{max-width:100%;color:var(--txt3);font-size:11px;white-space:normal;text-align:center;overflow-wrap:anywhere;line-height:1.4}
.fl-price{text-align:right;min-width:86px;margin-left:auto}
.fl-price .lp{font-size:17px;font-weight:600;color:var(--red)}
.fl-price .cap{font-size:11px;color:var(--txt3)}
.more-btn{flex:none;border:1px solid var(--blue);color:var(--blue);background:#fff;border-radius:999px;padding:5px 14px;font-size:12.5px;cursor:pointer;font-weight:500}
.more-btn:hover{background:var(--bluebg)}
.more-btn .mc{display:none}
details[open] .more-btn{background:var(--blue);color:#fff}
details[open] .more-btn .mo{display:none}
details[open] .more-btn .mc{display:inline}
.btn-query-cab{flex:none;border:1px solid var(--book);color:var(--book);background:#fff;border-radius:999px;padding:5px 14px;font-size:12.5px;cursor:pointer;font-weight:500;font-family:inherit}
.btn-query-cab:hover{background:var(--bookc)}
.btn-query-cab[disabled]{opacity:.6;cursor:default}
.cab-wrap-query{padding:10px 12px}
.cab-cmd{padding:10px 12px;background:#f8fafd;border:1px dashed var(--line);border-radius:8px}
.cab-cmd-t{font-size:12px;color:var(--txt2);margin-bottom:6px}
.cab-dim{color:var(--txt3);font-size:12px}
.cab-wrap{border-top:1px dashed var(--line)}
.legs-wrap{border-top:1px dashed var(--line);padding:8px 14px;display:flex;flex-direction:column;gap:6px}
.leg-row{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--txt2);flex-wrap:wrap}
.leg-row .leg-no{font-weight:600;color:var(--txt);min-width:56px}
.leg-row .leg-air{min-width:64px}
.leg-row .leg-t{font-weight:500;color:var(--txt);white-space:nowrap}
.leg-row .leg-t .plus1{font-style:normal;font-size:11px;color:var(--txt3)}
.leg-row .leg-ap{white-space:nowrap}
.leg-row .leg-dur,.leg-row .leg-ac{color:var(--txt3)}
.cab-table{width:100%;border-collapse:collapse}
.cab-table th{font-size:11.5px;color:var(--txt3);font-weight:400;text-align:right;padding:7px 12px;background:#fafbfc;border-bottom:1px solid var(--line)}
.cab-table th:first-child,.cab-table td:first-child{text-align:left}
.cab-table td{font-size:12.5px;padding:8px 12px;border-bottom:0.5px solid var(--line);vertical-align:middle}
.cab-table tr:last-child td{border-bottom:none}
.cab-code{font-weight:600;white-space:nowrap}
.cab-name{color:var(--txt2);font-size:11.5px;white-space:nowrap}
.price-n{font-weight:600}
.prcell{text-align:right;line-height:1.45}
.btn-book{display:inline-block;border:none;background:var(--book);color:#fff;border-radius:999px;padding:5px 16px;font-size:12.5px;cursor:pointer;font-weight:500;user-select:none;text-decoration:none}
.btn-book:hover{background:var(--bookb)}
.nocab{color:var(--txt3);font-size:12px;padding:9px 12px;background:#fbfcfd;border:1px dashed var(--line);border-radius:8px}
.empty{text-align:center;color:var(--txt3);padding:40px 0;display:none}
.note{color:var(--txt3);font-size:11.5px;margin-top:12px;text-align:center}
@media(max-width:900px){.journey-card .card-head{grid-template-columns:minmax(440px,1fr) 130px auto;gap:15px}.journey-card .fl-price{padding-left:15px}.journey-row{grid-template-columns:28px 78px minmax(120px,1fr) 78px;gap:9px}}
@media(max-width:760px){.fl-time{width:100%;flex-basis:100%}.journey-card .card-head{display:flex;flex-direction:column;align-items:stretch;gap:0;padding:0 14px 12px}.journey-card .fl-time{padding:10px 0 6px}.journey-card .fl-price{border-left:0;border-top:1px solid var(--line);padding:10px 0 0;flex-direction:row;align-items:baseline;gap:8px;text-align:left}.journey-card .more-btn,.journey-card .btn-query-cab{align-self:flex-start;margin-top:10px}.card-head{align-items:flex-start}.fl-price{margin-left:0}.journey-row{grid-template-columns:26px minmax(64px,78px) minmax(90px,1fr) minmax(64px,78px);gap:7px;padding:8px 0}.journey-endpoint strong{font-size:20px}.journey-route{display:none}.journey-flights{font-size:11px}}
"""


# == JS（渐进增强：筛选/排序/搜索，用 data 属性显示隐藏，无 JS 也能看首屏）==

_JS = """(function(){
var state={kw:"",route:"",air:"",cs:"",sort:"rank"};
function filterCards(){
var kw=state.kw.toLowerCase(),route=state.route,air=state.air,cs=state.cs;
var cards=document.querySelectorAll('.card');
var shown=0;
cards.forEach(function(c){
var hay=(c.getAttribute('data-no')||'')+' '+(c.getAttribute('data-air')||'');
hay=hay.toLowerCase();
var direct=c.getAttribute('data-direct')==='true';
var cAir=c.getAttribute('data-air');
var cCs=c.getAttribute('data-cs')==='true';
var show=(!kw||hay.indexOf(kw)>=0)&&(!route||(route==='direct')===direct)&&(!air||cAir===air)
  &&(!cs||(cs==='cs')===cCs);
c.style.display=show?'':'none';
if(show)shown++;
});
var cnt=document.getElementById('cnt');
if(cnt)cnt.textContent='共 '+shown+' / '+cards.length+' 个方案';
var empty=document.getElementById('empty');
if(empty)empty.style.display=shown?'none':'block';
}
function sortCards(){
var list=document.getElementById('list');
if(!list)return;
var cards=Array.prototype.slice.call(list.querySelectorAll('.card'));
var sort=state.sort;
cards.sort(function(a,b){
if(sort==='dur')return (+a.getAttribute('data-dur'))-(+b.getAttribute('data-dur'));
if(sort==='rank')return (+a.getAttribute('data-rank'))-(+b.getAttribute('data-rank'));
return (+a.getAttribute('data-price'))-(+b.getAttribute('data-price'));
});
cards.forEach(function(c){list.appendChild(c)});
}
var fKw=document.getElementById('fKw'),fRoute=document.getElementById('fRoute'),fAir=document.getElementById('fAir'),fCs=document.getElementById('fCs'),fSort=document.getElementById('fSort');
if(fKw)fKw.addEventListener('input',function(){state.kw=this.value;filterCards()});
if(fRoute)fRoute.addEventListener('change',function(){state.route=this.value;filterCards()});
if(fAir)fAir.addEventListener('change',function(){state.air=this.value;filterCards()});
if(fCs)fCs.addEventListener('change',function(){state.cs=this.value;filterCards()});
if(fSort)fSort.addEventListener('change',function(){state.sort=this.value;sortCards()});
filterCards();
})();

(function(){
// 无舱位航班：「查舱位」= 页内直调 intlShop（infoCode 换登录态，只读），
// 查到舱位原地渲染舱位表 + 每舱位一个免登「去下单」链接——零 server、零复制。
// 直调不可用（infoCode 过期 / 网络断）时显示原因并允许重试（不提供任何复制指令降级）。
function esc(s){return (''+(s==null?'':s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function escAttr(s){return esc(s).replace(/\"/g,'&quot;');}
var CFG=__PAGE_CFG__,CABIN_CACHE={};
var CABIN_CLASS={Y:'经济舱',C:'商务舱',F:'头等舱',J:'超级经济舱',W:'高端经济舱'};

function qAll(s){return encodeURIComponent(s);}
function qFlightList(s){return encodeURIComponent(s).replace(/%2C/g,',').replace(/%2F/g,'/');}
// 复刻 air_intl_build_order_jump_url.build_order_route + sso_forward.build_forward_url
function buildOrderUrl(serial,cabinPriceId){
  var fl=qFlightList(JSON.stringify([{serialNumber:serial,priceId:cabinPriceId}]));
  var route='/VuePage/international/index.html#/bookingPricing?flightList='+fl
    +'&flyType='+CFG.order.flyType+'&adultCount='+CFG.order.adult
    +'&payType='+CFG.order.payType+'&agent='+CFG.order.agent;
  return buildForwardUrl(route);
}
function buildForwardUrl(route){
  var base=(CFG&&CFG.forwardBase)?CFG.forwardBase:((CFG&&CFG.host)?('https://'+CFG.host+'/api/portal/mcp/oauth2/forward'):'');
  if(!base||!CFG||!CFG.forwardCode)return "";
  return base+'?redirectPage='+qAll(route)+'&authCode='+qAll(CFG.forwardCode);
}
/* v3.19.3：busi 直调响应外层包一层 data（{errorCode,data:{ok,allCab}}），
   早期实现从顶层取 allCab 恒为 undefined → 误报「舱位不足」。统一在此解壳。 */
function unwrapBusi(data){
  if(!data||typeof data!=='object')return data;
  return (data.allCab!=null||data.ok!=null||data.groupList!=null)?data:(data.data||data);
}
/* 页内直调：GET intlShop（请求头 X-Auth-Code: infoCode）。type=allCab 与 intl_shopping_all_cab 业务同构。 */
function shopCall(args){
  if(!CFG.intlShopUrl||!CFG.infoCode)return Promise.reject(new Error('no-infoCode'));
  var q='type=allCab'
    +'&serialNumber='+encodeURIComponent(args.serialNumber)
    +'&priceId='+encodeURIComponent(args.priceId);
  if(args.internal!=null)q+='&internal='+(args.internal?'true':'false');
  return fetch(CFG.intlShopUrl+'?'+q,{method:'GET',
      headers:{'Accept':'application/json','X-Auth-Code':CFG.infoCode}})
    .then(function(r){
      return r.text().then(function(text){
        var raw=null;
        try{raw=JSON.parse(text);}catch(e){throw new Error('HTTP '+r.status+'（非 JSON 响应）');}
        var data=unwrapBusi(raw);
        if(!r.ok||(data&&data.ok===false)){
          throw new Error((data&&data.message)||(raw&&raw.errorMsg)||('HTTP '+r.status));
        }
        return (data&&data.allCab)||null;
      });
    });
}
function parseCabins(data){
  // 兼容调用方传入已解壳或未解壳的对象。
  data=unwrapBusi(data);
  var g=data&&data.groupList&&data.groupList[0];
  if(!g)return [];
  return (g.priceList||[]).map(function(p){
    var t=(p.tripList&&p.tripList[0])||{},cab=(t.cabList&&t.cabList[0])||{},rule=t.rule||{};
    var cc=(cab.cabClass||'').toUpperCase(),fb=cab.cab||'';
    var name=CABIN_CLASS[cc]||cab.cabClass||'舱位';
    // v3.19.0：费用字段随舱位返回（tax/addPrice/servicePrice；v6.0.3 起仅税/服务费上页面）；
    // v3.19.1：特殊价限制规则（ruleList.ruleDesc，如 允许国籍：中国(CN)）。
    var rules=(p.ruleList||[]).map(function(r){return (r&&r.ruleDesc)||'';}).filter(function(s){return s;});
    return {priceId:p.priceId,total:p.totalPrice,label:fb?name+'（'+fb+'）':name,
      fare:p.price,tax:p.tax,addPrice:p.addPrice,servicePrice:p.servicePrice,
      allowTicket:p.allowTicket!==false,
      bigCustomer:p.customersId||'',selfBig:!!p.selfBigCustomersId,bigCustomerPrice:p.bigCustomerPrice===true,specialRate:p.specialRate,
      priceRules:rules,
      refundable:!!rule.refund,changeable:!!rule.change,recommend:!!p.recommend};
  });
}
function feeText(c){
  // v6.0.3 口径：费用拆分只显示税与服务费；票价并入含税总价，附加费一律不展示。
  var parts=[];
  if(c.tax!=null&&c.tax!=='')parts.push('税¥'+c.tax);
  if(+c.servicePrice>0)parts.push('服务费¥'+c.servicePrice);
  return parts.join(' · ');
}
function ruleLabel(desc){
  // 「允许国籍：中国(CN)」→「限中国大陆乘客预订」
  var m=/^允许国籍[：:]\\s*(.+?)(?:\\(([A-Z]{2})\\))?\\s*$/.exec(desc||'');
  if(m){var n=m[1];if(n==='中国'||n==='CN')n='中国大陆';return '限'+n+'乘客预订';}
  return desc||'';
}
function chanTags(c){
  // v3.19.1 口径：特殊价（有特殊规则的协议价）/ 大客户协议价（大客户号价）。
  // 渠道来源与代购标记不在页面展示。
  var t=[];
  if(c.specialRate){
    t.push('<span class="tg tg-d">特殊价</span>');
    (c.priceRules||[]).forEach(function(r){
      var l=ruleLabel(r);if(l)t.push('<span class="tg tg-c">'+esc(l)+'</span>');
    });
  }else if(c.bigCustomer||c.selfBig||c.bigCustomerPrice){
    t.push('<span class="tg tg-d">大客户协议价</span>');
  }
  return t.join('');
}
function cabinRow(c,serial){
  var url=buildOrderUrl(serial,c.priceId);
  var btn=url?'<a class="btn-book" href=\"'+escAttr(url)+'\" target=\"_blank\" rel=\"noopener\">去下单</a>':'<span class=\"cab-dim\">无链接</span>';
  var tags=(c.recommend?'<span class=\"tg tg-a\">推荐</span>':'')+chanTags(c);
  var refund=(c.refundable?'可退':'不可退')+'/'+(c.changeable?'可改':'不可改');
  var fee=feeText(c);
  return '<tr><td><span class=\"cab-code\">'+esc(c.label)+'</span>'+(tags?'<div class=\"cab-tags\">'+tags+'</div>':'')+'</td>'
    +'<td><span class=\"cab-name\">'+esc(refund)+'</span></td>'
    +'<td class=\"prcell\"><span class=\"price-n\">¥'+esc(c.total)+'</span>'+(fee?'<div class=\"cab-px\">'+esc(fee)+'</div>':'')+'</td>'
    +'<td style=\"text-align:right\">'+btn+'</td></tr>';
}
function fallbackBox(wrap,serial,priceId,reason){
  // v3.2.0 起按用户要求移除一切「复制指令」降级：直调不可用时只显示原因，不进剪贴板。
  wrap.innerHTML=(reason?'<div class=\"nocab\" style=\"margin-bottom:6px\">'+reason+'</div>':'')
    +'<div class=\"cab-cmd\"><div class=\"cab-cmd-t\">页内直调暂不可用（具体原因见上方），排除后点上方按钮重试</div></div>';
}
/* 直调失败分层诊断——预览沙箱 CSP 拦截 / infoCode 过期 / 网络 */
function diagError(msg){
  if(msg==='no-infoCode'||msg==='no-config')return '本页未内嵌直调授权码（infoCode 缺失）：重新生成页面即可';
  if(/Failed to fetch|NetworkError|Load failed/i.test(msg)){
    var h=location.hostname||'';
    if(location.protocol==='http:'&&(h==='127.0.0.1'||h==='localhost'||h==='0.0.0.0'))
      return '请求被预览面板沙箱拦截：预览环境的 CSP 不允许页面外联 '+CFG.host+'（浏览器层面直接拒绝，与服务端无关）。请用外部浏览器（Chrome/Edge）打开本页文件后再点此按钮';
    return '网络请求失败（'+msg+'）：检查本机网络/代理后重试';
  }
  if(/HTTP 401/.test(msg))return 'infoCode 已过期（页面内嵌的是生成时刻的短时效授权码）：重新查询生成新页面即可';
  return '直调失败（'+msg+'）';
}
document.addEventListener('click',function(e){
  var btn=e.target.closest?e.target.closest('.btn-query-cab'):null;
  if(!btn||btn.dataset.busy)return;
  var card=btn.closest('details.card');
  var wrap=card?card.querySelector('.cab-wrap-query'):null;
  var serial=btn.getAttribute('data-serial'),priceId=btn.getAttribute('data-price-id');
  if(!serial||!priceId||!wrap)return;
  /* v3.19.2：三态「查舱位」按钮——查到舱位后在 收起舱位/展开舱位 间切换，
     结果缓存于 CABIN_CACHE 不重复调 MCP；preventDefault 拦下 summary 的
     details 默认 toggle，卡片展开/舱位显隐由本逻辑统一管理。 */
  var st=btn.dataset.cabState||'';
  if(st==='open'||st==='closed'){
    e.preventDefault();
    if(st==='open'){
      wrap.innerHTML='';
      btn.dataset.cabState='closed';btn.textContent='展开舱位';
    }else{
      if(card)card.open=true;
      wrap.innerHTML=CABIN_CACHE[card.id]||'';
      btn.dataset.cabState='open';btn.textContent='收起舱位';
    }
    return;
  }
  btn.dataset.busy='1';btn.textContent='查询中…';
  if(card)card.open=true;
  shopCall({serialNumber:serial,priceId:priceId,internal:false}).then(function(data){
    var cabins=parseCabins(data);
    if(cabins.length){
      var html='<div class=\"cab-wrap\"><table class=\"cab-table\">'
        +'<thead><tr><th style=\"text-align:left\">舱位/等级</th><th style=\"text-align:left\">退改</th>'
        +'<th style=\"text-align:right\">合计(含税) / 费用拆分</th><th style=\"text-align:right\">去下单</th></tr></thead>'
        +'<tbody>'+cabins.map(function(c){return cabinRow(c,serial);}).join('')+'</tbody></table></div>';
      CABIN_CACHE[card.id]=html;
      wrap.innerHTML=html;
      btn.textContent='收起舱位';btn.dataset.cabState='open';btn.dataset.busy='';
    }else{
      wrap.innerHTML='<div class=\"nocab\">本次该航班无返回可售舱位（如确有余票，点「重新查询」换新会话）</div>';
      btn.dataset.busy='';btn.textContent='重新查询';
    }
  }).catch(function(err){
    var msg=(err&&err.message)||String(err);
    fallbackBox(wrap,serial,priceId,esc(diagError(msg)));
    btn.dataset.busy='';btn.textContent='重试';
  });
});
// 供自动化测试钩子（Node 验证脚本复用同一份实现，不参与交互）
window.__CABIN_JS__={buildOrderUrl:buildOrderUrl,parseCabins:parseCabins,shopCall:shopCall};
})();
"""


def render_html(model: dict[str, Any], action: str = "select-flight", serial_number: str = "",
                page_cfg: dict[str, Any] | None = None) -> str:
    """生成静态预渲染 HTML（feihe-travel 风格：无 JS 也能看首屏，零 server）。"""
    flights = model.get("flights") or []
    title = model.get("title", "国际航班方案")
    meta_parts = model.get("queryMeta") or []
    summary = model.get("summary", "")
    # v3.19.0：serialNumber 是会话内部标识，不上页面（用户反馈属无关信息）；
    # 顶部操作说明 banner 同样移除——页面按钮文案本身已自解释。
    summary = re.sub(r"\s*·?\s*serialNumber=\S+", "", summary).strip(" ·")
    meta = " · ".join(meta_parts)
    if summary:
        meta = (meta + " · " + summary) if meta else summary

    kpis_html = _static_kpis(flights)
    air_opts_html = _static_air_opts(flights)
    list_html = "".join(_static_flight_card(f, i, action, serial_number) for i, f in enumerate(flights))
    cnt_html = f"共 {len(flights)} 个方案"
    # v3.2.0：复制指令模板已移除（无 TMPL 锚点），js 直接取 _JS。
    js = _JS
    # 直调配置：缺 intlShopUrl/infoCode 时 JS 侧 no-infoCode 直接走降级，不发起任何请求。
    js = js.replace("__PAGE_CFG__", json.dumps(page_cfg or {}, ensure_ascii=False))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)}</title>
<style>
{_CSS}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>{_esc(title)}</h1>
<div class="sub">{_esc(meta)}</div>
</header>
<div class="kpis" id="kpis">{kpis_html}</div>
<div class="toolbar">
<input id="fKw" placeholder="航班号/航司" style="width:130px">
<select id="fRoute"><option value="">全部方案</option><option value="direct">仅直飞</option><option value="transfer">中转/经停</option></select>
<select id="fCs"><option value="">共享/非共享</option><option value="cs">仅共享航班</option><option value="own">仅非共享（自营）</option></select>
<select id="fAir">{air_opts_html}</select>
<select id="fSort"><option value="rank">推荐排序</option><option value="price">价格最低</option><option value="dur">时长最短</option></select>
<span class="cnt" id="cnt">{cnt_html}</span>
</div>
<div id="list">{list_html}</div>
<div class="empty" id="empty">没有符合条件的航班</div>
<div class="note">价格均含税，费用拆分见各卡片 · 「去下单」直接进飞鹤下单页（已免登） · 特殊价有预订限制（如限国籍），以标识为准 · 授权码短时效，链接过期重新查询生成即可</div>
</div>
<script>
{js}
</script>
</body>
</html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized JSON from air_intl_parse_shopping.py")
    parser.add_argument("--output", type=Path, help="HTML output path")
    parser.add_argument("--map-output", type=Path, help="selection map output path")
    parser.add_argument("--title", default="国际航班方案", help="display-only query title")
    parser.add_argument("--meta", action="append", default=[], help="display-only query fact; repeat as needed")
    parser.add_argument("--generation", help="结果世代 id；省略则随机")
    parser.add_argument(
        "--action", default="select-flight",
        choices=["select-flight", "select-cabin", "inline-cabins"],
        help="select-flight=仅展示；select-cabin=舱位页（每舱位一去下单链接）；inline-cabins=航班页内联舱位",
    )
    parser.add_argument("--cabins", type=Path, help="inline-cabins 模式：cabins_by_option.json（key=optionKey → 舱位数组）")
    parser.add_argument("--cabins-out-dir", dest="cabins_out_dir", type=Path,
                        help="兼容旧旗标，已忽略（查舱位改页内 busi intlShop）")
    parser.add_argument("--info-code", dest="info_code", default="",
                        help="infoCode（当次 intl_shopping 下发；页内直调 intlShop。缺省读 parsed.json）")
    parser.add_argument("--forward-code", dest="forward_code", default="",
                        help="forwardCode（当次 intl_shopping 下发；forward 免登跳转。缺省读 parsed.json）")
    parser.add_argument("--portal-host", dest="portal_host",
                        default=(portal_host() if callable(portal_host) else ORDER_DEFAULTS["portal_host"]))
    parser.add_argument("--adult", default=ORDER_DEFAULTS["adult"])
    parser.add_argument("--pay-type", dest="pay_type", default=ORDER_DEFAULTS["pay_type"], help="1=公费，0=自费")
    parser.add_argument("--fly-type", dest="fly_type", default=ORDER_DEFAULTS["fly_type"], help="1=单程，2=往返，3=多程")
    parser.add_argument("--agent", default=ORDER_DEFAULTS["agent"])
    args = parser.parse_args()

    # 授权码来源：优先命令行，其次 parsed.json（air_intl_parse_shopping 从当次 shopping 最外层写入）。
    # 没有授权码时 select-flight 仍可纯展示；带舱位/下单的 action 硬失败——死页面不如不出页。
    data = json.loads(args.input.read_text(encoding="utf-8"))
    info_code = args.info_code or str(data.get("infoCode") or "")
    forward_code = args.forward_code or str(data.get("forwardCode") or "")
    if (not info_code or not forward_code) and args.action != "select-flight":
        print(
            "ERROR: 缺少授权码拒绝渲染（去下单 forward 会白页、查舱位按钮 no-infoCode）。\n"
            "  处理：① 重新执行当次 intl_shopping 查询（授权码随响应最外层下发，30 分钟有效）；\n"
            "  ② 显式传 --info-code/--forward-code；③ 仅展示不下单时用 --action select-flight。",
            file=sys.stderr,
        )
        raise SystemExit(3)

    records = data.get("flights")
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("输入缺少 flights[]；请先运行 air_intl_parse_shopping.py")
    if not records:
        raise ValueError("flights[] 为空，不生成伪造的航班页面")

    output = args.output or args.input.with_name(f"{args.input.stem}_航班方案.html")
    map_output = args.map_output or output.with_suffix(".selection-map.json")
    generation = args.generation or secrets.token_hex(6)
    # generation 把 HTML 和 selection-map 对上号，避免 agent 拿错另一次查询的 map。
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    serial_number = data.get("serialNumber")
    order_params = {
        "adult": args.adult, "pay_type": args.pay_type, "fly_type": args.fly_type,
        "agent": args.agent, "portal_host": args.portal_host,
    }

    cabins_by_option: dict[str, list[dict[str, Any]]] = {}
    if args.cabins:
        cb = json.loads(args.cabins.read_text(encoding="utf-8"))
        if isinstance(cb, dict):
            for k, v in cb.items():
                if isinstance(v, list):
                    cabins_by_option[k] = v

    public_rows: list[dict[str, Any]] = []
    mapping: dict[str, Any] = {}
    for index, record in enumerate(records, 1):
        key = f"F{index:03d}"
        # 必须和 air_intl_book inline / parsed 列表下标一致，对不上舱位贴不到航班上。
        pub = _public_record(record, key)
        if args.action == "inline-cabins" and cabins_by_option:
            raw_cabins = cabins_by_option.get(key, [])
            pub["cabins"] = [
                _cabin_public(c, serial_number, forward_code, order_params)
                for c in raw_cabins if isinstance(c, dict)
            ]
        if args.action == "select-cabin":
            pub["orderUrl"] = _build_order_url(serial_number, record.get("priceId"), forward_code, order_params)
        public_rows.append(pub)
        selection = _selection_record(record)
        if serial_number is not None:
            selection["serialNumber"] = serial_number
        mapping[key] = selection

    model = {
        "title": args.title,
        "queryMeta": args.meta,
        "summary": _text(data.get("summary")),
        "generation": generation,
        "generatedAt": generated_at,
        "serialNumber": serial_number,
        "action": args.action,
        "flights": public_rows,
    }
    selection_map = {
        "schema": "fh-travel-selection-map/v1",
        "generation": generation,
        "createdAt": generated_at,
        "sourceFile": str(args.input.resolve()),
        "flightCount": len(records),
        "serialNumber": serial_number,
        "infoCode": info_code or None,
        "forwardCode": forward_code or None,
        "options": mapping,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    map_output.parent.mkdir(parents=True, exist_ok=True)
    # 「查舱位」一律页内直调 busi intlShop（infoCode）；v3.2.0 起无复制指令降级，
    # 直调不可用时页面显示原因并允许重试。
    # 直调配置进页面 JS：infoCode/forwardCode 与 forward URL 同源同暴露面（短时效、仅本机本地页）。
    # intlShopUrl/forwardBase 运行时引用 config.json（portal_config），不写死路径。
    _host = order_params["portal_host"] or (portal_host() if callable(portal_host) else "")
    _mcp = mcp_base() if callable(mcp_base) else (f"https://{_host}/api/portal/mcp" if _host else "")
    _shop = (intl_shop_url() if callable(intl_shop_url)
             else (_mcp.rstrip("/") + "/busi/air/intl/intlShop" if _mcp else ""))
    _fwd = forward_base() if callable(forward_base) else (_mcp.rstrip("/") + "/oauth2/forward" if _mcp else "")
    page_cfg = {
        "intlShopUrl": _shop,
        "infoCode": info_code,
        "forwardCode": forward_code,
        "host": _host,
        "forwardBase": _fwd,
        "order": {
            "adult": order_params["adult"], "payType": order_params["pay_type"],
            "flyType": order_params["fly_type"], "agent": order_params["agent"],
        },
    }
    output.write_text(
        render_html(model, args.action, serial_number, page_cfg), encoding="utf-8"
    )
    map_output.write_text(json.dumps(selection_map, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "html": str(output.resolve()),
        "selectionMap": str(map_output.resolve()),
        "generation": generation,
        "flightCount": len(records),
        "action": args.action,
        "cabinsAttached": bool(cabins_by_option),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[错误] {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
