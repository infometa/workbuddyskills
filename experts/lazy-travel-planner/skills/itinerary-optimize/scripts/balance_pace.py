#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
balance_pace.py · 给排好序的单日 POI 序列分配时间轴
约束：
  - 早餐 7:30-9:00 / 午餐 12:00-13:30 / 晚餐 18:00-19:30
  - 上午景点 9:30-12:00（≤2 个）/ 下午 14:30-17:30（≤2 个）/ 晚间 20:00-22:00（可选）
  - 检查营业时间冲突（用 open_hours 字段）
  - 按 user_profile.basic.preferred_pace 限制每日景点数
体力指数：
  - 累加 walk_steps_est + 景点用时
  - >0.85 警告
"""
import argparse, json
from datetime import datetime, timedelta


SLOTS = [
    ("breakfast",     "07:30", "09:00"),
    ("morning_1",     "09:30", "11:00"),
    ("morning_2",     "11:00", "12:00"),
    ("lunch",         "12:00", "13:30"),
    ("afternoon_1",   "14:30", "16:00"),
    ("afternoon_2",   "16:00", "17:30"),
    ("dinner",        "18:00", "19:30"),
    ("evening_1",     "20:00", "22:00"),
]


def _hm_to_minutes(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def _is_open(poi, slot_start, slot_end):
    oh = poi.get("open_hours") or ""
    if not oh:
        return True  # 未知就当开
    # 简单 parse "08:00-18:00"
    parts = oh.split("-")
    if len(parts) != 2:
        return True
    try:
        oh_start = _hm_to_minutes(parts[0].strip())
        oh_end = _hm_to_minutes(parts[1].strip())
        return oh_start <= slot_start and slot_end <= oh_end
    except Exception:
        return True


def _category_of_slot(slot_name):
    if "breakfast" in slot_name:
        return "breakfast"
    if "lunch" in slot_name:
        return "lunch"
    if "dinner" in slot_name:
        return "dinner"
    if "evening" in slot_name:
        return "evening"
    if "morning" in slot_name or "afternoon" in slot_name:
        return "scenic_spot"


def _pace_limit(pace):
    return {
        "walker_intense": 5,
        "normal":         4,
        "relaxed":        2,
    }.get(pace, 3)


def assign_time(ordered_pois, hotel, pace="normal"):
    """返回每个 POI 带 time slot 的列表"""
    by_type = {}
    for p in ordered_pois:
        t = p.get("category") or p.get("type") or "scenic_spot"
        by_type.setdefault(t, []).append(p)

    result = []
    used_slots = set()
    scenic_used = 0
    scenic_limit = _pace_limit(pace)

    for slot_name, start, end in SLOTS:
        cat = _category_of_slot(slot_name)
        pool = by_type.get(cat) or by_type.get("restaurant" if cat in ("breakfast", "lunch", "dinner") else None) or []
        if cat == "scenic_spot":
            pool = by_type.get("scenic_spot") or []
            if scenic_used >= scenic_limit:
                continue
        # 选第一个营业的
        chosen = None
        for p in pool:
            if id(p) in used_slots:
                continue
            if _is_open(p, _hm_to_minutes(start), _hm_to_minutes(end)):
                chosen = p
                break
        if not chosen:
            continue
        used_slots.add(id(chosen))
        if cat == "scenic_spot":
            scenic_used += 1
        result.append({
            "slot": slot_name,
            "time": f"{start}-{end}",
            "type": cat,
            "poi": chosen,
        })

    # 体力指数
    walk_steps = sum(p["poi"].get("est_walk_steps", 3000) for p in result)
    fatigue = min(1.0, walk_steps / 25000)
    return result, fatigue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="单日 ordered_pois JSON")
    ap.add_argument("--pace", default="normal")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    data = json.load(open(a.input, encoding="utf-8"))
    timeline, fatigue = assign_time(data["ordered_pois"], data.get("hotel"), a.pace)
    out = {
        "hotel": data.get("hotel"),
        "timeline": timeline,
        "fatigue_index": round(fatigue, 2),
        "warning": "fatigue_high" if fatigue > 0.85 else None,
    }
    open(a.output, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print(json.dumps({"ok": True, "stops": len(timeline), "fatigue": round(fatigue, 2)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
