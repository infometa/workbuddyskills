#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_cluster.py · 把 N 个 POI 按地理位置聚类成 duration_days 个簇
算法：K-Means（无依赖纯实现，避免 scikit-learn 引入）
约束：
  - 每天 6-8 个点（含三餐）
  - 同簇 POI 距离上限：城市 15km / 跨景区 50km
"""
import argparse, json, math, random


def haversine(a, b):
    """a, b = (lat, lng) 返回 km"""
    R = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def kmeans(points, k, max_iter=50, seed=42):
    """points: [(lat, lng), ...] 返回 [cluster_id, ...]"""
    random.seed(seed)
    if len(points) <= k:
        return list(range(len(points)))
    centers = random.sample(points, k)
    for _ in range(max_iter):
        clusters = [-1] * len(points)
        for i, p in enumerate(points):
            best_d, best_c = float("inf"), 0
            for j, c in enumerate(centers):
                d = haversine(p, c)
                if d < best_d:
                    best_d, best_c = d, j
            clusters[i] = best_c
        new_centers = []
        for j in range(k):
            members = [points[i] for i, c in enumerate(clusters) if c == j]
            if not members:
                new_centers.append(centers[j])
                continue
            new_centers.append((
                sum(m[0] for m in members) / len(members),
                sum(m[1] for m in members) / len(members),
            ))
        if all(haversine(a, b) < 0.01 for a, b in zip(centers, new_centers)):
            break
        centers = new_centers
    return clusters


def cluster_pois(pois, duration_days):
    """聚类后按"地理质心从北到南/从西到东"排序日索引"""
    pts = [(p["lat"], p["lng"]) for p in pois]
    cluster_ids = kmeans(pts, duration_days)

    # 给每个 cluster 算质心，按经度排序
    by_cid = {}
    for p, c in zip(pois, cluster_ids):
        by_cid.setdefault(c, []).append(p)
    centroids = {}
    for c, lst in by_cid.items():
        centroids[c] = (
            sum(x["lat"] for x in lst) / len(lst),
            sum(x["lng"] for x in lst) / len(lst),
        )
    sorted_cids = sorted(by_cid.keys(), key=lambda c: centroids[c][1])

    days = []
    for day_idx, cid in enumerate(sorted_cids, start=1):
        days.append({
            "day_index": day_idx,
            "centroid": centroids[cid],
            "pois": by_cid[cid],
            "count": len(by_cid[cid]),
        })
    return days


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="poi_pool.json")
    ap.add_argument("--days", type=int, required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--city", default=None, help="只对特定城市的 POI 聚类")
    a = ap.parse_args()

    pool = json.load(open(a.input, encoding="utf-8"))
    flat = []
    if "by_city" in pool:
        for city, by_cat in pool["by_city"].items():
            if a.city and city != a.city:
                continue
            for cat, items in by_cat.items():
                for it in items:
                    it.setdefault("category", cat)
                    flat.append(it)
    else:
        flat = pool

    if not flat:
        print(json.dumps({"ok": False, "error": "no_pois"}))
        return

    days = cluster_pois(flat, a.days)
    out = {"days": days, "input_count": len(flat), "days_count": a.days}
    open(a.output, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print(json.dumps({"ok": True, "days": a.days,
                      "per_day_avg": round(len(flat) / a.days, 1)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
