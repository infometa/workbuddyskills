#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_input.py —— 知识框架梳理 Skill · 输入闸门(v0.2.0)

功能:
  - 读取 input.json(course_topic + material_files + context + preferences)
  - 校验输入合法性(必填项 / 类型 / 取值范围)
  - 判定生成模式 mode:
      topic_only      —— 仅 course_topic,无 material_files
      material_first  —— 有 material_files,无 / 弱 course_topic
      hybrid          —— 两者都有
  - 判定深度档位 depth_used(基于 context 字段 + preferences.depth_hint):
      ["skim"]                          —— 默认(context 全空)
      ["skim", "guided"]                —— focus_topics / learning_goal / user_level 任一非空
      ["skim", "guided", "deep"]        —— deep_explain == true 或 depth_hint == "force_deep"
  - 输出 build_plan.json:给 Agent 看的执行计划(mode / depth / warnings / next_step_for_llm)

用法:
  python3 scripts/validate_input.py --input input.json --out build_plan.json --pretty
  python3 scripts/validate_input.py --input input.json    # stdout 输出 build_plan

退出码:
  0  输入合法
  1  参数错误 / 文件不存在
  2  输入非法(course_topic 与 material_files 都为空 / 字段类型错误等)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "0.5.0"

VALID_DEPTH_HINTS = {"auto", "skim_only", "force_skim", "force_guided", "force_deep"}
VALID_DEP_STRATEGIES = {"off", "conservative", "aggressive"}
VALID_LANGUAGES = {"zh", "en", "bilingual"}
VALID_USER_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_OUTPUT_FORMATS = {"markdown", "markmap", "mermaid", "opml"}

CONSTRAINTS = {
    "max_levels": 5,
    "max_total_nodes": 100,
    "max_focus_topics": 5,
    "max_recommended_questions": 5,
}


def detect_mode(course_topic: str, material_files: list) -> str:
    has_topic = bool((course_topic or "").strip())
    has_material = bool(material_files)
    if has_topic and not has_material:
        return "topic_only"
    if has_material and not has_topic:
        return "material_first"
    if has_topic and has_material:
        return "hybrid"
    return "invalid"


def detect_depth(context: dict, depth_hint: str) -> tuple[list[str], str]:
    """返回 (depth_used, decision_reason)。"""
    if depth_hint in ("skim_only", "force_skim"):
        return ["skim"], f"depth_hint == {depth_hint},强制单档"
    if depth_hint == "force_deep":
        return ["skim", "guided", "deep"], "depth_hint == force_deep,强制三档全开"

    has_focus = bool(context.get("focus_topics"))
    has_goal = bool((context.get("learning_goal") or "").strip())
    has_level = bool(context.get("user_level"))
    has_deep = bool(context.get("deep_explain"))

    if has_deep or depth_hint == "force_guided":
        if has_deep:
            return ["skim", "guided", "deep"], "context.deep_explain == true,启用三档"
        return ["skim", "guided"], "depth_hint == force_guided"

    if has_focus or has_goal or has_level:
        triggers = []
        if has_focus:
            triggers.append(f"focus_topics({len(context['focus_topics'])} 项)")
        if has_goal:
            triggers.append("learning_goal")
        if has_level:
            triggers.append(f"user_level={context['user_level']}")
        return ["skim", "guided"], f"context 提供 {' / '.join(triggers)} → 升档 guided"

    return ["skim"], "context 全空 + depth_hint=auto → 默认 skim 单档"


def validate_input(data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return False, ["input.json 顶层必须是 object"]

    course_topic = data.get("course_topic", "")
    material_files = data.get("material_files", [])
    context = data.get("context") or {}
    prefs = data.get("preferences") or {}

    if not isinstance(course_topic, str):
        errors.append("course_topic 必须是 string")
    if not isinstance(material_files, list):
        errors.append("material_files 必须是 array")
    if not isinstance(context, dict):
        errors.append("context 必须是 object")
    if not isinstance(prefs, dict):
        errors.append("preferences 必须是 object")

    if not (course_topic or material_files):
        errors.append("course_topic 与 material_files 不可同时为空(SKILL.md Step 0)")

    depth_hint = prefs.get("depth_hint", "auto")
    if depth_hint not in VALID_DEPTH_HINTS:
        errors.append(f"preferences.depth_hint 非法: {depth_hint!r},允许 {sorted(VALID_DEPTH_HINTS)}")

    dep_strategy = prefs.get("concept_dependency_strategy", "off")
    if dep_strategy not in VALID_DEP_STRATEGIES:
        errors.append(f"preferences.concept_dependency_strategy 非法: {dep_strategy!r}")

    lang = prefs.get("language", "zh")
    if lang not in VALID_LANGUAGES:
        errors.append(f"preferences.language 非法: {lang!r},允许 {sorted(VALID_LANGUAGES)}")

    if "user_level" in context and context["user_level"] not in VALID_USER_LEVELS:
        errors.append(f"context.user_level 非法: {context['user_level']!r}")

    focus = context.get("focus_topics") or []
    if focus and len(focus) > CONSTRAINTS["max_focus_topics"]:
        errors.append(f"context.focus_topics 上限 {CONSTRAINTS['max_focus_topics']},当前 {len(focus)}")

    fmts = prefs.get("output_formats", ["markdown", "markmap", "mermaid", "opml"])
    if not isinstance(fmts, list) or any(f not in VALID_OUTPUT_FORMATS for f in fmts):
        errors.append(f"preferences.output_formats 含非法值;允许 {sorted(VALID_OUTPUT_FORMATS)}")

    max_levels = prefs.get("max_levels", CONSTRAINTS["max_levels"])
    if not isinstance(max_levels, int) or not (1 <= max_levels <= CONSTRAINTS["max_levels"]):
        errors.append(f"preferences.max_levels 必须是 1-{CONSTRAINTS['max_levels']} 的整数")

    return len(errors) == 0, errors


def build_plan(data: dict) -> dict:
    course_topic = data.get("course_topic", "")
    material_files = data.get("material_files", [])
    context = data.get("context") or {}
    prefs = data.get("preferences") or {}

    mode = detect_mode(course_topic, material_files)
    depth_used, depth_reason = detect_depth(context, prefs.get("depth_hint", "auto"))

    warnings: list[dict] = []
    if mode == "topic_only":
        warnings.append({
            "level": "high",
            "code": "TOPIC_ONLY_HALLUCINATION_RISK",
            "message": "本框架完全为 AI 推断,所有节点 evidence_source = ai_inference。强烈建议用户提供 material_files(教材目录 / 笔记)做交叉验证。",
            "ui_hint": "顶部 ⚠️ banner",
        })

    fmts = prefs.get("output_formats", ["markdown", "markmap", "mermaid", "opml"])
    max_levels = prefs.get("max_levels", CONSTRAINTS["max_levels"])

    next_steps_by_depth = {
        ("skim",): "生成 framework_tree(3-5 层骨架 + 每层 ≤ 7 子节点 + 总节点 ≤ 100)+ recommended_questions(3 条)",
        ("skim", "guided"): "生成 framework_tree + 选 5-10 个高 ROI 节点写 200-500 字讲解(写入 node_explanations[])+ recommended_questions(3 条)",
        ("skim", "guided", "deep"): "生成 framework_tree + 全叶子节点 200-500 字讲解 + 易混点 + 例题(写入 node_explanations[])+ recommended_questions(3 条)",
    }
    next_step = next_steps_by_depth.get(tuple(depth_used), "未匹配的深度组合,见 SKILL.md")

    return {
        "validator_version": SCRIPT_VERSION,
        "validated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_valid": True,
        "mode": mode,
        "mode_reason": {
            "topic_only": "course_topic 非空 + material_files 为空",
            "material_first": "material_files 非空 + course_topic 为空 / 弱",
            "hybrid": "course_topic 与 material_files 都非空",
        }.get(mode, "无效输入"),
        "depth_used": depth_used,
        "depth_decision_reason": depth_reason,
        "warnings": warnings,
        "constraints": {**CONSTRAINTS, "max_levels_effective": max_levels},
        "preferences_resolved": {
            "language": prefs.get("language", "zh"),
            "concept_dependency_strategy": prefs.get("concept_dependency_strategy", "off"),
            "output_formats": fmts,
        },
        "next_step_for_llm": next_step,
        "audit_trail": {
            "course_topic_present": bool(course_topic),
            "material_files_count": len(material_files),
            "context_fields_present": [k for k, v in context.items() if v not in (None, "", [], {})],
            "depth_hint": prefs.get("depth_hint", "auto"),
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description="知识框架梳理 Skill 输入闸门")
    p.add_argument("--input", required=True, help="input.json 路径")
    p.add_argument("--out", help="build_plan.json 输出路径(缺省写 stdout)")
    p.add_argument("--pretty", action="store_true", help="JSON indent=2")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[validate_input] 错误: input 文件不存在 {in_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[validate_input] 错误: input.json 解析失败: {e}", file=sys.stderr)
        return 1

    ok, errors = validate_input(data)
    if not ok:
        print(f"[validate_input] 输入非法:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        invalid_plan = {
            "validator_version": SCRIPT_VERSION,
            "input_valid": False,
            "errors": errors,
        }
        out_text = json.dumps(invalid_plan, ensure_ascii=False, indent=2 if args.pretty else None)
        if args.out:
            Path(args.out).write_text(out_text + "\n", encoding="utf-8")
        else:
            print(out_text)
        return 2

    plan = build_plan(data)
    out_text = json.dumps(plan, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.out:
        Path(args.out).write_text(out_text + "\n", encoding="utf-8")
        print(f"[validate_input] ✓ 通过 · mode={plan['mode']} · depth={plan['depth_used']} · → {args.out}", file=sys.stderr)
    else:
        print(out_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
