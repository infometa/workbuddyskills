#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_itinerary.py · 行程编排总入口
串起 geo_cluster → optimize_route → balance_pace，输出最终 itinerary.json
"""
import argparse, json, pathlib, sys, datetime, subprocess

THIS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR.parent.parent.parent / "shared"))

from check_deps import check_or_block           # noqa
from geo_cluster import cluster_pois            # noqa
from optimize_route import optimize_day         # noqa
from balance_pace import assign_time            # noqa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poi-pool", required=True)
    ap.add_argument("--trip", required=True, help="trip_request.json")
    ap.add_argument("--profile", required=True, help="user_profile.json")
    ap.add_argument("--hotel", required=True, help="hotel_candidates.json (取第 1 个为锚点)")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    # 软告知：未开通美团时，POI 坐标可能不准（依赖上游 04 给的数据精度）
    from check_deps import check_all  # noqa
    deps = check_all()
    if not deps["meituan_travel"]["ok"]:
        print("[build_itinerary] ⚠️ 美团未开通，POI 坐标精度依赖上游兜底数据，"
              "运筹结果置信度降为 🟡", file=sys.stderr)

    pool = json.loads(pathlib.Path(a.poi_pool).read_text(encoding="utf-8"))
    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    profile = json.loads(pathlib.Path(a.profile).read_text(encoding="utf-8"))
    hotels = json.loads(pathlib.Path(a.hotel).read_text(encoding="utf-8"))

    # 拍平 by_city（MVP 先按单城市处理；多城走第一个城市）
    flat = []
    main_city = None
    if isinstance(pool, dict) and "by_city" in pool:
        for city, by_cat in pool["by_city"].items():
            main_city = main_city or city
            for cat, items in by_cat.items():
                for it in items:
                    it.setdefault("category", cat)
                    flat.append(it)
    pace = (profile.get("basic") or {}).get("preferred_pace", "normal")

    days_clusters = cluster_pois(flat, trip["duration_days"])
    hotel_anchor = hotels[0] if isinstance(hotels, list) else hotels.get("stays", [{}])[0].get("hotels", [{}])[0]

    days_out = []
    start_date = datetime.date.fromisoformat(trip["start_date"])
    for i, day in enumerate(days_clusters):
        ordered, dist_km = optimize_day(
            (hotel_anchor["lat"], hotel_anchor["lng"]),
            day["pois"]
        )
        timeline, fatigue = assign_time(ordered, hotel_anchor, pace)
        days_out.append({
            "day_index": day["day_index"],
            "date": (start_date + datetime.timedelta(days=i)).isoformat(),
            "theme": _infer_theme(day["pois"]),
            "hotel": hotel_anchor,
            "stops": [
                {
                    "order": j + 1,
                    "time": s["time"],
                    "type": s["type"],
                    "poi": {
                        "name": s["poi"]["name"],
                        "lat": s["poi"]["lat"],
                        "lng": s["poi"]["lng"],
                        "category": s["poi"].get("category"),
                        "rating": s["poi"].get("amap_rating") or s["poi"].get("rating"),
                        "ticket_price": s["poi"].get("ticket_price", 0),
                        "open_hours": s["poi"].get("open_hours"),
                    },
                    "duration_min": _slot_duration(s["time"]),
                }
                for j, s in enumerate(timeline)
            ],
            "total_distance_km": round(dist_km, 2),
            "fatigue_index": fatigue,
        })

    backup_pool = [p for p in flat if p.get("name") not in
                   {s["poi"]["name"] for d in days_out for s in d["stops"]}]

    out = {
        "trip_id": trip.get("session_id") or "trip-" + start_date.isoformat(),
        "main_city": main_city,
        "days": days_out,
        "backup_pool": backup_pool[:30],
        "metadata": {
            "algorithm_version": "1.0",
            "total_poi_used": sum(len(d["stops"]) for d in days_out),
            "total_poi_pool": len(flat),
            "pace": pace,
        }
    }
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "days": len(days_out), "stops": out["metadata"]["total_poi_used"]}, ensure_ascii=False))


def _infer_theme(pois):
    cats = [p.get("category", "") for p in pois]
    if any("博物" in c or "museum" in c for c in cats):
        return "文化探索"
    if any("山" in c or "湖" in c or "公园" in c for c in cats):
        return "自然风光"
    if any("夜" in str(p.get("name", "")) for p in pois):
        return "夜游夜市"
    return "综合体验"


def _slot_duration(t):
    s, e = t.split("-")
    sh, sm = map(int, s.split(":"))
    eh, em = map(int, e.split(":"))
    return (eh * 60 + em) - (sh * 60 + sm)


if __name__ == "__main__":
    main()
