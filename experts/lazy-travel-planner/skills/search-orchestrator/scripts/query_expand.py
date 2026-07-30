#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
query_expand.py · 查询矩阵生成器
按 query_templates.json 的模板填空，结合候选地点 × user_profile × 季节 × 时长
生成 15-20 条查询关键词。

90% 走规则模板，10% 留给上层 LLM 创造性扩展（本脚本只产规则部分，不调用 LLM）。
"""
import json, datetime, pathlib

THIS_DIR = pathlib.Path(__file__).parent
TEMPLATES_PATH = THIS_DIR / "query_templates.json"


def load_templates():
    with open(TEMPLATES_PATH, encoding="utf-8") as f:
        return json.load(f)


def expand_queries(candidates: list, domain: str, profile: dict,
                   intent: str, season: str = None, duration: str = None) -> list:
    """生成查询矩阵。

    candidates: geo_fanout 返回的候选地点列表
    domain:     destination / poi / accommodation / risk
    profile:    user_profile.json 字典
    intent:     原始意图，用作"通用层"查询保留
    season:     可选，覆盖默认季节
    duration:   可选，影响 {duration}日游 模板
    """
    tpl = load_templates()
    queries = set()

    # 通用层：保留用户原始意图
    queries.add(intent.strip())

    # 季节 / 月份
    month = datetime.date.today().strftime("%m")
    season_label = season or tpl["season_map"].get(month, "")

    # 候选地点层
    for cand in candidates[:8]:  # 取前 8 个候选避免查询爆炸
        loc = cand["name"]
        for raw_template in tpl.get(domain, tpl["destination"]):
            q = raw_template.format(
                location=loc,
                season=season_label,
                duration=duration or "3",
                category="美食",                          # poi domain 默认；上层可重复扩展
                tier_label=tpl["tier_label_map"].get(profile.get("basic", {}).get("budget_tier") or "standard", "性价比"),
                area="",                                  # accommodation 用，留空时模板会自然忽略
                month=month,
            ).strip()
            queries.add(q)

    # 偏好附加层
    addons = tpl.get("preference_addons", {})
    physical = profile.get("physical", {}) or {}
    constraints = profile.get("constraints", {}) or {}
    tastes = profile.get("tastes", {}) or {}

    flag_to_key = []
    if physical.get("no_long_walk"):
        flag_to_key.append("no_long_walk")
    if physical.get("fear_of_heights"):
        flag_to_key.append("fear_of_heights")
    if constraints.get("must_have_starbucks_or_equivalent"):
        flag_to_key.append("must_have_starbucks_or_equivalent")
    if "photo" in (tastes.get("scene_likes") or []):
        flag_to_key.append("scene_likes_photo")
    if "food" in (tastes.get("scene_likes") or []):
        flag_to_key.append("scene_likes_food")
    if "crowded_check_in_spot" in (tastes.get("scene_dislikes") or []):
        flag_to_key.append("scene_dislikes_crowded")

    for cand in candidates[:5]:
        loc = cand["name"]
        for flag in flag_to_key:
            for raw in addons.get(flag, []):
                queries.add(raw.format(location=loc).strip())

    # 上限保护：>20 条裁剪到 20（保留通用层 + 候选层前 N + 偏好层前 N）
    final = list(queries)
    if len(final) > 20:
        final = final[:20]
    return final


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--domain", default="destination")
    ap.add_argument("--intent", required=True)
    a = ap.parse_args()
    profile = json.load(open(a.profile, encoding="utf-8"))
    candidates = json.load(open(a.candidates, encoding="utf-8"))
    qs = expand_queries(candidates, a.domain, profile, a.intent)
    print(json.dumps(qs, ensure_ascii=False, indent=2))
