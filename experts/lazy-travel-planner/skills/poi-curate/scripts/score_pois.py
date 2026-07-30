#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_pois.py · POI 多维加权评分
读 data/scoring_rules.json + user_profile.json + raw_pois.json
输出 poi_pool.json（按城市 × 类目分组，每个 POI 含 final_score）
"""
import argparse, json, math, pathlib, sys, re

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
RULES_PATH = ROOT / "data" / "scoring_rules.json"
PROFILE_PATH = ROOT / "data" / "user_profile.json"


def _norm_amap(rating):
    if rating is None:
        return 0
    try:
        r = float(rating)
    except (TypeError, ValueError):
        return 0
    return max(0.0, min(1.0, (r - 3.0) / 2.0)) if r >= 3.0 else 0.0


def _norm_xhs_buzz(notes, likes):
    n = float(notes or 0)
    l = float(likes or 0)
    raw = math.log10(n + l / 100 + 1) / 4.0
    return max(0.0, min(1.0, raw))


def _sentiment(comments_or_text, rules):
    """正/负面词频比"""
    if not comments_or_text:
        return 0.5
    if isinstance(comments_or_text, list):
        text = " ".join(c.get("content", "") if isinstance(c, dict) else str(c)
                        for c in comments_or_text)
    else:
        text = str(comments_or_text)
    pos = sum(1 for k in rules["dimensions"]["xhs_sentiment"]["positive_keywords"] if k in text)
    neg = sum(1 for k in rules["dimensions"]["xhs_sentiment"]["negative_keywords"] if k in text)
    if pos + neg == 0:
        return 0.5
    return pos / (pos + neg)


def _user_pref_match(poi, profile, rules):
    """用户偏好匹配度 0-1"""
    score = 0.5
    history = profile.get("history", {}) or {}
    tastes = profile.get("tastes", {}) or {}

    # 拒绝过的直接 0
    if poi.get("name") in (history.get("rejected_pois") or []):
        return 0.0
    # 喜欢过的加分
    if poi.get("name") in (history.get("favorite_pois") or []):
        score = min(1.0, score + 0.4)
    # 类目偏好匹配
    cat = poi.get("category", "")
    likes = tastes.get("scene_likes") or []
    dislikes = tastes.get("scene_dislikes") or []
    for tag in likes:
        if tag in str(cat) or tag in poi.get("name", ""):
            score = min(1.0, score + 0.1)
    for tag in dislikes:
        if tag in str(cat) or tag in poi.get("name", ""):
            score = max(0.0, score - 0.2)
    return score


def _queuing(poi, profile):
    tol = (profile.get("constraints", {}) or {}).get("queuing_tolerance_min", 30)
    est = poi.get("est_queue_min", 0)
    return 1.0 if est <= tol else 0.0


def _weather_compat(poi, weather=None):
    """简化版：未传 weather 时给 0.7（中性）"""
    if not weather:
        return 0.7
    rain = weather.get("rain_prob", 0)
    cat = poi.get("category", "")
    if rain > 0.5 and any(k in str(cat) for k in ("户外", "山", "湖", "公园")):
        return 0.3
    return 0.8


def score_one(poi, profile, rules, weather=None):
    dims = rules["dimensions"]
    weighted = (
        dims["amap_rating"]["weight"]            * _norm_amap(poi.get("amap_rating") or poi.get("rating")) +
        dims["xhs_buzz"]["weight"]               * _norm_xhs_buzz(poi.get("xhs_notes"), poi.get("xhs_likes")) +
        dims["xhs_sentiment"]["weight"]          * _sentiment(poi.get("xhs_comments_text") or poi.get("xhs_comments"), rules) +
        dims["user_preference_match"]["weight"]  * _user_pref_match(poi, profile, rules) +
        dims["queuing_factor"]["weight"]         * _queuing(poi, profile) +
        dims["weather_compatibility"]["weight"]  * _weather_compat(poi, weather)
    )

    # penalties
    pen = rules["penalties"]
    history = profile.get("history", {}) or {}
    physical = profile.get("physical", {}) or {}
    tastes = profile.get("tastes", {}) or {}
    if poi.get("name") in (history.get("rejected_pois") or []):
        return -1
    if physical.get("no_high_altitude") and (poi.get("altitude_m") or 0) > 2000:
        return -1
    if physical.get("fear_of_heights"):
        height_kw = ["玻璃栈道", "悬空栈道", "蹦极", "高空缆车", "索道"]
        if any(k in poi.get("name", "") for k in height_kw):
            return -1
    if physical.get("no_long_walk") and poi.get("requires_hike_km", 0) > 3:
        weighted += pen["no_long_walk_match"] / 100  # 减分但不直接淘汰
    diet = tastes.get("religious_dietary")
    if diet and poi.get("category") == "restaurant" and not poi.get("dietary_compatible"):
        return -1

    # boosts
    bo = rules["boosts"]
    if any(t in poi.get("name", "") + str(poi.get("category", ""))
           for t in (tastes.get("scene_likes") or [])):
        weighted += bo["matches_scene_likes"] / 100
    text = poi.get("xhs_comments_text", "") or ""
    if any(k in text for k in bo.get("_local_keywords", []) or
                          ["本地人", "苍蝇馆子", "老字号", "藏在巷子里", "不踩雷"]):
        weighted += bo["is_local_recommended_not_tourist_trap"] / 100

    # category modifiers
    mods = rules.get("category_modifiers", {})
    cat_mod = mods.get(poi.get("category"))
    if cat_mod and "min_amap_rating" in cat_mod:
        if (poi.get("amap_rating") or 0) < cat_mod["min_amap_rating"]:
            return -1

    return round(max(0.0, min(1.0, weighted)), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="raw_pois.json (来自 00 编排)")
    ap.add_argument("--profile", default=str(PROFILE_PATH))
    ap.add_argument("--rules", default=str(RULES_PATH))
    ap.add_argument("--top-n", type=int, default=15)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    raw = json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))
    profile = json.loads(pathlib.Path(a.profile).read_text(encoding="utf-8"))
    rules = json.loads(pathlib.Path(a.rules).read_text(encoding="utf-8"))

    pois = raw.get("pois") if isinstance(raw, dict) else raw
    by_city = {}
    for p in pois or []:
        score = score_one(p, profile, rules)
        if score < 0:
            continue
        p["final_score"] = score
        city = p.get("city") or p.get("address", "").split("市")[0] or "未知"
        cat = p.get("category", "scenic_spot")
        by_city.setdefault(city, {}).setdefault(cat, []).append(p)

    # Top-N per category
    for city in by_city:
        for cat in by_city[city]:
            by_city[city][cat] = sorted(by_city[city][cat],
                                         key=lambda x: x["final_score"],
                                         reverse=True)[:a.top_n]

    out = {
        "by_city": by_city,
        "metadata": {
            "scoring_rules_version": rules.get("_schema_version"),
            "input_pois": len(pois or []),
            "kept_pois": sum(len(c) for city in by_city.values() for c in city.values())
        }
    }
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "kept": out["metadata"]["kept_pois"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
