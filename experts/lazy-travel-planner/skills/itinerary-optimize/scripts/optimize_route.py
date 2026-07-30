#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
optimize_route.py · 单日 POI 顺路优化（TSP）
算法：节点 ≤ 10 全排列，> 10 贪心 + 2-opt
锚点：当天住宿（hotel）作起终点
"""
import argparse, json, itertools, math


def haversine(a, b):
    R = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def total_distance(coords):
    """coords: [hotel, p1, p2, ..., hotel]"""
    return sum(haversine(coords[i], coords[i+1]) for i in range(len(coords)-1))


def brute_force(hotel, pois):
    """节点少时全排列"""
    best, best_dist = None, float("inf")
    pts = [(p["lat"], p["lng"]) for p in pois]
    for perm in itertools.permutations(range(len(pois))):
        coords = [hotel] + [pts[i] for i in perm] + [hotel]
        d = total_distance(coords)
        if d < best_dist:
            best, best_dist = perm, d
    return list(best), best_dist


def greedy_nearest(hotel, pois):
    pts = [(p["lat"], p["lng"]) for p in pois]
    n = len(pois)
    visited = [False] * n
    order = []
    current = hotel
    for _ in range(n):
        best_d, best_i = float("inf"), -1
        for i in range(n):
            if visited[i]:
                continue
            d = haversine(current, pts[i])
            if d < best_d:
                best_d, best_i = d, i
        visited[best_i] = True
        order.append(best_i)
        current = pts[best_i]
    return order


def two_opt(order, hotel, pois, max_iter=200):
    pts = [(p["lat"], p["lng"]) for p in pois]
    def dist(o):
        coords = [hotel] + [pts[i] for i in o] + [hotel]
        return total_distance(coords)
    best = list(order)
    best_d = dist(best)
    for _ in range(max_iter):
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                new = best[:i] + best[i:j+1][::-1] + best[j+1:]
                nd = dist(new)
                if nd < best_d - 1e-6:
                    best, best_d = new, nd
                    improved = True
        if not improved:
            break
    return best, best_d


def optimize_day(hotel, pois):
    """主入口：返回排好序的 pois 列表 + 总距离"""
    if not pois:
        return [], 0.0
    if len(pois) <= 8:
        order, d = brute_force(hotel, pois)
    else:
        order = greedy_nearest(hotel, pois)
        order, d = two_opt(order, hotel, pois)
    return [pois[i] for i in order], d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="单日 cluster JSON {hotel, pois}")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    data = json.load(open(a.input, encoding="utf-8"))
    hotel = (data["hotel"]["lat"], data["hotel"]["lng"])
    sorted_pois, dist_km = optimize_day(hotel, data["pois"])
    out = {
        "hotel": data["hotel"],
        "ordered_pois": sorted_pois,
        "total_distance_km": round(dist_km, 2),
        "node_count": len(sorted_pois),
    }
    open(a.output, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print(json.dumps({"ok": True, "distance_km": round(dist_km, 2)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
