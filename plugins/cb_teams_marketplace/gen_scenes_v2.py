import json
import re
import pandas as pd

XLSX = "WorkBuddy_query池_最新分类与胶囊Top4_923_1790336609267724640-latest.xlsx"

# 中文胶囊名 -> (id, unified_id, icon, mode)；顺序即 Excel 中的胶囊顺序
CAPSULE_META = {
    "创作文档": (47, 130, "documentation", "working"),
    "金融服务": (52, 135, "financial-services", "working"),
    "分析数据": (48, 131, "data-visualization", "working"),
    "制作PPT": (49, 132, "slides-creation", "working"),
    "深度研究": (50, 133, "deep-research", "working"),
    "策划方案": (51, 134, "lightbulb", "working"),
    "定时任务": (53, 136, "timer", "working"),
    "日常开发": (54, 137, "daily-development", "coding"),
    "开发网站": (55, 138, "website-development", "coding"),
    "Agent 应用": (56, 139, "agent-apps", "coding"),
    "开发 Skill": (57, 140, "skill-development", "coding"),
    "小程序": (58, 141, "mini-program", "coding"),
    "技术文档": (59, 142, "documentation-tools", "coding"),
}


def parse_plugin(v):
    """plugin 列为 JSON 片段，如 '"plugins": [...],'，解析出列表。"""
    if pd.isna(v):
        return []
    s = str(v).strip()
    m = re.match(r'"plugins":\s*(\[.*\])\s*,?\s*$', s, re.S)
    if not m:
        raise ValueError(f"无法解析 plugin 片段: {s[:60]!r}")
    return json.loads(m.group(1))


def merge_plugins(rows):
    """逐行 plugin 聚合为场景级列表：按名称去重保序，id 重编为 0..n-1。

    Excel 中每行带自己的 id（存在行内递增的枚举瑕疵，如 spglobal 7/8/9），
    scenes.json 规范是场景级 0..n-1 顺序编号，故以名称为准重新编号。
    """
    seen = {}
    for v in rows:
        for p in parse_plugin(v):
            if p["name"] not in seen:
                seen[p["name"]] = p["marketplaceName"]
    # 组内同名插件的 marketplaceName 必须一致
    for v in rows:
        for p in parse_plugin(v):
            assert seen[p["name"]] == p["marketplaceName"], p["name"]
    return [
        {"id": i, "name": n, "marketplaceName": m}
        for i, (n, m) in enumerate(seen.items())
    ]


def make_scene(name, sid, uid, icon, mode, plugins, queries, prompts):
    scene = {"id": sid, "unified_id": uid, "name": name, "icon": icon, "mode": mode}
    if mode == "working":
        scene["interactionModes"] = ["craft", "plan"]
    scene["plugins"] = plugins
    scene["prompts"] = [str(p).strip() for p in prompts]
    scene["promptTitles"] = [str(q).strip() for q in queries]
    scene["target"] = "all"
    return scene


# ---- 中文：sheet2（序号/胶囊/对应原胶囊/plugin/排序/Query/Prompt）----
zh = pd.read_excel(XLSX, sheet_name=1, header=0, engine="calamine")
zh.columns = ["no", "capsule", "orig", "plugin", "rank", "query", "prompt"]
scenes_zh = []
for capsule, g in zh.groupby("capsule", sort=False):
    g = g.sort_values("rank")
    sid, uid, icon, mode = CAPSULE_META[capsule]
    plugins = merge_plugins(g["plugin"])
    scenes_zh.append(make_scene(capsule, sid, uid, icon, mode, plugins, g["query"], g["prompt"]))

# ---- 英文：sheet3（No./Mode/Capsule/plugin/Rank/Query/Prompt），行序与中文一致 ----
en = pd.read_excel(XLSX, sheet_name=2, header=0, engine="calamine")
en.columns = ["no", "mode", "capsule", "plugin", "rank", "query", "prompt"]
mode_en = {"Work": "working", "Code": "coding"}
capsule_of_row = {i: r["capsule"] for i, r in zh.iterrows()}
scenes_en = []
for wf, g in en.groupby("capsule", sort=False):
    g = g.sort_values("rank")
    zh_capsule = capsule_of_row[g.index[0]]
    sid, uid, icon, _ = CAPSULE_META[zh_capsule]
    mode = mode_en[g["mode"].iloc[0]]
    plugins = merge_plugins(g["plugin"])
    scenes_en.append(make_scene(wf, sid, uid, icon, mode, plugins, g["query"], g["prompt"]))

for scenes, out in [(scenes_zh, "scenes-v2.json"), (scenes_en, "scenes-v2-en.json")]:
    with open(out, "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    print(f"{out}: {len(scenes)} scenes, {sum(len(s['prompts']) for s in scenes)} prompts")
