#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
risk-check/check_risks.py · 风险体检胶水脚本
读 itinerary + trip_request + risk_knowledge.json
拼装五大类风险报告（天气由 agent 调高德/和风 MCP 后 merge 进来）
"""
import argparse, json, pathlib, datetime

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
RISK_KB = ROOT / "data" / "risk_knowledge.json"


def detect_holiday(start_date_str, kb):
    d = datetime.date.fromisoformat(start_date_str)
    holidays = kb.get("holiday_warnings") or {}
    md = (d.month, d.day)
    if md in [(4, 4), (4, 5), (4, 6)]:
        return {"is_holiday": True, "name": "清明", "details": holidays.get("qingming"),
                "alternative_dates": []}
    if md in [(5, 1), (5, 2), (5, 3), (5, 4), (5, 5)]:
        return {"is_holiday": True, "name": "五一", "details": holidays.get("labor_day"),
                "alternative_dates": []}
    if md in [(10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7)]:
        return {"is_holiday": True, "name": "国庆", "details": holidays.get("national_day"),
                "alternative_dates": ["2026-10-08 之后"]}
    if d.month == 2 and d.day < 15:
        return {"is_holiday": True, "name": "春节", "details": holidays.get("spring_festival"),
                "alternative_dates": []}
    return {"is_holiday": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True)
    ap.add_argument("--itinerary", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    itin = json.loads(pathlib.Path(a.itinerary).read_text(encoding="utf-8"))
    profile = json.loads(pathlib.Path(a.profile).read_text(encoding="utf-8"))
    kb = json.loads(pathlib.Path(RISK_KB).read_text(encoding="utf-8"))

    # 1. 节假日
    holiday = detect_holiday(trip["start_date"], kb)

    # 2. 城市防坑（按 itinerary 涉及的城市）
    cities = {itin.get("main_city") or trip["destination"]}
    for d in itin.get("days", []):
        for s in d.get("stops") or []:
            poi = s.get("poi") or {}
            if poi.get("city"):
                cities.add(poi["city"])

    scams = []
    city_specific = kb.get("city_specific_warnings", {}) or {}
    for c in cities:
        if c in city_specific:
            scams.append({
                "category": "city_specific",
                "city": c,
                "items": city_specific[c],
                "source": "risk_knowledge.json",
                "confidence": "green"
            })
    scams.append({
        "category": "general",
        "items": [s["name"] + "：" + s["prevention"] for s in (kb.get("general_scams") or [])[:5]],
        "confidence": "green"
    })

    # 3. 行前清单（按 user_profile 微调）
    kit = kb.get("general_kit") or {}
    physical = profile.get("physical", {}) or {}
    extra_health = []
    if physical.get("motion_sickness"):
        extra_health.append("晕车药（你 profile 标了 motion_sickness）")
    pre = {
        "ids": kit.get("ids", []),
        "health": (kit.get("health", []) or []) + extra_health,
        "weather": kit.get("weather", []),
        "tech": kit.get("tech", []),
        "money": kit.get("money", []),
    }

    out = {
        "trip_id": itin.get("trip_id"),
        "weather": {
            "summary": "请由 agent 调高德 maps_weather / 和风预警 MCP 填充",
            "by_day": [],
            "confidence": "gray",
            "_doc": "stub；agent runtime 拿到天气后 merge"
        },
        "holiday_alert": {
            "is_holiday": holiday["is_holiday"],
            "holiday_name": holiday.get("name"),
            "level": "warning" if holiday["is_holiday"] else "ok",
            "details": holiday.get("details"),
            "alternative_dates": holiday.get("alternative_dates", []),
        },
        "traffic_restrictions": {"applicable": False},
        "scams_to_watch": scams,
        "emergency_contacts": kb.get("emergency_contacts") or {},
        "pre_trip_checklist": pre,
    }
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "scam_groups": len(scams)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
