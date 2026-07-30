#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
accommodation-pick/pick_hotel.py · 住宿选型胶水脚本
1) 计算 anchor_pois 的地理质心
2) 调 search-orchestrator (domain=accommodation) 拿酒店候选
3) 三维评分（位置/价位/口碑）排序，输出 Top 3-5
"""
import argparse, json, pathlib, subprocess, sys, math

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
ORCHESTRATOR = ROOT / "skills" / "search-orchestrator" / "scripts" / "orchestrate.py"
BENCH_PATH = ROOT / "data" / "price_benchmark.json"


def haversine_km(a, b):
    R = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def centroid(pois):
    return (sum(p["lat"] for p in pois) / len(pois),
            sum(p["lng"] for p in pois) / len(pois))


def score_hotel(h, anchor, bench_range):
    # 位置：距 anchor < 5km 满分，> 10km 0 分
    d = haversine_km(anchor, (h["lat"], h["lng"]))
    pos = max(0.0, min(1.0, (10 - d) / 10))
    # 价位：在 bench 区间内满分
    p = h.get("price_per_night_ref", 0) or 0
    lo, hi = bench_range
    if lo <= p <= hi:
        price = 1.0
    elif p < lo:
        price = 0.7
    else:
        price = max(0.0, 1.0 - (p - hi) / hi)
    # 口碑
    rating = h.get("amap_rating") or h.get("rating") or 0
    rep = max(0.0, min(1.0, (float(rating) - 3.0) / 2.0)) if rating else 0.5
    return round(pos * 0.4 + price * 0.3 + rep * 0.3, 3), d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--anchor-pois", required=True, help="JSON 文件，含 [{lat,lng,...}] 列表")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    pois = json.loads(pathlib.Path(a.anchor_pois).read_text(encoding="utf-8"))
    if isinstance(pois, dict) and "by_city" in pois:
        flat = []
        for city, by_cat in pois["by_city"].items():
            for cat, items in by_cat.items():
                flat.extend(items)
        pois = flat
    anchor = centroid(pois) if pois else (CITY_DEFAULT.get(trip["destination"], (30.5, 104.0)))

    bench = json.loads(pathlib.Path(BENCH_PATH).read_text(encoding="utf-8"))
    tier = (trip.get("budget_tier") or "standard").lower()
    city_data = bench["cities"].get(trip["destination"]) or list(bench["cities"].values())[0]
    bench_range = city_data["hotel"][tier]

    cache = pathlib.Path(a.output).parent / "00_orchestrator_accommodation.json"
    intent = f"{trip['destination']} 酒店推荐 {tier}"
    r = subprocess.run([
        sys.executable, str(ORCHESTRATOR),
        "--intent", intent,
        "--profile", a.profile,
        "--domain", "accommodation",
        "--output", str(cache),
    ], capture_output=True, text=True)
    if r.returncode == 2:
        print(r.stdout)
        sys.exit(2)

    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        candidates = data.get("geo_candidates") or []
    else:
        candidates = []

    scored = []
    for h in candidates:
        if not h.get("lat") or not h.get("lng"):
            continue
        h.setdefault("price_per_night_ref", (bench_range[0] + bench_range[1]) // 2)
        s, d = score_hotel(h, anchor, bench_range)
        h["score"] = s
        h["distance_to_anchor_km"] = round(d, 2)
        h["confidence"] = h.get("confidence", "yellow")
        scored.append(h)
    scored.sort(key=lambda x: x["score"], reverse=True)

    out = {
        "anchor_centroid": {"lat": anchor[0], "lng": anchor[1]},
        "candidates_count": len(scored),
        "stays": [{
            "nights": max(1, trip["duration_days"] - 1),
            "area": trip["destination"],
            "hotels": scored[:5],
        }]
    }
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "candidates": len(scored)}, ensure_ascii=False))


CITY_DEFAULT = {}  # 备用，可填城市默认坐标

if __name__ == "__main__":
    main()
