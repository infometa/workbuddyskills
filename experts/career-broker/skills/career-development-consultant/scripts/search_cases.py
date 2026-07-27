#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_cases.py  v2.0
==================================================
按 5 轴标签（stage / event / scene / persona / span）在新案例库中召回案例。
读取 skills/career-development-consultant/references/cases/all_cases.json（受控词表见 tag_definitions.md）。

设计原则（详见 cases/README.md §召回逻辑）：
  - 多轴交集召回，精度从高到低降级
  - 永远给出兜底召回（不允许"空召回"——除非库为空）
  - 输出脱敏：默认隐藏真实代号（code_name），只输出 case_id

调用：
  # 三轴交集（最精准）
  python search_cases.py --stage 3-5年瓶颈期 --scene 身份焦虑 --persona 🌱开放型

  # 双轴交集
  python search_cases.py --scene 路径选择 --persona 🔍挑剔型

  # 单轴
  python search_cases.py --event "跨BG活水"

  # 多个标签同轴（OR 关系）
  python search_cases.py --scene "身份焦虑,路径选择" --top-k 3

  # 输出真实代号（仅用于调试，生产环境别用）
  python search_cases.py --scene 路径选择 --reveal-code-name
"""
import argparse
import json
import sys
from pathlib import Path

# ----------------------------------------------------------------
# 数据加载
# ----------------------------------------------------------------
CASES_FILE = Path(__file__).resolve().parent.parent / "references" / "cases" / "all_cases.json"


def load_cases() -> list:
    """加载案例库；自动过滤标记为低质量的案例（_quality_note 中含'建议暂存不入库'）"""
    if not CASES_FILE.exists():
        print(json.dumps({"ok": False, "error": f"case file not found: {CASES_FILE}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    raw = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    cases = raw.get("cases", [])

    # 过滤明确标注"建议暂存不入库"的案例
    filtered = []
    for c in cases:
        note = c.get("_quality_note", "") or ""
        if "建议暂存不入库" in note:
            continue
        filtered.append(c)
    return filtered


# ----------------------------------------------------------------
# 召回逻辑
# ----------------------------------------------------------------
def case_matches_axis(case: dict, axis_field: str, query_tags: list) -> int:
    """返回 case 在某轴上命中查询标签的数量（0 = 没命中）"""
    if not query_tags:
        return 0
    case_tags = set(case.get(axis_field, []))
    return len(set(query_tags) & case_tags)


def recall_with_precision(
    cases: list,
    stage: list,
    event: list,
    scene: list,
    persona: list,
    span: list,
) -> tuple:
    """
    按精度从高到低召回，返回 (matched_cases, precision_level, hint)

    精度 1: stage + scene + persona 三轴全交集（每轴至少命中 1）
    精度 2: scene + persona 双轴交集
    精度 3: event + persona 双轴交集
    精度 4: scene 单轴
    精度 5: 全库（按 summary 长度兜底，不留空）
    """

    # —— 精度 1：三轴交集 ——
    if stage and scene and persona:
        hits = [
            c for c in cases
            if case_matches_axis(c, "stage_tags", stage)
            and case_matches_axis(c, "scene_tags", scene)
            and case_matches_axis(c, "persona_tags", persona)
        ]
        if hits:
            return hits, 1, "三轴精确命中（stage + scene + persona）"

    # —— 精度 2：scene + persona ——
    if scene and persona:
        hits = [
            c for c in cases
            if case_matches_axis(c, "scene_tags", scene)
            and case_matches_axis(c, "persona_tags", persona)
        ]
        if hits:
            return hits, 2, "双轴命中（scene + persona）"

    # —— 精度 3：event + persona ——
    if event and persona:
        hits = [
            c for c in cases
            if case_matches_axis(c, "event_tags", event)
            and case_matches_axis(c, "persona_tags", persona)
        ]
        if hits:
            return hits, 3, "双轴命中（event + persona）"

    # —— 精度 4：scene 单轴 ——
    if scene:
        hits = [c for c in cases if case_matches_axis(c, "scene_tags", scene)]
        if hits:
            return hits, 4, "单轴命中（scene）"

    # —— 精度 4 备选：event 单轴 ——
    if event:
        hits = [c for c in cases if case_matches_axis(c, "event_tags", event)]
        if hits:
            return hits, 4, "单轴命中（event）"

    # —— 精度 4 备选：stage 单轴 ——
    if stage:
        hits = [c for c in cases if case_matches_axis(c, "stage_tags", stage)]
        if hits:
            return hits, 4, "单轴命中（stage）"

    # —— 精度 4 备选：span 单轴 ——
    if span:
        hits = [c for c in cases if case_matches_axis(c, "span_tags", span)]
        if hits:
            return hits, 4, "单轴命中（span）"

    # —— 精度 4 备选：persona 单轴 ——
    if persona:
        hits = [c for c in cases if case_matches_axis(c, "persona_tags", persona)]
        if hits:
            return hits, 4, "单轴命中（persona）"

    # —— 精度 5：兜底（永远不空）——
    return cases, 5, "无标签命中，全库兜底（按案例顺序返回）"


def rank_within_precision(cases: list, all_query: list) -> list:
    """同精度内，按总命中标签数排序——命中越多越靠前"""

    def total_hits(c):
        h = 0
        h += case_matches_axis(c, "stage_tags", all_query.get("stage", []))
        h += case_matches_axis(c, "event_tags", all_query.get("event", []))
        h += case_matches_axis(c, "scene_tags", all_query.get("scene", []))
        h += case_matches_axis(c, "persona_tags", all_query.get("persona", []))
        h += case_matches_axis(c, "span_tags", all_query.get("span", []))
        return h

    return sorted(cases, key=lambda c: -total_hits(c))


# ----------------------------------------------------------------
# 输出脱敏
# ----------------------------------------------------------------
def desensitize(case: dict, reveal_code_name: bool = False) -> dict:
    """
    输出前脱敏：
      - 默认移除 code_name（真实姓名），只保留 case_id
      - reveal_code_name=True 时保留（仅供调试）
      - 永远移除内部维护字段（_quality_note 等）
    """
    out = {k: v for k, v in case.items() if not k.startswith("_")}
    if not reveal_code_name:
        out.pop("code_name", None)
    return out


# ----------------------------------------------------------------
# 主入口
# ----------------------------------------------------------------
def parse_csv_arg(s: str) -> list:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(
        description="按 5 轴标签召回案例。详见 cases/tag_definitions.md。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--stage", default="", help="阶段轴（多个用逗号分隔），如：3-5年瓶颈期,5-10年中坚期")
    ap.add_argument("--event", default="", help="事件轴，如：业务收缩,跨BG活水")
    ap.add_argument("--scene", default="", help="场景轴（5维度），如：身份焦虑,路径选择")
    ap.add_argument("--persona", default="", help="画像轴，如：🌱开放型")
    ap.add_argument("--span", default="", help="跨度轴，如：跨BG跨岗位")
    ap.add_argument("--top-k", type=int, default=2, help="返回案例数上限（默认 2）")
    ap.add_argument("--reveal-code-name", action="store_true", help="保留 code_name（调试用，生产关掉）")

    # —— 兼容老版调用（旧的 --tags / --span / --tenure）——
    ap.add_argument("--tags", default="", help="[deprecated] 旧版自由文本标签，将映射到 scene/event")
    ap.add_argument("--tenure", default="", help="[deprecated] 旧版司龄阶段，将映射到 stage")

    args = ap.parse_args()

    stage = parse_csv_arg(args.stage)
    event = parse_csv_arg(args.event)
    scene = parse_csv_arg(args.scene)
    persona = parse_csv_arg(args.persona)
    span = parse_csv_arg(args.span)

    # 兼容老调用：--tags / --tenure 自动并入 scene / stage
    legacy_tags = parse_csv_arg(args.tags)
    if legacy_tags:
        scene.extend(legacy_tags)
        event.extend(legacy_tags)  # 老 tags 既可能是场景也可能是事件，两边都尝试
    if args.tenure:
        stage.append(args.tenure)

    cases = load_cases()
    matched, precision, hint = recall_with_precision(
        cases, stage=stage, event=event, scene=scene, persona=persona, span=span
    )

    all_query = {"stage": stage, "event": event, "scene": scene, "persona": persona, "span": span}
    ranked = rank_within_precision(matched, all_query)
    top_k = ranked[: args.top_k]

    results = [
        {
            "precision": precision,
            "case": desensitize(c, reveal_code_name=args.reveal_code_name),
        }
        for c in top_k
    ]

    print(
        json.dumps(
            {
                "ok": True,
                "n_total_in_lib": len(cases),
                "n_matched": len(matched),
                "n_returned": len(results),
                "precision_level": precision,
                "precision_hint": hint,
                "query": {k: v for k, v in all_query.items() if v},
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
