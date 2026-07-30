#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_profile.py · 增量更新 user_profile.json
模式：
  - --bootstrap：写入 BOOTSTRAP 三题答案
  - --merge:     合并对话抽取的偏好增量（来自 LLM 输出的 patch JSON）
  - --visited <city>: 标记一次出行完成，加到 history.visited_cities
  - --reject  <poi>:  把 POI 加入 rejected_pois
  - --favorite <poi>: 把 POI 加入 favorite_pois

JSON patch 格式（--merge）：
  {
    "tastes": { "food_dislikes": ["seafood"], "scene_likes": ["coffee_shop"] },
    "physical": { "no_long_walk": true },
    ...
  }
"""
import json, sys, argparse, pathlib, datetime

DEFAULT_PROFILE = (pathlib.Path(__file__).parent.parent.parent.parent
                   / "data" / "user_profile.json")


def deep_merge(base: dict, patch: dict):
    """递归合并 patch → base；list 字段做去重 union"""
    for k, v in patch.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        elif isinstance(v, list) and isinstance(base.get(k), list):
            for item in v:
                if item not in base[k]:
                    base[k].append(item)
        else:
            base[k] = v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=str(DEFAULT_PROFILE))
    ap.add_argument("--bootstrap", help="JSON 字符串，含 pace/dislikes/budget_tier 三题答案")
    ap.add_argument("--merge", help="patch JSON 文件路径")
    ap.add_argument("--visited", help="目的地名，加入 history.visited_cities")
    ap.add_argument("--reject", help="POI 名/id，加入 rejected_pois")
    ap.add_argument("--favorite", help="POI 名/id，加入 favorite_pois")
    ap.add_argument("--mark-trip", help="JSON 文件，加入 history.completed_trips")
    a = ap.parse_args()

    p = pathlib.Path(a.profile)
    if not p.exists():
        print(f"❌ profile 不存在: {p}", file=sys.stderr)
        sys.exit(3)
    data = json.loads(p.read_text(encoding="utf-8"))
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    data.setdefault("_created_at", now)
    data["_last_active"] = now

    if a.bootstrap:
        boot = json.loads(a.bootstrap)
        data.setdefault("basic", {})
        if boot.get("pace") in ("walker_intense", "normal", "relaxed"):
            data["basic"]["preferred_pace"] = boot["pace"]
        if boot.get("budget_tier") in ("economy", "standard", "premium", "luxury"):
            data["basic"]["budget_tier"] = boot["budget_tier"]
        if isinstance(boot.get("dislikes"), list):
            data.setdefault("tastes", {})
            for k in boot["dislikes"]:
                _route_dislike(data, k)

    if a.merge:
        patch = json.loads(pathlib.Path(a.merge).read_text(encoding="utf-8"))
        deep_merge(data, patch)

    if a.visited:
        data.setdefault("history", {}).setdefault("visited_cities", [])
        if a.visited not in data["history"]["visited_cities"]:
            data["history"]["visited_cities"].append(a.visited)

    if a.reject:
        data.setdefault("history", {}).setdefault("rejected_pois", [])
        if a.reject not in data["history"]["rejected_pois"]:
            data["history"]["rejected_pois"].append(a.reject)

    if a.favorite:
        data.setdefault("history", {}).setdefault("favorite_pois", [])
        if a.favorite not in data["history"]["favorite_pois"]:
            data["history"]["favorite_pois"].append(a.favorite)

    if a.mark_trip:
        trip = json.loads(pathlib.Path(a.mark_trip).read_text(encoding="utf-8"))
        data.setdefault("history", {}).setdefault("completed_trips", []).append(trip)

    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "updated_at": now}, ensure_ascii=False))


def _route_dislike(data: dict, key: str):
    """把 BOOTSTRAP Q2 的 dislike 关键词路由到合适字段"""
    food_keys = {"seafood", "spicy", "lamb", "raw_food", "innards", "halal_violation"}
    scene_keys = {"long_queue", "crowded_check_in_spot", "shopping_district",
                  "amusement_park", "museum"}
    physical_keys = {"hiking", "high_altitude", "long_walk"}
    physical_map = {"hiking": "no_long_walk", "high_altitude": "no_high_altitude",
                    "long_walk": "no_long_walk"}
    if key in food_keys:
        data["tastes"].setdefault("food_dislikes", [])
        if key not in data["tastes"]["food_dislikes"]:
            data["tastes"]["food_dislikes"].append(key)
    elif key in scene_keys:
        data["tastes"].setdefault("scene_dislikes", [])
        if key not in data["tastes"]["scene_dislikes"]:
            data["tastes"]["scene_dislikes"].append(key)
    elif key in physical_keys:
        data.setdefault("physical", {})[physical_map[key]] = True


if __name__ == "__main__":
    main()
