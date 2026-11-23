#!/usr/bin/env python3
"""Normalize an oversized intl_shopping tool result.

Business payload is protocol structuredContent (then raw shopping JSON /
script#flight-data). Never calls MCP; never uses display maps as API inputs.

Usage:
  command-producing-json | python3 scripts/air_intl_parse_shopping.py - --json
  python3 scripts/air_intl_parse_shopping.py - --json --html out.html --dest SIN
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unwrap_content import unwrap_envelope, EnvelopeError  # noqa: E402

from mcp_envelope import decode, peel_candidates


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def load_display_codes(path: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    # 对照表只给人看的中文名。shopping / all_cab 入参必须用缓存或 MCP 返回的 code，禁止用这里的名字反查。
    airlines: dict[str, str] = {}
    airports: dict[str, str] = {}
    # 空舱等和 "--" 都当最低价基础舱展示，不能在卡片上留空白。
    cabins: dict[str, str] = {"": "基础舱", "--": "基础舱"}
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 航司"):
            section = "airline"
            continue
        if line.startswith("## 机场"):
            section = "airport"
            continue
        if line.startswith("## 舱位"):
            section = "cabin"
            continue
        if not line.startswith("|") or "---" in line:
            continue
        values = _cells(line)
        if section in {"airline", "airport"} and len(values) >= 4:
            target = airlines if section == "airline" else airports
            for code, name in ((values[0], values[1]), (values[2], values[3])):
                if re.fullmatch(r"[A-Z0-9]{2,3}", code):
                    target[code] = name
        elif section == "cabin" and len(values) >= 2 and values[0] != "码":
            # 「码」是表头，不是舱等代码。
            for code in re.split(r"\s*/\s*", values[0].replace("空", "")):
                cabins[code] = values[1].replace("（未明确公布舱等的最低价运价）", "")
    return airlines, airports, cabins


def _read_payload(value: str) -> tuple[Any, Path | None]:
    if value == "-":
        return decode(sys.stdin.read()), None
    path = Path(value)
    return decode(path.read_text(encoding="utf-8")), path


def _call_result(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        return payload["result"]
    return payload


def _content_blocks(payload: Any) -> list[dict[str, Any]]:
    value = _call_result(payload)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get("content"), list):
        return [item for item in value["content"] if isinstance(item, dict)]
    return []


def _summary(blocks: list[dict[str, Any]]) -> str:
    for block in blocks:
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            text = block["text"].strip()
            if text and not text.startswith(("{", "[")):
                # 以 { / [ 开头的是套了 JSON 的 content.text，不是给人看的摘要句。
                return text
    return ""


def _structured(payload: Any, blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates: list[Any] = list(peel_candidates(payload))
    for block in blocks:
        candidates.extend(peel_candidates(block))
    for candidate in candidates:
        # 读 structuredContent（unwrap 已处理指引句）；再匹配 groupList。
        candidate = unwrap_envelope(candidate)
        from unwrap_content import _is_structured_pointer, SUCCESS_SUMMARY
        if _is_structured_pointer(candidate) or candidate == SUCCESS_SUMMARY:
            continue
        # 谁带着 groupList 谁才是 intl_shopping 载荷（国内页找的是 flightList）。
        if isinstance(candidate, dict) and isinstance(candidate.get("groupList"), list):
            return candidate
    return None


def _embedded_rows(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 最后才挖 HTML 里的 script#flight-data：那是展示映射，不能当 API 入参。
    patterns = (
        re.compile(r'<script[^>]*id=["\']flight-data["\'][^>]*>(.*?)</script>', re.I | re.S),
        re.compile(r"<script[^>]*>(\[.*?\])</script>", re.I | re.S),
    )
    for block in blocks:
        resource = block.get("resource")
        text = resource.get("text") if isinstance(resource, dict) else None
        if not isinstance(text, str):
            continue
        for pattern in patterns:
            match = pattern.search(text)
            if not match:
                continue
            try:
                rows = json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
            if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
                return rows
    return []


def _serial_from_blocks(blocks: list[dict[str, Any]]) -> str | None:
    for block in blocks:
        resource = block.get("resource")
        if not isinstance(resource, dict):
            continue
        uri = resource.get("uri")
        if isinstance(uri, str) and uri.startswith("flightquery://results/"):
            value = uri.rsplit("/", 1)[-1]
            # latest 是占位不是会话号，拿去 all_cab 会失败。
            return value if value and value != "latest" else None
    return None


def _first(value: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not isinstance(value, dict):
        return default
    for key in keys:
        current = value.get(key)
        if current is not None:
            return current
    return default


def _amount_key(value: Any) -> tuple[int, float]:
    try:
        return 0, float(value)
    except (TypeError, ValueError):
        # 无报价排到最后，min() 不会把 None/空串当成最便宜。
        return 1, 0.0


def _air_prefix(flight_no: str) -> str:
    match = re.match(r"([A-Z0-9]{2})", flight_no or "")
    return match.group(1) if match else ""


def _code_from_label(label: Any) -> str:
    text = str(label or "")
    match = re.search(r"\(([A-Z]{3})\)\s*$", text)
    return match.group(1) if match else (text if re.fullmatch(r"[A-Z]{3}", text) else "")


def _airport_label(code: str, server_names: dict[str, str], fallback: dict[str, str]) -> str:
    name = server_names.get(code) or fallback.get(code)
    return f"{name} ({code})" if name and code else (code or name or "--")


def _journey(legs: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep one shopping trip as one visible journey (outbound/return/multi-city)."""
    transfer = _transfer_meta(legs)
    return {
        "legs": legs,
        "from": legs[0].get("from", "") if legs else "",
        "fromCode": legs[0].get("fromCode", "") if legs else "",
        "to": legs[-1].get("to", "") if legs else "",
        "toCode": legs[-1].get("toCode", "") if legs else "",
        "dep": legs[0].get("dep", "") if legs else "",
        "arr": legs[-1].get("arr", "") if legs else "",
        "flightDurationMin": sum(int(leg.get("dur") or 0) for leg in legs),
        "layoverMin": transfer["layoverMin"],
        "stops": transfer["stops"],
    }


def _journeys_meta(journeys: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate only within-trip transfers; return/multi-city legs are not stopovers."""
    transfer_airports = []
    for journey in journeys:
        for leg in (journey.get("legs") or [])[:-1]:
            code = str(leg.get("toCode") or "").strip()
            if code:
                transfer_airports.append(code)
    return {
        "stops": sum(int(j.get("stops") or 0) for j in journeys),
        "transferAirports": transfer_airports,
        "sameAirport": all(
            _transfer_meta(j.get("legs") or [])["sameAirport"] for j in journeys
        ) if journeys else True,
        "layoverMin": sum(int(j.get("layoverMin") or 0) for j in journeys),
        "doorToDoorMin": sum(
            _transfer_meta(j.get("legs") or [])["doorToDoorMin"] for j in journeys
        ),
    }


def flatten_structured(
    data: dict[str, Any], airlines: dict[str, str], airports: dict[str, str], cabins: dict[str, str],
    baggage: tuple[dict[str, str], dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    server_airports: dict[str, str] = {}
    for city in data.get("cityList") or []:
        code = str(_first(city, "airPortCode", "airportCode", "cityCode", default=""))
        name = str(_first(city, "airPortName", "airportName", "cityName", default=""))
        if code and name:
            server_airports[code] = name
    server_airlines: dict[str, str] = {}
    for airway in data.get("airwayList") or []:
        code = str(_first(airway, "companyNo", "airLine", "airlineCode", default=""))
        name = str(_first(airway, "companyName", "fullCompanyName", default=""))
        if code and name:
            server_airlines[code] = name
    # 机型代码 → 机型名（typeList 由服务端下发，如 359 → 空客350）
    aircraft_names: dict[str, str] = {}
    for item in data.get("typeList") or []:
        code = str(_first(item, "type", "aircraftCode", default=""))
        name = str(_first(item, "name", "aircraftName", default=""))
        if code and name:
            aircraft_names[code] = name

    records: list[dict[str, Any]] = []
    for rank, group in enumerate(data.get("groupList") or [], 1):
        prices = [item for item in (group.get("priceList") or []) if isinstance(item, dict)]
        # 列表「起」价取该组最便宜一档，不是 priceList 第一档。
        price = min(prices, key=lambda item: _amount_key(_first(item, "totalPrice", "total"))) if prices else {}
        price_trips = price.get("tripList") or []
        first_price_trip = price_trips[0] if price_trips and isinstance(price_trips[0], dict) else {}
        legs: list[dict[str, Any]] = []
        journeys: list[dict[str, Any]] = []
        direct = True
        total_duration = 0
        trips = group.get("tripList") or []
        if not trips:
            direct = False
        for trip in trips:
            flights = trip.get("flightList") or []
            if len(flights) != 1:
                direct = False
            journey_legs: list[dict[str, Any]] = []
            for flight in flights:
                stops = flight.get("stopList") or []
                direct = direct and not stops
                flight_no = str(_first(flight, "flightId", "flightNumber", default=""))
                airline_code = str(_first(flight, "airLine", "airlineCode", default=_air_prefix(flight_no)))
                from_code = str(_first(flight, "fromPort", "fromCode", default="")).strip()
                to_code = str(_first(flight, "toPort", "toCode", default="")).strip()
                # 部分数据源把航站楼（如 "T3"/"2"/空白）塞进 fromPort/toPort，真实机场码
                # 拼接在 airLine 字段（如 "SZXDPS" = SZX→DPS）。与 normalize_embedded 的
                # route_match 同款处理：airLine 命中 6 位拼接码且端口字段不是 3 位机场码时，
                # 从 airLine 拆出起止机场，并让航司码回退到航班号前缀。
                route_match = re.fullmatch(r"([A-Z]{3})([A-Z]{3})", airline_code)
                if route_match:
                    if not re.fullmatch(r"[A-Z]{3}", from_code):
                        from_code = route_match.group(1)
                    if not re.fullmatch(r"[A-Z]{3}", to_code):
                        to_code = route_match.group(2)
                    airline_code = _air_prefix(flight_no) or airline_code
                duration = int(_first(flight, "duration", "durationMinutes", default=0) or 0)
                total_duration += duration
                # fromPort/toPort 被 route_match 覆盖成机场码后，原始值（"T2"/"1"）是航站楼。
                from_term = str(flight.get("fromPort") or "").strip()
                to_term = str(flight.get("toPort") or "").strip()
                leg = {
                    "flightNo": flight_no,
                    "airlineCode": airline_code,
                    "airline": server_airlines.get(airline_code) or airlines.get(airline_code) or airline_code,
                    "fromCode": from_code,
                    "from": _airport_label(from_code, server_airports, airports),
                    "toCode": to_code,
                    "to": _airport_label(to_code, server_airports, airports),
                    "fromTerminal": "" if re.fullmatch(r"[A-Z]{3}", from_term) else from_term,
                    "toTerminal": "" if re.fullmatch(r"[A-Z]{3}", to_term) else to_term,
                    "dep": _first(flight, "flyDate", "departureTime"),
                    "arr": _first(flight, "arrDate", "arrivalTime"),
                    "dur": duration,
                    "aircraft": _first(flight, "type", "aircraft", default=""),
                    "aircraftName": aircraft_names.get(str(_first(flight, "type", "aircraft", default="")), ""),
                    # 共享航班：operatingFlightId 非空时，该航班由另一航班实际承运。
                    "operatingFlightNo": str(_first(flight, "operatingFlightId", "operatingFlightNo", default="") or "").strip(),
                }
                legs.append(leg)
                journey_legs.append(leg)
            if journey_legs:
                journeys.append(_journey(journey_legs))
        cabin_code = str(_first(first_price_trip, "cabClass", "cabin", default="--"))
        check_map, carry_map = baggage or ({}, {})
        bag = {"check": "", "carry": ""}
        cab_list = first_price_trip.get("cabList") or []
        if cab_list:
            c0 = cab_list[0]
            cid = c0.get("checkBaggageId")
            pid = c0.get("carryBaggageId")
            if cid is not None:
                bag["check"] = check_map.get(cid, "")
            if pid is not None:
                bag["carry"] = carry_map.get(pid, "")
        rule0 = first_price_trip.get("rule") or {}
        refundable = bool(rule0.get("refund"))
        changeable = bool(rule0.get("change"))
        upgradable = bool(rule0.get("upgra"))
        # 大客户价判定：脱敏后只下发 bigCustomerPrice 布尔；旧 customersId/selfBig 仍兼容。
        agreement = (
            bool(price.get("customersId"))
            or bool(price.get("selfBigCustomersId"))
            or price.get("bigCustomerPrice") is True
        )
        supplier = str(price.get("supplier") or "")
        # 往返/多程的不同 journey 之间不是中转；只在每个 journey 内聚合中转元数据。
        transfer = _journeys_meta(journeys)
        operated_by = [leg["operatingFlightNo"] for leg in legs if leg.get("operatingFlightNo")]
        # 特殊价规则（v3.19.1）：specialRate 报价的限制条件，原文保留（如「允许国籍：中国(CN)」），
        # 页面转写为「限中国大陆乘客预订」等标识。
        price_rules = [
            str(r.get("ruleDesc") or "").strip()
            for r in (price.get("ruleList") or [])
            if isinstance(r, dict) and str(r.get("ruleDesc") or "").strip()
        ]
        records.append({
            "rank": rank,
            "direct": direct and bool(legs),
            "recommended": bool(_first(price, "recommend", "recommended", default=False)),
            "groupId": group.get("groupId"),
            "priceId": price.get("priceId"),
            "legs": legs,
            "journeys": journeys,
            "cabin": cabins.get(cabin_code, cabin_code),
            "fareName": _first(first_price_trip, "caption", "fareName", default=""),
            "total": _first(price, "totalPrice", "total"),
            "fare": _first(price, "price", "fare"),
            "tax": price.get("tax"),
            # 费用拆分（v3.19.0）：附加费/服务费不计入 total（total=fare+tax），如实展示。
            "addPrice": price.get("addPrice"),
            "servicePrice": price.get("servicePrice"),
            "totalDurMin": total_duration,
            "finalDest": legs[-1]["toCode"] if legs else "",
            "baggage": bag,
            "refundable": refundable,
            "changeable": changeable,
            "upgradable": upgradable,
            "agreement": agreement,
            # 决策级补充字段（v2.6.0）：供应商/廉价航标记 + 中转元数据 + 门到门耗时
            "supplier": supplier,
            "lcc": supplier == "IBELCC",
            "stops": transfer["stops"],
            "transferAirports": transfer["transferAirports"],
            "sameAirport": transfer["sameAirport"],
            "layoverMin": transfer["layoverMin"],
            "doorToDoorMin": transfer["doorToDoorMin"] or total_duration,
            # 渠道与大客户字段（v3.19.0）：
            # codeshare=有共享承运段；source=价格来源（Ibe/IbeNdc/TongCheng）；
            # allowTicket=false 表示该报价不可在线出票（需代购）；
            # bigCustomer=大客户协议码（如 GBA10）——协议价=大客户号价（v3.19.1）；
            # specialRate=1 为特殊价：有特殊规则的协议价，限制条件在 priceRules（如限国籍）。
            "codeshare": bool(operated_by),
            "operatedBy": operated_by,
            "source": str(price.get("source") or ""),
            "allowTicket": bool(price.get("allowTicket", True)),
            "bigCustomer": str(price.get("customersId") or ""),
            "selfBig": bool(price.get("selfBigCustomersId")),
            "bigCustomerPrice": price.get("bigCustomerPrice") is True,
            "specialRate": price.get("specialRate"),
            "priceRules": price_rules,
        })
    return records


def _baggage_maps(baggage_list: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Build id -> short-text maps for checked and carry-on baggage."""
    check_map: dict[str, str] = {}
    carry_map: dict[str, str] = {}
    if not isinstance(baggage_list, list):
        return check_map, carry_map
    for item in baggage_list:
        if not isinstance(item, dict):
            continue
        bid = item.get("id")
        if bid is None:
            continue
        btype = item.get("baggageType")
        pieces = item.get("pieces")
        weight = item.get("weight")
        if pieces and weight:
            short = f"{pieces}件/{weight}kg"
        elif pieces:
            short = f"{pieces}件"
        elif weight:
            short = f"{weight}kg"
        else:
            short = item.get("textCh") or ""
        if btype == "check":
            check_map[bid] = short
        elif btype == "carry":
            carry_map[bid] = short
    return check_map, carry_map


def normalize_embedded(
    rows: list[dict[str, Any]], airlines: dict[str, str], airports: dict[str, str], cabins: dict[str, str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        legs: list[dict[str, Any]] = []
        for leg in row.get("legs") or []:
            flight_no = str(_first(leg, "flightNumber", "flightNo", default=""))
            carrier_code = _air_prefix(flight_no)
            airline_raw = str(_first(leg, "airline", "airlineCode", default=""))
            # 部分 MCP 渲染会把“出发机场码+到达机场码”（如 "PKXSIN"）塞进 airline 字段，
            # 而不是承运航司码。先识别并拆开；真实航司优先从航班号前缀取。
            route_match = re.fullmatch(r"([A-Z]{3})([A-Z]{3})", airline_raw)
            if route_match:
                from_code = route_match.group(1)
                to_code = route_match.group(2)
            else:
                from_code = str(_first(leg, "fromCode", default=_code_from_label(leg.get("from"))))
                to_code = str(_first(leg, "toCode", default=_code_from_label(leg.get("to"))))
            if carrier_code:
                airline_code = carrier_code
            elif re.fullmatch(r"[A-Z0-9]{2,3}", airline_raw):
                airline_code = airline_raw
            else:
                airline_code = str(_first(leg, "airlineCode", default=""))
            airline_name = airlines.get(airline_code, airline_code)
            legs.append({
                "flightNo": flight_no,
                "airlineCode": airline_code,
                "airline": airline_name,
                "fromCode": from_code,
                "from": _airport_label(from_code, {}, airports),
                "toCode": to_code,
                "to": _airport_label(to_code, {}, airports),
                "fromTerminal": "",
                "toTerminal": "",
                "dep": _first(leg, "departureTime", "dep"),
                "arr": _first(leg, "arrivalTime", "arr"),
                "dur": int(_first(leg, "durationMinutes", "dur", default=0) or 0),
                "aircraft": leg.get("aircraft") or "",
                "aircraftName": "",
                "operatingFlightNo": str(_first(leg, "operatingFlightNo", "operatingFlightId", default="") or "").strip(),
            })
        cabin_code = str(row.get("cabin") or "--")
        journeys = [_journey(legs)] if legs else []
        transfer = _journeys_meta(journeys)
        flight_duration = sum(int(leg.get("dur") or 0) for leg in legs)
        if flight_duration <= 0:
            flight_duration = int(_first(row, "totalDurationMinutes", "totalDurMin", default=0) or 0)
        operated_by = [leg["operatingFlightNo"] for leg in legs if leg.get("operatingFlightNo")]
        records.append({
            "rank": row.get("rank") or index,
            "direct": bool(row.get("direct")),
            "recommended": bool(row.get("recommended")),
            "groupId": row.get("groupId"),
            "priceId": row.get("priceId"),
            "legs": legs,
            "journeys": journeys,
            "cabin": cabins.get(cabin_code, cabin_code),
            "fareName": row.get("fareName") or "",
            "total": _first(row, "total", "totalPrice"),
            "fare": _first(row, "fare", "price"),
            "tax": row.get("tax"),
            "addPrice": row.get("addPrice"),
            "servicePrice": row.get("servicePrice"),
            "totalDurMin": flight_duration,
            "finalDest": legs[-1]["toCode"] if legs else "",
            "baggage": {"check": "", "carry": ""},
            # 嵌入的 flight-data 没有退改/行李/协议价字段，一律 false/空，避免假装有规则。
            "refundable": False,
            "changeable": False,
            "upgradable": False,
            "agreement": False,
            # 决策级补充字段（v2.6.0）：embedded 源无 supplier，中转元数据仍可从 legs 算出
            "supplier": "",
            "lcc": False,
            "stops": transfer["stops"],
            "transferAirports": transfer["transferAirports"],
            "sameAirport": transfer["sameAirport"],
            "layoverMin": transfer["layoverMin"],
            "doorToDoorMin": transfer["doorToDoorMin"] or int(_first(row, "totalDurationMinutes", "totalDurMin", default=0) or 0),
            # 渠道与大客户字段（v3.19.0）：embedded 源无渠道信息，给安全默认；共享标记可从 legs 算出。
            "codeshare": bool(operated_by),
            "operatedBy": operated_by,
            "source": "",
            "allowTicket": True,
            "bigCustomer": "",
            "selfBig": False,
            "bigCustomerPrice": False,
            "specialRate": 0,
            "priceRules": [],
        })
    return records


def _duration(minutes: Any) -> str:
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        return "--"
    return f"{value // 60}h{value % 60:02d}m"


_DT_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M")


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _transfer_meta(legs: list[dict[str, Any]]) -> dict[str, Any]:
    """从 legs 计算中转元数据：中转次数/机场/停留分钟/是否同机场/门到门分钟。

    这些字段是「给用户推荐航班」的决策核心（旧版缺失导致 agent 不得不逐字段
    python -c 探索原始 JSON）。时间解析失败时相应字段回退为 0/空，不抛异常。
    """
    meta = {"stops": max(0, len(legs) - 1), "transferAirports": [], "sameAirport": True,
            "layoverMin": 0, "doorToDoorMin": 0}
    if not legs:
        return meta
    for prev, nxt in zip(legs, legs[1:]):
        transfer_code = str(prev.get("toCode") or "").strip()
        meta["transferAirports"].append(transfer_code)
        if transfer_code and transfer_code != str(nxt.get("fromCode") or "").strip():
            meta["sameAirport"] = False
        arr = _parse_dt(prev.get("arr"))
        dep = _parse_dt(nxt.get("dep"))
        if arr and dep:
            meta["layoverMin"] += max(0, int((dep - arr).total_seconds() // 60))
    first_dep = _parse_dt(legs[0].get("dep"))
    last_arr = _parse_dt(legs[-1].get("arr"))
    if first_dep and last_arr:
        meta["doorToDoorMin"] = max(0, int((last_arr - first_dep).total_seconds() // 60))
    return meta


def _bag_short(text: Any) -> str:
    """行李额度缩短显示：'总重不超过25公斤,每件…' → '25kg'；'1件/23kg' 原样保留。"""
    if not text:
        return ""
    t = str(text).replace("公斤", "kg").replace("千克", "kg")
    if "/" in t:
        # 已是 '1件/23kg' 短格式
        return t if len(t) <= 14 else t[:14]
    match = re.search(r"(\d+)\s*kg", t)
    if match:
        return f"{match.group(1)}kg"
    return t if len(t) <= 14 else t[:14]


def _synthesize_summary(records: list[dict[str, Any]], serial_number: Any) -> str:
    """summary 信封缺失时合成一行总览（修复旧版 summary 恒为空串的问题）。"""
    direct = [r for r in records if r.get("direct")]
    transfer = [r for r in records if not r.get("direct")]
    parts = [f"航班 {len(records)} 班：直飞 {len(direct)} / 中转 {len(transfer)}"]
    for label, rows in (("直飞最低", direct), ("中转最低", transfer)):
        prices = [r.get("total") for r in rows if isinstance(r.get("total"), (int, float))]
        if prices:
            parts.append(f"{label} ¥{min(prices):.0f}")
    if serial_number:
        parts.append(f"serialNumber={serial_number}")
    return " · ".join(parts)


def render_text(records: list[dict[str, Any]], summary: str, rows: int = 15) -> str:
    """决策级摘要：每行含 行李/退改/中转机场+停留/同机场/廉价航 标记，
    使 agent 无需再对 parsed.json 做逐字段探索。"""
    lines = [summary, ""] if summary else []
    for title, values in (
        ("直飞", [row for row in records if row["direct"]]),
        ("中转/经停", [row for row in records if not row["direct"]]),
    ):
        values = sorted(values, key=lambda row: _amount_key(row.get("total")))
        prices = [row.get("total") for row in values if isinstance(row.get("total"), (int, float))]
        head = f"=== {title} {len(values)} 个方案（按价格）"
        if prices:
            head += f" ¥{min(prices):.0f}–¥{max(prices):.0f}"
        head += " ==="
        lines.append(head)
        for row in values[:rows]:
            # 对话里只打前 rows 条（默认 15，--rows 可调）；全量在 parsed json，
            # 避免 oversized shopping 倒进聊天。
            route = " + ".join(
                f"{leg.get('flightNo', '--')} {leg.get('fromCode', '--')} "
                f"{str(leg.get('dep', ''))[11:16]}→{leg.get('toCode', '--')} "
                f"{str(leg.get('arr', ''))[11:16]}"
                for leg in row["legs"]
            )
            tags = [row.get("cabin") or "--"]
            bag = row.get("baggage") or {}
            check = _bag_short(bag.get("check"))
            carry = _bag_short(bag.get("carry"))
            bag_text = "+".join(x for x in (check, carry) if x) or "无行李信息"
            tags.append(bag_text)
            tags.append(f"退{'✓' if row.get('refundable') else '✗'}"
                        f"改{'✓' if row.get('changeable') else '✗'}")
            if row.get("lcc"):
                tags.append("廉价航")
            if row.get("codeshare"):
                tags.append("共享")
            if not row.get("allowTicket", True):
                tags.append("代购")
            if row.get("specialRate"):
                tags.append("特殊价")
            elif row.get("agreement"):
                tags.append("协议价")
            # 对话摘要也只报飞行时长；中转停留单独通过「停」字段表达。
            dur = row.get("totalDurMin") or row.get("doorToDoorMin")
            if not row.get("direct"):
                airports = "·".join(row.get("transferAirports") or [])
                cross = "" if row.get("sameAirport", True) else "·跨机场"
                tags.append(f"中转{airports}停{_duration(row.get('layoverMin'))}{cross}")
            lines.append(
                f"#{row['rank']} ¥{row.get('total', '--')} [{_duration(dur)}] "
                f"{route} | {' · '.join(str(t) for t in tags)}"
            )
        if len(values) > rows:
            lines.append(f"…（其余 {len(values) - rows} 个方案见 parsed JSON / --rows 调整）")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="工具的返回：`-` 从 stdin 读，或 JSON 路径")
    parser.add_argument("--json", action="store_true", help="print normalized JSON（与 --html 同用时输出摘要而非全量）")
    parser.add_argument("--dest", help="keep rows whose final airport code matches")
    parser.add_argument("--output", type=Path, help="write normalized JSON to this file")
    parser.add_argument(
        "--html", nargs="?", const="", default=None,
        help="一步渲染可交互 HTML：自动调用同目录 air_intl_render_flight_options.py；"
             "可附带输出路径（如 --html out.html），不给路径则用默认名",
    )
    parser.add_argument("--title", default="", help="渲染页标题（仅 --html 生效）")
    parser.add_argument("--meta", action="append", default=[], help="渲染页展示事实（仅 --html 生效，可重复）")
    parser.add_argument("--action", default="select-flight", help="渲染页回传 action（仅 --html 生效：select-flight/select-cabin）")
    parser.add_argument("--rows", type=int, default=15, help="文本摘要每个分组最多打印的方案行数（默认 15）")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，航司中文/¥ 会崩。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    skill_root = Path(__file__).resolve().parents[1]
    airlines, airports, cabins = load_display_codes(skill_root / "references" / "air-intl-iata-codes.md")
    payload, input_path = _read_payload(args.input)
    # 快捷回退（v2.6.0）：输入本身已是 parsed.json（顶层有 flights[]）时直接重印摘要，
    # 免得 agent 为了看行李/中转信息再对 parsed.json 做逐字段 python -c 探索。
    if isinstance(payload, dict) and isinstance(payload.get("flights"), list):
        records = payload["flights"]
        serial_number = payload.get("serialNumber")
        # 授权码：intl_shopping 最外层下发；already-parsed 输入从旧 parsed.json 透传。
        forward_code = payload.get("forwardCode")
        info_code = payload.get("infoCode")
        source = "already-parsed"
        summary = _synthesize_summary(records, serial_number)
    else:
        blocks = _content_blocks(payload)
        summary = _summary(blocks)
        structured = _structured(payload, blocks)
        if structured is not None:
            baggage = _baggage_maps(structured.get("baggageList"))
            records = flatten_structured(structured, airlines, airports, cabins, baggage)
            serial_number = structured.get("serialNumber")
            # forwardCode→免登跳转；infoCode→页面侧舱位接口（intlShop）。
            forward_code = structured.get("forwardCode")
            info_code = structured.get("infoCode")
            source = "structuredContent"
        else:
            rows = _embedded_rows(blocks)
            if not rows:
                raise ValueError("未找到 structuredContent.groupList、原始 groupList 或 script#flight-data JSON")
            records = normalize_embedded(rows, airlines, airports, cabins)
            serial_number = _serial_from_blocks(blocks)
            # 展示映射没有授权码：该路径只能展示，不得进入选舱与下单跳转。
            forward_code = None
            info_code = None
            source = "embedded-flight-data"

    if args.dest:
        destination = args.dest.upper()
        # 多机场/备选目的地查询时只留飞到指定三字码的方案（如 --dest SIN）。
        records = [row for row in records if row.get("finalDest") == destination]
    # summary 修复（v2.6.0）：信封里没有纯文本摘要时合成一行总览，
    # 避免 parsed.json 的 summary 恒为空串、agent 还要自己数航班。
    if not summary:
        summary = _synthesize_summary(records, serial_number)
    output = {
        "source": source,
        "serialNumber": serial_number,
        "forwardCode": forward_code or None,
        "infoCode": info_code or None,
        "summary": summary,
        "flightCount": len(records),
        "flights": records,
    }
    if args.html is not None:
        # 渲染模式下 stdout 只输出摘要，避免把全量 JSON 倒进宿主上下文
        print(render_text(records, summary, rows=args.rows))
    elif args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(render_text(records, summary, rows=args.rows))

    output_path = args.output
    if output_path is None and input_path is not None:
        output_path = input_path.with_name(f"parsed_{input_path.stem}.json")
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[信息] 已写出结构化结果: {output_path}", file=sys.stderr)

    if args.html is not None:
        from subprocess import run as _run
        script_dir = Path(__file__).resolve().parent
        render_script = script_dir / "air_intl_render_flight_options.py"
        parsed_json = output_path or input_path
        if parsed_json is None:
            parsed_json = Path("parsed_result.json")
            parsed_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        cmd = [sys.executable, str(render_script), str(parsed_json)]
        if args.html:
            cmd += ["--output", args.html]
        if args.title:
            cmd += ["--title", args.title]
        for meta in args.meta:
            cmd += ["--meta", meta]
        if args.action != "select-flight":
            cmd += ["--action", args.action]
        print(f"[信息] 调用 {render_script.name} 渲染交互页…", file=sys.stderr)
        proc = _run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"[警告] 渲染失败（解析结果已保留）：{proc.stderr.strip()}", file=sys.stderr)
        else:
            print(proc.stdout.strip(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EnvelopeError as exc:
        print(f"[工具失败] {exc}", file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
