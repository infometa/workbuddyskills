#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_html.py · 用 Jinja2 把 5 份 JSON 渲染成单文件 HTML 行程书
依赖：jinja2（必装）

用法：
  python render_html.py \
    --itinerary itinerary.json \
    --transport transport.json \
    --hotel hotel_candidates.json \
    --budget budget.json \
    --risk risk_report.json \
    --trip trip_request.json \
    --output output/<城市>-<日期>-行程书.html
"""
from __future__ import annotations

import argparse, json, pathlib, datetime, os, re, sys

ROOT = pathlib.Path(__file__).parent.parent  # skills/report-render/
TEMPLATE_DIR = ROOT / "templates"
STYLES_PATH = TEMPLATE_DIR / "styles.css"

# 项目根（用于读 data/skeleton_fallbacks.json）
AGENT_ROOT = ROOT.parent.parent  # 出游规划师/
SHARED_DIR = AGENT_ROOT / "shared"
sys.path.insert(0, str(SHARED_DIR))


def _ensure_jinja2():
    try:
        import jinja2  # noqa
        return
    except ImportError:
        print("📦 安装 jinja2（一次性）...", flush=True)
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "jinja2"],
                       check=True, capture_output=True)


def calc_confidence_summary(*all_data):
    """粗算所有数据的置信度构成"""
    g = y = w = 0
    for d in all_data:
        s = json.dumps(d, ensure_ascii=False)
        g += s.count('"confidence": "green"')
        y += s.count('"confidence": "yellow"')
        w += s.count('"confidence": "gray"')
    total = g + y + w
    if total == 0:
        return {"green_pct": 0, "yellow_pct": 0, "gray_pct": 0}
    return {
        "green_pct": round(g / total * 100),
        "yellow_pct": round(y / total * 100),
        "gray_pct": round(w / total * 100),
    }


def _first_present(d: dict, *keys):
    for key in keys:
        value = d.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_price(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"(\d+(?:\.\d+)?)", str(value).replace(",", ""))
    return int(float(match.group(1))) if match else value


def _parse_route_text(value):
    if not value:
        return None, None
    parts = re.split(r"\s*(?:→|->|—|-|到|至)\s*", str(value), maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None


def _parse_time_range(value):
    if not value:
        return None, None
    times = re.findall(r"\d{1,2}:\d{2}", str(value))
    if len(times) >= 2:
        return times[0], times[1]
    return None, None


def _parse_duration_min(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    hour_match = re.search(r"(\d+)\s*(?:h|小时|时)", text, re.I)
    min_match = re.search(r"(\d+)\s*(?:m|min|分钟|分)", text, re.I)
    if hour_match or min_match:
        hours = int(hour_match.group(1)) if hour_match else 0
        minutes = int(min_match.group(1)) if min_match else 0
        return hours * 60 + minutes
    plain = re.search(r"\d+", text)
    return int(plain.group(0)) if plain else None


def _duration_between(start, end):
    if not start or not end:
        return None
    try:
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
    except ValueError:
        return None
    minutes = (eh * 60 + em) - (sh * 60 + sm)
    return minutes if minutes > 0 else None


def _normalize_transport_option(opt: dict, parent_mode: str | None = None) -> dict:
    opt = dict(opt or {})
    route_from, route_to = _parse_route_text(_first_present(
        opt, "route", "route_text", "station_pair", "from_to"
    ))
    time_from, time_to = _parse_time_range(_first_present(
        opt, "time", "time_range", "schedule", "depart_arrive_time"
    ))
    duration = _first_present(opt, "duration_min", "duration_minutes")
    if duration in (None, ""):
        duration = _parse_duration_min(_first_present(opt, "duration", "duration_text", "elapsed"))
    if duration in (None, "") and time_from and time_to:
        duration = _duration_between(time_from, time_to)

    opt["mode"] = _first_present(opt, "mode", "transport_mode") or parent_mode or "high_speed_rail"
    opt["train_no"] = _first_present(opt, "train_no", "train_number", "train", "code", "no")
    opt["flight_no"] = _first_present(opt, "flight_no", "flight_number", "flight")
    opt["depart_station"] = _first_present(opt, "depart_station", "from_station", "origin_station", "from") or route_from
    opt["arrive_station"] = _first_present(opt, "arrive_station", "to_station", "dest_station", "destination_station", "to") or route_to
    opt["depart_time"] = _first_present(opt, "depart_time", "departure_time", "start_time") or time_from
    opt["arrive_time"] = _first_present(opt, "arrive_time", "arrival_time", "end_time") or time_to
    opt["duration_min"] = duration
    opt["price_ref"] = _parse_price(_first_present(
        opt, "price_ref", "price", "fare", "ticket_price", "second_class_price", "price_text"
    ))
    opt["ticket_class"] = _first_present(opt, "ticket_class", "seat_class", "cabin") or opt.get("ticket_class")
    return opt


def _normalize_transport(trans: dict) -> dict:
    trans = dict(trans or {})
    for key, aliases in {
        "outbound": ("outbound", "go", "depart", "departure"),
        "return": ("return", "inbound", "back", "return_trip"),
    }.items():
        block = next((trans.get(a) for a in aliases if trans.get(a)), {})
        if isinstance(block, list):
            block = {"options": block}
        block = dict(block or {})
        options = block.get("options") or block.get("trains") or block.get("flights") or []
        if isinstance(options, dict):
            options = [options]
        block["options"] = [_normalize_transport_option(o, block.get("mode")) for o in options]
        trans[key] = block
    return trans


def _normalize_hotels(hotels):
    if isinstance(hotels, dict) and "stays" in hotels:
        raw_hotels = []
        for stay in hotels.get("stays") or []:
            raw_hotels.extend(stay.get("hotels") or [])
    elif isinstance(hotels, dict):
        raw_hotels = hotels.get("hotels") or hotels.get("candidates") or hotels.get("options")
        if raw_hotels is None:
            raw_hotels = [hotels.get("selected_hotel") or hotels.get("hotel") or hotels]
    else:
        raw_hotels = hotels or []

    normalized = []
    for h in raw_hotels:
        h = dict(h or {})
        h["name"] = _first_present(h, "name", "hotel_name", "title", "display_name")
        h["price_per_night_ref"] = _parse_price(_first_present(
            h, "price_per_night_ref", "price_ref", "price", "nightly_price", "price_per_night", "price_text"
        ))
        h["area"] = _first_present(h, "area", "district", "location", "address")
        h["recommend_reason"] = _first_present(h, "recommend_reason", "reason", "highlight", "why")
        rating = h.get("rating")
        if rating and not isinstance(rating, dict):
            h["rating"] = {"meituan": rating, "xhs_sentiment": h.get("xhs_sentiment", "参考")}
        normalized.append(h)
    return normalized


def _time_start(value):
    match = re.search(r"\d{1,2}:\d{2}", str(value or ""))
    return match.group(0) if match else None


def _normalize_itinerary(itin: dict) -> dict:
    itin = dict(itin or {})
    for day in itin.get("days", []) or []:
        stops = day.get("stops") or []
        starts = [_time_start(s.get("time")) for s in stops]
        for idx, stop in enumerate(stops):
            if stop.get("duration_min") in (None, ""):
                inferred = _duration_between(starts[idx], starts[idx + 1] if idx + 1 < len(starts) else None)
                if inferred:
                    stop["duration_min"] = inferred
            stop["duration_display"] = (
                f"{stop['duration_min']} 分钟" if stop.get("duration_min") not in (None, "")
                else _first_present(stop, "duration", "duration_text") or "待核实"
            )
            stop.setdefault("poi", {})
            stop["poi"]["name"] = _first_present(stop["poi"], "name", "title", "poi_name") or stop.get("name")
    return itin


def _extract_xhs_raw_notes(data) -> list:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("evidence", "raw_notes", "notes", "items", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    nested = []
    for key in ("groups", "themes"):
        value = data.get(key)
        if isinstance(value, list):
            for group in value:
                if isinstance(group, dict):
                    nested.extend(group.get("notes") or group.get("items") or [])
            if nested:
                return nested
    for value in data.values():
        if isinstance(value, dict):
            nested.extend(_extract_xhs_raw_notes(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nested.extend(_extract_xhs_raw_notes(item))
    return nested


def _normalize_xhs_note(raw: dict) -> dict | None:
    raw = dict(raw or {})
    interact = raw.get("interact_info") or {}
    nid = _first_present(raw, "note_id", "id", "noteId")
    title = _first_present(raw, "display_title", "title", "name", "desc", "snippet")
    desc = _first_present(raw, "full_content", "desc", "content", "snippet", "summary") or ""
    url = _first_present(raw, "url", "link", "note_url")
    if not url and nid:
        url = f"https://www.xiaohongshu.com/discovery/item/{nid}"
    if not (title or desc):
        return None

    cover = ""
    if isinstance(raw.get("cover"), dict):
        cover = _first_present(raw["cover"], "url_default", "url")
    elif isinstance(raw.get("cover"), str):
        cover = raw["cover"]
    elif isinstance(raw.get("images_list"), list) and raw["images_list"]:
        first = raw["images_list"][0]
        cover = first.get("url") if isinstance(first, dict) else first

    author = _first_present(raw, "author", "source", "nickname")
    if isinstance(raw.get("user"), dict):
        author = _first_present(raw["user"], "nickname", "nick_name") or author

    return {
        "title": str(title)[:60],
        "url": url or "https://www.xiaohongshu.com/",
        "cover": cover or "",
        "author": author or "",
        "likes": _first_present(raw, "liked_count", "likes") or interact.get("liked_count"),
        "comments": _first_present(raw, "comment_count", "comments") or interact.get("comment_count"),
        "snippet": str(desc)[:120].replace("\n", " "),
        "sentiment": _first_present(raw, "sentiment") or "neutral",
    }


def _normalize_xhs_notes(xhs_notes):
    raw_notes = _extract_xhs_raw_notes(xhs_notes)
    normalized = []
    for raw in raw_notes:
        if isinstance(raw, dict):
            note = _normalize_xhs_note(raw)
            if note:
                normalized.append(note)
    return [{"theme": "真实笔记参考", "notes": normalized}] if normalized else None


def _normalize_risk(risk: dict, skeleton_fallbacks: dict | None = None) -> dict:
    risk = dict(risk or {})
    fallback = (skeleton_fallbacks or {}).get("risk_panel_default") or {}

    weather = risk.get("weather")
    if not isinstance(weather, dict):
        weather = {"summary": weather} if weather else {}
    risk["weather"] = {
        "summary": weather.get("summary") or weather.get("details") or fallback.get("weather", "天气信息待核实"),
        "recommendations": weather.get("recommendations") or weather.get("tips") or [],
        "confidence": weather.get("confidence") or "yellow",
    }

    holiday = risk.get("holiday_alert")
    if not isinstance(holiday, dict):
        holiday = {}
    risk["holiday_alert"] = {
        "is_holiday": bool(holiday.get("is_holiday")),
        "holiday_name": holiday.get("holiday_name") or holiday.get("name") or "常规出行日",
        "details": holiday.get("details") or holiday.get("summary") or "",
        "alternative_dates": holiday.get("alternative_dates") or [],
    }

    scams = risk.get("scams_to_watch") or risk.get("scams") or risk.get("pitfalls") or []
    if not scams and isinstance(risk.get("risks"), list):
        scams = [
            r for r in risk["risks"]
            if any(k in str(r.get("category") or r.get("title") or r) for k in ("坑", "骗", "避雷", "风险"))
        ]
    normalized_scams = []
    for item in scams:
        if isinstance(item, str):
            normalized_scams.append({"category": "防坑提示", "items": [item]})
        elif isinstance(item, dict):
            points = item.get("items") or item.get("points") or item.get("tips")
            if isinstance(points, str):
                points = [points]
            normalized_scams.append({
                "category": item.get("category") or item.get("title") or "防坑提示",
                "city": item.get("city"),
                "items": points or [item.get("summary") or item.get("details") or "出行前再次核实"],
            })
    risk["scams_to_watch"] = normalized_scams or fallback.get("scams") or []

    contacts = risk.get("emergency_contacts")
    risk["emergency_contacts"] = contacts if isinstance(contacts, dict) else {}
    return risk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--itinerary", required=True)
    ap.add_argument("--transport", required=True)
    ap.add_argument("--hotel", required=True)
    ap.add_argument("--budget", required=True)
    ap.add_argument("--risk", required=True)
    ap.add_argument("--trip", required=True)
    ap.add_argument("--checklist", help="可选，外部输入；缺省则用 risk_report.pre_trip_checklist")
    ap.add_argument("--xhs-notes", help="可选，按主题分组的 xhs 笔记 JSON")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    _ensure_jinja2()
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    itin = _normalize_itinerary(json.loads(pathlib.Path(a.itinerary).read_text(encoding="utf-8")))
    trans = _normalize_transport(json.loads(pathlib.Path(a.transport).read_text(encoding="utf-8")))
    hotels = _normalize_hotels(json.loads(pathlib.Path(a.hotel).read_text(encoding="utf-8")))
    budget = json.loads(pathlib.Path(a.budget).read_text(encoding="utf-8"))
    risk = json.loads(pathlib.Path(a.risk).read_text(encoding="utf-8"))
    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    checklist = (json.loads(pathlib.Path(a.checklist).read_text(encoding="utf-8"))
                 if a.checklist else risk.get("pre_trip_checklist") or {})
    xhs_notes = _normalize_xhs_notes(
        json.loads(pathlib.Path(a.xhs_notes).read_text(encoding="utf-8"))
        if a.xhs_notes and pathlib.Path(a.xhs_notes).exists() else None
    )

    # 加载骨架硬兜底数据
    fallbacks_path = AGENT_ROOT / "data" / "skeleton_fallbacks.json"
    skeleton_fallbacks = (json.loads(fallbacks_path.read_text(encoding="utf-8"))
                          if fallbacks_path.exists() else {})
    risk = _normalize_risk(risk, skeleton_fallbacks)

    # 加载 data_sources（哪些数据源激活了，给"数据完整性面板"用）
    data_sources = {"meituan_travel": False, "xhs_logged_in": False,
                    "qweather": False, "websearch": True}
    try:
        from check_deps import get_active_sources
        data_sources.update(get_active_sources())
    except Exception:
        pass
    # agent 也可以传 skipped/degraded 进来
    skip_marker = AGENT_ROOT / "data" / ".skip_marker.json"
    if skip_marker.exists():
        try:
            data_sources["skipped"] = json.loads(skip_marker.read_text(encoding="utf-8")).get("skipped", [])
        except Exception:
            pass

    # ===== 骨架完整性体检（控制台 print 给 agent 看） =====
    warnings = []
    days_no_routes = [d.get("day_index") for d in itin.get("days", []) if not d.get("routes")]
    if days_no_routes:
        warnings.append(f"⚠️ 以下天的 routes 字段缺失，地图只能画虚线兜底：{days_no_routes}")
    poi_no_coord = sum(1 for d in itin.get("days", []) for s in d.get("stops", [])
                       if not (s.get("poi", {}).get("lat") and s.get("poi", {}).get("lng")))
    if poi_no_coord:
        warnings.append(f"⚠️ 共 {poi_no_coord} 个 POI 缺坐标，建议 agent 补 lat/lng")
    if not xhs_notes:
        warnings.append("⚠️ xhs_notes 为空，模板会渲染兜底搜索链接卡片")
    if not hotels:
        warnings.append("⚠️ 酒店候选为空，建议 agent 至少补 3 家")
    if warnings:
        print("\n[render_html] 骨架完整性体检（仅 agent 可见）:", file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)

    confidence = calc_confidence_summary(itin, trans, hotels, budget, risk)

    # 计算 end_date
    start = datetime.date.fromisoformat(trip["start_date"])
    end = (start + datetime.timedelta(days=trip["duration_days"] - 1)).isoformat()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("itinerary.html")

    html = template.render(
        trip={
            "main_city": itin.get("main_city") or trip.get("destination"),
            "start_date": trip["start_date"],
            "end_date": end,
            "party_size": trip.get("party_size", 2),
            "duration_days": trip["duration_days"],
        },
        itinerary=itin,
        transport=trans,
        hotels=hotels,
        budget=budget,
        risk=risk,
        checklist=checklist,
        xhs_notes=xhs_notes,
        skeleton_fallbacks=skeleton_fallbacks,
        data_sources=data_sources,
        confidence=confidence,
        styles_css=STYLES_PATH.read_text(encoding="utf-8") if STYLES_PATH.exists() else "",
        amap_key=os.getenv("AMAP_MAPS_API_KEY", ""),
        agent_version="1.0.0",
        generated_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    )

    out = pathlib.Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(out), "bytes": len(html)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
