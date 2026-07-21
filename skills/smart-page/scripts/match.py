#!/usr/bin/env python3
"""
match.py · tencent-smart-page 意图路由匹配器（COS 远端模板版）

三层正交：场景 × 叙事范式 × 设计皮肤
- 输入：answers（scene / sub_intent / audience / tone / skin_pref / content / theme
        / narrative · 用户手选叙事 / auto_pick_narrative · "AI 全部替我选"开关）
- 输出：Top N 叙事模板组合（scene × narrative × 推荐 skin），
        预览图字段 `previews` / `full_previews` 统一为 **COS 绝对 URL**

打分与挑选机制：
  L1 场景兜底     answers.scene 缺失/未知时，用 theme+content+sub_intent 命中
                  scenes[*].intentTags 估算最佳场景
  L2 叙事打分     按 NARRATIVE_HINTS 关键词命中数 ×2 累加；
                  +0.5 加权 scene_def.defaultNarrative；
                  若 answers.narrative 显式指定，+100 拉到第一
  L3 皮肤挑选     pick_skins_for() 输出每个 (scene, narrative) 的 ≤3 套皮肤候选：
                  · narrative=="magazine"     → 强制走杂志深刊皮肤
                  · skin_pref/tone == tencent → 腾讯系皮肤（按场景过滤）
                  · 否则                       → tone 偏好 + scene 默认 + _index.json 顺序补齐

同分时按叙事在 SCENE_NARRATIVES（或 _index.json.scenes[*].narratives）里的顺序。

Usage:
    python3 match.py --answers answers.json [--top 3]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import template_source  # noqa: E402


# ---- 叙事关键词推荐（按场景分组列出每个 narrative 的命中关键词）----
NARRATIVE_HINTS: Dict[str, List[str]] = {
    # proposal
    "pyramid":      ["立项", "申请", "方案", "对比", "推荐", "决策", "批准"],
    "scqa":         ["问题", "现状", "改变", "转型", "不得不", "冲突", "挑战"],
    "blm":          ["战略", "规划", "长期", "愿景", "3年", "五年", "3-5年", "顶层"],
    # sync
    "prep":         ["周报", "双周报", "进展", "常规", "进度"],
    "star":         ["复盘", "战役", "项目收尾", "行动", "里程碑"],
    "okr":          ["okr", "目标", "kr", "季度", "对齐"],
    # insight
    "pyramid-data": ["kpi", "dau", "mau", "同步", "大盘", "dashboard", "概览"],
    "attribution":  ["下跌", "上涨", "为什么", "归因", "波动", "异常", "根因"],
    "contrast":     ["a/b", "ab", "对比", "同比", "环比", "版本", "实验"],
    # share
    "story-arc":    ["故事", "理念", "起源", "缘起", "产品理念", "长文"],
    "qa-driven":    ["faq", "问答", "培训", "常见问题", "答疑"],
    "magazine":     ["杂志", "深度", "长文", "沉浸", "阅读"],
}

# 每场景可选的三个叙事
SCENE_NARRATIVES: Dict[str, List[str]] = {
    "proposal": ["pyramid", "scqa", "blm"],
    "sync":     ["prep", "star", "okr"],
    "insight":  ["pyramid-data", "attribution", "contrast"],
    "share":    ["story-arc", "qa-driven", "magazine"],
}

# 皮肤：腾讯系优先；其他按气质
TONE_TO_SKIN: Dict[str, str] = {
    "precise":        "stillwater",
    "institutional":  "monolith",
    "warm":           "letterpad",
    "narrative":      "hearth",
    "elegant":        "prism",
    "data":           "pulse",
    "tencent":        "tencent-blue",
    "magazine":       "indigo-porcelain",
}

# 场景默认皮肤（fallback 兜底）：当 tone/skin_pref 都没命中时，
# pick_skins_for() 会用这里的值作为该场景的默认皮肤先放进候选。
SCENE_DEFAULT_SKIN: Dict[str, str] = {
    "proposal": "stillwater",
    "sync":     "stillwater",
    "insight":  "pulse",
    "share":    "letterpad",
}

# 用户气质偏好选"腾讯"时的候选池（按 _index.json.skins[*].scenes 过滤后取前 3 个）
TENCENT_SKINS = ["tencent-blue", "stillwater", "prism"]

# magazine 叙事专用皮肤：narrative=="magazine" 时强制走这些杂志深读皮肤，覆盖其他规则
MAGAZINE_ONLY_SKINS = ["indigo-porcelain", "ink-press", "forest-press", "kraft-press", "dune-press"]


def _tokenize(text: str) -> str:
    """返回小写连续文本，用于简单子串匹配"""
    return text.lower()


def load_index() -> dict:
    try:
        return template_source.load_index()
    except Exception as e:
        print(f"Error: fetch _index.json failed: {e}", file=sys.stderr)
        sys.exit(1)


def score_narrative(narr_id: str, text: str) -> Tuple[float, List[str]]:
    """对某个叙事，按关键词命中给分"""
    text_l = _tokenize(text)
    hits = []
    score = 0.0
    for kw in NARRATIVE_HINTS.get(narr_id, []):
        if kw.lower() in text_l:
            score += 2.0
            hits.append(kw)
    return score, hits


def pick_skins_for(scene: str, narrative: str, tone: str, skin_pref: str, index: dict) -> List[str]:
    """为某个 (scene, narrative) 组合挑选最多 3 套推荐皮肤（顺序即推荐优先级）。"""
    skins_def = index.get("skins", {})

    # 1) magazine 叙事：强制走杂志深刊皮肤池（覆盖 tone / skin_pref）
    if narrative == "magazine":
        return MAGAZINE_ONLY_SKINS[:3]

    # 2) 用户明确选了"腾讯系"：按 scene 过滤腾讯系候选池
    if skin_pref == "tencent" or tone == "tencent":
        return [s for s in TENCENT_SKINS if scene in skins_def.get(s, {}).get("scenes", [])][:3] or ["tencent-blue"]

    # 3) tone 命中的皮肤优先（需通过 scene 白名单）
    candidates = []
    tone_preferred = TONE_TO_SKIN.get(tone, "") if tone else ""
    if tone_preferred and scene in skins_def.get(tone_preferred, {}).get("scenes", []):
        candidates.append(tone_preferred)

    # 4) 加入场景默认皮肤兜底
    default_skin = SCENE_DEFAULT_SKIN.get(scene, "stillwater")
    if default_skin not in candidates:
        candidates.append(default_skin)

    # 5) 仍不足 3 个时，从 _index.json.skins 顺序遍历补齐（跳过 magazineOnly 与已选）
    for sid, meta in skins_def.items():
        if sid in candidates:
            continue
        if meta.get("magazineOnly"):
            continue
        if scene in meta.get("scenes", []):
            candidates.append(sid)
        if len(candidates) >= 3:
            break

    return candidates[:3]


def build_preview_paths(scene: str, narrative: str, skin: str) -> Dict[str, str]:
    """
    返回 (scene, narrative, skin) 对应的预览图 COS 绝对 URL。

    约定：
      - 缩略图：scenes/{scene}/{narrative}/preview/{skin}.png
      - 长图：  scenes/{scene}/{narrative}/preview/{skin}-full.png

    若远端对应文件缺失，前端 <img onerror> 会自动隐藏/降级，本函数不再做 fs 扫描降级。
    """
    base_rel = f"scenes/{scene}/{narrative}/preview"
    return {
        "thumbnail": template_source.cos_url(f"{base_rel}/{skin}.png"),
        "fullPreview": template_source.cos_url(f"{base_rel}/{skin}-full.png"),
    }


def match(answers: dict, top: int = 3) -> dict:
    index = load_index()
    scenes_all = {s["id"]: s for s in index.get("scenes", [])}
    narratives_def = index.get("narratives", {})
    skins_def = index.get("skins", {})

    # --- 解析输入 ---
    scene = answers.get("scene", "")
    sub_intent = answers.get("sub_intent", "")  # 细分意图（如 "new-project" / "retro" / ...）
    tone = answers.get("tone", "") or answers.get("mood", "")
    skin_pref = answers.get("skin_pref", "")    # 气质偏好开关，目前主要用于强制腾讯系
    content = answers.get("content", "")
    theme = answers.get("theme", "")
    auto_pick_narrative = bool(answers.get("auto_pick_narrative", False))
    picked_narrative = answers.get("narrative", "")  # 用户手选的叙事，命中后直接置顶

    # --- 场景兜底 ---
    if scene not in scenes_all:
        # 用内容 + theme 推断
        text = f"{theme} {content} {sub_intent}".lower()
        best_scene = "sync"
        best_score = -1.0
        for sid, sdef in scenes_all.items():
            score = 0.0
            for tag in sdef.get("intentTags", []):
                if tag.lower() in text:
                    score += 1.0
            if score > best_score:
                best_score = score
                best_scene = sid
        scene = best_scene

    scene_def = scenes_all[scene]
    narratives_in_scene = scene_def.get("narratives", SCENE_NARRATIVES.get(scene, []))

    # --- 打分每个叙事 ---
    text_for_match = f"{theme} {content} {sub_intent}"
    scored: List[Tuple[str, float, List[str]]] = []
    for narr_id in narratives_in_scene:
        s, hits = score_narrative(narr_id, text_for_match)
        # 该场景的默认叙事 +0.5：在打平局时把它推到前面，避免全 0 时顺序乱跳
        if narr_id == scene_def.get("defaultNarrative"):
            s += 0.5
        # 用户显式手选的叙事 +100：等价于强制置顶
        if picked_narrative == narr_id:
            s += 100.0
        scored.append((narr_id, s, hits))

    scored.sort(key=lambda x: -x[1])
    top_narratives = scored[: max(top, 3)]

    # --- 组装候选模板卡片 ---
    cards = []
    for narr_id, ns, hits in top_narratives[:top]:
        narr_meta = narratives_def.get(narr_id, {})
        skins = pick_skins_for(scene, narr_id, tone, skin_pref, index)
        default_skin = skins[0] if skins else SCENE_DEFAULT_SKIN.get(scene, "stillwater")

        # 为每个皮肤组装预览路径（一次调用同时获取 thumbnail 和 fullPreview）
        preview_data = {sid: build_preview_paths(scene, narr_id, sid) for sid in skins}
        previews = {sid: v["thumbnail"] for sid, v in preview_data.items()}
        full_previews = {sid: v["fullPreview"] for sid, v in preview_data.items()}

        cards.append({
            "scene": scene,
            "scene_name": scene_def.get("name", scene),
            "narrative": narr_id,
            "narrative_name": narr_meta.get("name", narr_id),
            "intent": narr_meta.get("intent", ""),
            "recommended_skin": default_skin,
            "available_skins": skins,
            "skin_labels": {sid: f"{skins_def.get(sid, {}).get('cn', sid)} · {skins_def.get(sid, {}).get('mood', '')}" for sid in skins},
            "skin_accents": {sid: skins_def.get(sid, {}).get("accent", "#5E6AD2") for sid in skins},
            "previews": previews,
            "full_previews": full_previews,
            "default_thumbnail": previews.get(default_skin, ""),
            "default_full_preview": full_previews.get(default_skin, ""),
            "score": round(ns, 2),
            "hits": hits,
        })

    return {
        "scene": scene,
        "scene_name": scene_def.get("name", scene),
        "auto_pick_narrative": auto_pick_narrative,
        "top": cards,
        "answers": answers,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="意图路由匹配器（COS 远端模板版）")
    p.add_argument("--answers", help="answers.json 路径")
    p.add_argument("--top", type=int, default=3)
    args = p.parse_args()

    if args.answers:
        ans = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    else:
        print("Error: --answers is required", file=sys.stderr)
        return 1

    result = match(ans, top=args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
