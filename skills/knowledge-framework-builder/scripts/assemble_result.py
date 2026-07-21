#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_result.py —— 知识框架梳理 Skill · result.json 装配器(v0.5.0)

定位:
  - LLM 已经按 SKILL.md Step 3 / 4 / 5 / 6 产出 framework_tree / node_explanations /
    concept_dependencies / recommended_questions 各 JSON 中间产物。
  - 本脚本接收 input.json + tree.json + (可选) questions / explanations / dependencies,
    自动:
    * 遍历 framework_tree 计算 tree_stats(total / leaf / max_depth / level_counts)
    * 校验约束:
        - max_total_nodes / max_levels(SKILL.md 核心原则 9)
        - guided 5-10 节点 + 200-500 字 + node_id ⊂ tree
        - deep ≤ leaf_count + 200-800 字 + 总字数 ≤ 30000
        - dependencies 边数预算 / DAG / 6 类 / from-to ∈ tree / rationale 非套话
    * 自动填补每个节点的 evidence_source(按 mode 默认值,允许 LLM 显式覆盖)
    * 计算 provenance_summary(汇总三种 evidence_source 的占比)
    * 生成 warnings(topic_only → high 级 banner;hybrid AI 占比超半 → medium;
                    deep_truncated / dependency_over_budget 等)
    * 装配完整 result.json(meta + inputs_summary + warnings + framework_tree
                            + tree_stats + node_explanations + concept_dependencies
                            + recommended_questions + provenance_summary
                            + outputs + next_step_hint)

设计原则:
  - 不调用 LLM(零依赖,标准库)
  - 校验失败 → 退出码 ≠ 0,Agent 拿到详细 error 重新生成
  - 已有声明值优先(LLM 写过的 evidence_source / is_focus 不覆盖)

用法:
  # v0.2 用法(skim 单档)
  python3 scripts/assemble_result.py \
      --input input.json --tree tree.json \
      --questions questions.json \
      --out result.json --pretty

  # v0.3 用法(skim + guided)
  python3 scripts/assemble_result.py \
      --input input.json --tree tree.json \
      --questions questions.json \
      --explanations explanations.json \
      --out result.json --pretty

  # v0.4 用法(skim + guided + deep + 概念依赖)
  python3 scripts/assemble_result.py \
      --input input.json --tree tree.json \
      --questions questions.json \
      --explanations explanations.json \
      --dependencies dependencies.json \
      --out result.json --pretty

  # 自包含 dogfood 模式(从已有 result.json 抽 framework_tree)
  python3 scripts/assemble_result.py \
      --input input.json --tree-from-result existing-result.json \
      --out result.json --pretty

退出码:
  0  装配成功
  1  参数 / 文件错误
  2  约束违反(节点数 > 100、层级超限、guided/deep/dependency 校验失败)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "0.5.0"
SKILL_VERSION = "0.5.0"

CONSTRAINTS = {
    "max_levels": 5,
    "max_total_nodes": 100,
    "max_focus_nodes": 10,
    "min_focus_nodes_guided": 5,
    "guided_word_min": 200,
    "guided_word_max": 500,
    "deep_word_min": 200,
    "deep_word_max": 800,
    "deep_total_word_max": 30000,
    "concept_dep_ratio_aggressive": 0.30,
    "concept_dep_ratio_conservative": 0.15,
}

DEFAULT_EVIDENCE_BY_MODE = {
    "topic_only": "ai_inference",
    "material_first": "user_material",
    "hybrid": "ai_inference",
}

VALID_DEP_TYPES = {
    "prerequisite",
    "generalization",
    "specialization",
    "contrast",
    "application",
    "tool",
}

# 套话黑名单(rationale 含其一即触发 warning,非阻断)
RATIONALE_CLICHE = [
    "紧密相关",
    "息息相关",
    "密切相关",
    "至关重要",
    "非常重要",
    "综上所述",
    "众所周知",
    "毫无疑问",
    "有助于",  # 可接受但需有具体后续,这里仅作提示
]


# ---------- 通用工具 ----------

def walk_tree(node: dict, level: int = 0):
    """生成器,深度优先 yield (node, level)。"""
    yield node, level
    for c in node.get("children", []) or []:
        yield from walk_tree(c, level + 1)


def collect_node_ids(root: dict) -> set[str]:
    return {n.get("id") for n, _ in walk_tree(root) if n.get("id")}


def collect_leaf_ids(root: dict) -> list[str]:
    return [n["id"] for n, _ in walk_tree(root) if not (n.get("children") or [])]


def count_chinese_chars(text: str) -> int:
    """中文按字符,英文按 word × 1.6 折算成"中文字数等价"。"""
    if not text:
        return 0
    cn = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    en_words = len(re.findall(r"[A-Za-z]+", text))
    return cn + int(round(en_words * 1.6))


# ---------- tree 统计 ----------

def compute_tree_stats(root: dict) -> dict:
    total = 0
    leaf = 0
    max_depth = 0
    level_counts: dict[int, int] = {}

    for node, lv in walk_tree(root):
        total += 1
        max_depth = max(max_depth, lv)
        level_counts[lv] = level_counts.get(lv, 0) + 1
        if not (node.get("children") or []):
            leaf += 1

    non_leaf = total - leaf
    branching = round((total - 1) / non_leaf, 2) if non_leaf else 0.0

    return {
        "total_nodes": total,
        "max_depth": max_depth,
        "max_depth_semantics": f"max_depth = 最大 level 值(从 root 的 0 起算);层数 = max_depth + 1 = {max_depth + 1} 层",
        "level_counts": {str(k): v for k, v in sorted(level_counts.items())},
        "leaf_count": leaf,
        "branching_factor_avg": branching,
    }


def fill_evidence_source(root: dict, mode: str) -> dict:
    """对没有 evidence_source 字段的节点按 mode 默认值填补。返回汇总计数。"""
    default = DEFAULT_EVIDENCE_BY_MODE.get(mode, "ai_inference")
    counts = {"user_material": 0, "ai_inference": 0, "curated_syllabus": 0}
    for node, _lv in walk_tree(root):
        es = node.get("evidence_source")
        if not es:
            node["evidence_source"] = default
            es = default
        counts[es] = counts.get(es, 0) + 1
    return counts


def check_tree_constraints(stats: dict, max_levels: int) -> list[str]:
    errors: list[str] = []
    if stats["total_nodes"] > CONSTRAINTS["max_total_nodes"]:
        errors.append(
            f"total_nodes={stats['total_nodes']} 超过上限 {CONSTRAINTS['max_total_nodes']}(SKILL.md 核心原则 9)"
        )
    levels = stats["max_depth"] + 1
    if levels > max_levels:
        errors.append(
            f"层数={levels}(max_depth+1)超过 max_levels={max_levels}"
        )
    return errors


# ---------- guided / deep explanations 校验 ----------

def validate_explanations(
    explanations: list[dict],
    tree_root: dict,
    depth_used: list[str],
) -> tuple[list[str], list[dict]]:
    """
    校验 node_explanations 数组。
    返回 (errors, warnings)。errors 触发退出码 2,warnings 写入 result.json.warnings。
    """
    errors: list[str] = []
    warnings: list[dict] = []
    if not explanations:
        return errors, warnings

    has_deep = "deep" in depth_used
    has_guided = "guided" in depth_used
    if not (has_guided or has_deep):
        errors.append(
            "提供了 node_explanations,但 depth_used 既不含 guided 也不含 deep"
        )
        return errors, warnings

    valid_ids = collect_node_ids(tree_root)
    leaf_ids = set(collect_leaf_ids(tree_root))

    # 数量校验
    if has_deep:
        # deep:覆盖叶子节点(允许子集 → 触发 DEEP_BATCH_TRUNCATED warning)
        if len(explanations) > len(leaf_ids):
            errors.append(
                f"deep 节点讲解数 {len(explanations)} 超过叶子总数 {len(leaf_ids)}"
            )
    elif has_guided:
        if not (CONSTRAINTS["min_focus_nodes_guided"] <= len(explanations) <= CONSTRAINTS["max_focus_nodes"]):
            errors.append(
                f"guided 节点讲解数={len(explanations)}, 应在 "
                f"[{CONSTRAINTS['min_focus_nodes_guided']}, {CONSTRAINTS['max_focus_nodes']}] 范围内"
            )

    # 单条 + 总字数校验
    word_min = CONSTRAINTS["deep_word_min"] if has_deep else CONSTRAINTS["guided_word_min"]
    word_max = CONSTRAINTS["deep_word_max"] if has_deep else CONSTRAINTS["guided_word_max"]

    seen_ids: set[str] = set()
    total_words = 0
    for i, exp in enumerate(explanations):
        nid = exp.get("node_id")
        if not nid:
            errors.append(f"node_explanations[{i}] 缺 node_id")
            continue
        if nid in seen_ids:
            errors.append(f"node_explanations[{i}] node_id={nid} 重复")
            continue
        seen_ids.add(nid)

        if nid not in valid_ids:
            errors.append(f"node_explanations[{i}] node_id={nid} 在 framework_tree 中不存在")
            continue

        if has_deep and nid not in leaf_ids:
            warnings.append({
                "level": "low",
                "code": "DEEP_NON_LEAF_EXPLANATION",
                "message": f"deep 模式下 {nid} 非叶子节点,通常 deep 只覆盖叶子",
                "ui_hint": "informational",
            })

        explanation = exp.get("explanation", "")
        wc = exp.get("word_count")
        if wc is None:
            wc = count_chinese_chars(explanation)
            exp["word_count"] = wc
        total_words += wc

        if not (word_min <= wc <= word_max):
            errors.append(
                f"node_explanations[{i}] node_id={nid} word_count={wc}, 应在 [{word_min}, {word_max}] 范围内"
            )

        # 三段式结构软检查(guided / deep 都要求)
        for tag in ["[定义]", "[展开]"]:
            if tag not in explanation:
                warnings.append({
                    "level": "low",
                    "code": "EXPLANATION_STRUCTURE_INCOMPLETE",
                    "message": f"{nid} 的 explanation 缺 {tag} 段(rubric 三段式建议)",
                    "ui_hint": "informational",
                })
                break

    # deep 总字数封顶
    if has_deep and total_words > CONSTRAINTS["deep_total_word_max"]:
        warnings.append({
            "level": "medium",
            "code": "DEEP_TOTAL_WORD_OVER_LIMIT",
            "message": (
                f"deep 总字数 {total_words} > {CONSTRAINTS['deep_total_word_max']}, "
                "建议分批 deep 或截断"
            ),
            "ui_hint": "顶部黄色提示",
        })

    # deep 截断 warning
    if has_deep and len(explanations) < len(leaf_ids):
        warnings.append({
            "level": "medium",
            "code": "DEEP_BATCH_TRUNCATED",
            "message": (
                f"deep 仅覆盖 {len(explanations)}/{len(leaf_ids)} 个叶子节点, "
                "建议分批 deep 或缩小 focus_topics 范围"
            ),
            "ui_hint": "顶部黄色提示",
        })

    return errors, warnings


# ---------- concept_dependencies 校验(DAG + 边预算 + 6 类) ----------

def has_cycle_directed(edges: list[tuple[str, str]], all_nodes: set[str]) -> bool:
    """Kahn 拓扑排序检测有向图环。"""
    indeg: dict[str, int] = {n: 0 for n in all_nodes}
    adj: dict[str, list[str]] = {n: [] for n in all_nodes}
    for u, v in edges:
        if u in adj and v in indeg:
            adj[u].append(v)
            indeg[v] += 1
    queue = [n for n, d in indeg.items() if d == 0]
    visited = 0
    while queue:
        u = queue.pop(0)
        visited += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return visited != len(all_nodes)


def validate_dependencies(
    deps: list[dict],
    tree_root: dict,
    strategy: str,
) -> tuple[list[str], list[dict]]:
    """
    校验 concept_dependencies。返回 (errors, warnings)。
    """
    errors: list[str] = []
    warnings: list[dict] = []
    if not deps:
        return errors, warnings

    if strategy == "off":
        errors.append("提供了 concept_dependencies 但 preferences.concept_dependency_strategy=off")
        return errors, warnings

    valid_ids = collect_node_ids(tree_root)
    total_nodes = len(valid_ids)

    ratio = (
        CONSTRAINTS["concept_dep_ratio_conservative"]
        if strategy == "conservative"
        else CONSTRAINTS["concept_dep_ratio_aggressive"]
    )
    budget = int(total_nodes * ratio)
    if len(deps) > budget:
        warnings.append({
            "level": "medium",
            "code": "DEP_OVER_BUDGET",
            "message": (
                f"概念依赖边数 {len(deps)} > 预算 {budget} "
                f"(策略 {strategy} = total_nodes × {ratio})"
            ),
            "ui_hint": "顶部黄色提示",
        })

    # 单条校验
    seen_pairs: set[tuple[str, str, str]] = set()
    prereq_edges: list[tuple[str, str]] = []
    for i, d in enumerate(deps):
        u = d.get("from")
        v = d.get("to")
        t = d.get("type")
        rationale = (d.get("rationale") or "").strip()
        conf = d.get("confidence", "medium")

        if not u or not v:
            errors.append(f"concept_dependencies[{i}] 缺 from/to")
            continue
        if u == v:
            errors.append(f"concept_dependencies[{i}] from == to ({u}) 自环禁止")
            continue
        if u not in valid_ids:
            errors.append(f"concept_dependencies[{i}] from={u} 在 framework_tree 中不存在")
            continue
        if v not in valid_ids:
            errors.append(f"concept_dependencies[{i}] to={v} 在 framework_tree 中不存在")
            continue
        if t not in VALID_DEP_TYPES:
            errors.append(
                f"concept_dependencies[{i}] type={t!r} 不在 6 类合法范围 {sorted(VALID_DEP_TYPES)}"
            )
            continue

        # contrast 双向去重:存 (min, max, contrast)
        if t == "contrast":
            key = (min(u, v), max(u, v), t)
        else:
            key = (u, v, t)
        if key in seen_pairs:
            errors.append(f"concept_dependencies[{i}] {key} 重复")
            continue
        seen_pairs.add(key)

        # rationale 非空
        if len(rationale) < 8:
            errors.append(
                f"concept_dependencies[{i}] {u}→{v}({t}) rationale 过短 (<8 字),禁止套话"
            )
            continue
        for cliche in RATIONALE_CLICHE[:3]:  # 仅最严重的几个套话作为 warning
            if cliche in rationale:
                warnings.append({
                    "level": "low",
                    "code": "DEP_RATIONALE_CLICHE",
                    "message": f"{u}→{v}({t}) rationale 含套话『{cliche}』,建议改具体",
                    "ui_hint": "informational",
                })
                break

        # conservative 策略下只允许 high
        if strategy == "conservative" and conf != "high":
            warnings.append({
                "level": "low",
                "code": "DEP_LOW_CONFIDENCE_IN_CONSERVATIVE",
                "message": f"{u}→{v}({t}) confidence={conf},conservative 策略建议只输出 high",
                "ui_hint": "informational",
            })

        if t == "prerequisite":
            prereq_edges.append((u, v))

    # DAG: 仅对 prerequisite 边检测环(generalization / specialization 也宜无环,
    #       但这里宽松,只严卡先修关系)
    if has_cycle_directed(prereq_edges, valid_ids):
        errors.append("concept_dependencies: prerequisite 关系存在环,违反 DAG 约束")

    return errors, warnings


# ---------- mode / depth 推断 ----------

def infer_mode(course_topic: str, material_files: list) -> str | None:
    has_topic = bool((course_topic or "").strip())
    has_material = bool(material_files)
    if has_topic and not has_material:
        return "topic_only"
    if has_material and not has_topic:
        return "material_first"
    if has_topic and has_material:
        return "hybrid"
    return None


def infer_depth(context: dict, prefs: dict) -> list[str]:
    depth_used = ["skim"]
    if context.get("focus_topics") or context.get("learning_goal") or context.get("user_level"):
        depth_used = ["skim", "guided"]
    if context.get("deep_explain") or prefs.get("depth_hint") == "force_deep":
        depth_used = ["skim", "guided", "deep"]
    if prefs.get("depth_hint") == "skim_only" or prefs.get("depth_hint") == "force_skim":
        depth_used = ["skim"]
    if prefs.get("depth_hint") == "force_guided":
        depth_used = ["skim", "guided"]
    return depth_used


# ---------- warnings / provenance ----------

def build_warnings(mode: str, evidence_counts: dict) -> list[dict]:
    warnings: list[dict] = []
    if mode == "topic_only":
        warnings.append({
            "level": "high",
            "code": "TOPIC_ONLY_HALLUCINATION_RISK",
            "message": "本框架完全为 AI 推断,所有节点 evidence_source = ai_inference。强烈建议用户提供 material_files(教材目录 / 笔记)做交叉验证。",
            "ui_hint": "顶部 ⚠️ banner",
        })
    elif mode == "hybrid":
        ai_ratio = evidence_counts["ai_inference"] / max(1, sum(evidence_counts.values()))
        if ai_ratio > 0.5:
            warnings.append({
                "level": "medium",
                "code": "HYBRID_AI_DOMINANT",
                "message": f"hybrid 模式下 AI 推断节点占比 {ai_ratio:.0%} > 50%,建议核对教材或追加更多 material_files",
                "ui_hint": "顶部黄色提示",
            })
    return warnings


def build_provenance_summary(mode: str, total: int, evidence_counts: dict) -> dict:
    risk = {
        "topic_only": "high",
        "material_first": "low" if evidence_counts["user_material"] / max(1, total) > 0.7 else "medium",
        "hybrid": "medium",
    }.get(mode, "medium")

    summary = {
        "total_nodes": total,
        "evidence_source_breakdown": evidence_counts,
        "ai_inferred_fields": ["framework_tree(*)", "recommended_questions(*)"] if mode == "topic_only" else ["framework_tree(部分)"],
        "ngram_match_attempted": mode != "topic_only",
        "hallucination_risk_overall": risk,
        "user_review_required": mode == "topic_only" or evidence_counts["ai_inference"] / max(1, total) > 0.3,
    }
    if mode == "topic_only":
        summary["ngram_match_attempted_reason"] = "topic_only 模式无 material_files,跳过 ngram 校验"
        summary["banner_message"] = "本框架完全为 AI 推断,建议核对教材"
    return summary


# ---------- 装配 ----------

def assemble(
    input_data: dict,
    tree: dict,
    questions: list,
    explanations: list | None,
    dependencies: list | None,
    fixture_id: str | None,
) -> tuple[dict, list[str]]:
    course_topic = input_data.get("course_topic", "")
    material_files = input_data.get("material_files", [])
    context = input_data.get("context") or {}
    prefs = input_data.get("preferences") or {}

    mode = infer_mode(course_topic, material_files)
    if mode is None:
        return {}, ["course_topic 与 material_files 不可同时为空"]

    depth_used = infer_depth(context, prefs)

    evidence_counts = fill_evidence_source(tree, mode)
    stats = compute_tree_stats(tree)
    max_levels = prefs.get("max_levels", CONSTRAINTS["max_levels"])

    errors: list[str] = []
    extra_warnings: list[dict] = []

    errors.extend(check_tree_constraints(stats, max_levels))

    # explanations 校验(仅当用户提供)
    if explanations is not None:
        e_err, e_warn = validate_explanations(explanations, tree, depth_used)
        errors.extend(e_err)
        extra_warnings.extend(e_warn)

    # dependencies 校验(仅当用户提供)
    dep_strategy = prefs.get("concept_dependency_strategy", "off")
    if dependencies is not None:
        d_err, d_warn = validate_dependencies(dependencies, tree, dep_strategy)
        errors.extend(d_err)
        extra_warnings.extend(d_warn)

    if errors:
        return {}, errors

    warnings = build_warnings(mode, evidence_counts) + extra_warnings
    prov_summary = build_provenance_summary(mode, stats["total_nodes"], evidence_counts)

    # node_explanations / concept_dependencies 默认值
    if "guided" in depth_used or "deep" in depth_used:
        node_exps = explanations or []
    else:
        node_exps = None

    if dep_strategy != "off":
        cdeps = dependencies or []
    else:
        cdeps = None

    result = {
        "meta": {
            "skill_name": "knowledge-framework-builder",
            "skill_version": SKILL_VERSION,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": mode,
            "depth_used": depth_used,
            "language": prefs.get("language", "zh"),
            "course_topic": course_topic or "(from material_files)",
            "material_files_count": len(material_files),
            **({"fixture_id": fixture_id} if fixture_id else {}),
        },
        "inputs_summary": {
            "course_topic": course_topic,
            "material_files_count": len(material_files),
            "focus_topics": context.get("focus_topics"),
            "learning_goal": context.get("learning_goal"),
            "user_level": context.get("user_level"),
            "deep_explain": bool(context.get("deep_explain")),
            "depth_hint": prefs.get("depth_hint", "auto"),
            "concept_dependency_strategy": dep_strategy,
            "importance_strategy": prefs.get("importance_strategy", "centrality"),
            "output_formats_requested": prefs.get("output_formats", ["markdown", "markmap", "mermaid", "opml"]),
        },
        "warnings": warnings,
        "framework_tree": tree,
        "tree_stats": stats,
        "node_explanations": node_exps,
        "concept_dependencies": cdeps,
        "recommended_questions": questions or [],
        "provenance_summary": prov_summary,
        "outputs": {
            "framework_md": "framework.md",
            "framework_markmap_html": "framework.markmap.html",
            "framework_mermaid_md": "framework.mermaid.md",
            "framework_opml": "framework.opml",
            **({"concept_dependencies_md": "concept-dependencies.md"} if cdeps else {}),
            "provenance_audit_json": "provenance-audit.json",
        },
        "next_step_hint": _next_hint(mode, depth_used, dep_strategy),
    }
    return result, []


def _next_hint(mode: str, depth_used: list[str], dep_strategy: str) -> str:
    hints = []
    if "guided" not in depth_used:
        hints.append("提供 context.focus_topics 自动升档 guided")
    if "deep" not in depth_used:
        hints.append("提供 context.deep_explain=true 升档 deep")
    if dep_strategy == "off":
        hints.append("提供 concept_dependency_strategy=conservative 启用依赖图")
    if mode == "topic_only":
        hints.append("提供 material_files 启用节点级 ngram 校验")
    if not hints:
        return "已开启所有高级特性,可生成 HTML 报告或导入 XMind 精修"
    return "下一步可:" + ";".join(hints) + "。"


# ---------- IO + main ----------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="装配 result.json")
    p.add_argument("--input", required=True, help="input.json 路径")
    p.add_argument("--tree", help="tree.json(LLM 产出的 framework_tree,顶层是单 root dict)")
    p.add_argument("--tree-from-result", help="从已有 result.json 抽取 framework_tree(自包含 dogfood 模式)")
    p.add_argument("--questions", help="questions.json(可选,recommended_questions 列表 / 字典)")
    p.add_argument("--explanations", help="explanations.json(可选,guided/deep node_explanations)")
    p.add_argument("--dependencies", help="dependencies.json(可选,concept_dependencies)")
    p.add_argument("--fixture-id", help="可选 fixture_id 写入 meta")
    p.add_argument("--out", required=True, help="result.json 输出路径")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[assemble] 错误: --input 不存在 {in_path}", file=sys.stderr)
        return 1
    input_data = load_json(in_path)

    if args.tree:
        tree_path = Path(args.tree)
        if not tree_path.exists():
            print(f"[assemble] 错误: --tree 不存在 {tree_path}", file=sys.stderr)
            return 1
        tree = load_json(tree_path)
        if isinstance(tree, dict) and "framework_tree" in tree:
            tree = tree["framework_tree"]
    elif args.tree_from_result:
        rpath = Path(args.tree_from_result)
        if not rpath.exists():
            print(f"[assemble] 错误: --tree-from-result 不存在 {rpath}", file=sys.stderr)
            return 1
        existing = load_json(rpath)
        tree = existing.get("framework_tree")
        if not tree:
            print(f"[assemble] 错误: {rpath} 不含 framework_tree 字段", file=sys.stderr)
            return 1
    else:
        print("[assemble] 错误: 必须提供 --tree 或 --tree-from-result", file=sys.stderr)
        return 1

    questions: list = []
    if args.questions:
        qpath = Path(args.questions)
        if qpath.exists():
            q_data = load_json(qpath)
            questions = q_data if isinstance(q_data, list) else q_data.get("recommended_questions", [])
    if not args.questions and args.tree_from_result:
        existing = load_json(Path(args.tree_from_result))
        questions = existing.get("recommended_questions", []) or []

    explanations: list | None = None
    if args.explanations:
        epath = Path(args.explanations)
        if not epath.exists():
            print(f"[assemble] 错误: --explanations 不存在 {epath}", file=sys.stderr)
            return 1
        e_data = load_json(epath)
        explanations = e_data if isinstance(e_data, list) else e_data.get("node_explanations", [])

    dependencies: list | None = None
    if args.dependencies:
        dpath = Path(args.dependencies)
        if not dpath.exists():
            print(f"[assemble] 错误: --dependencies 不存在 {dpath}", file=sys.stderr)
            return 1
        d_data = load_json(dpath)
        dependencies = d_data if isinstance(d_data, list) else d_data.get("concept_dependencies", [])

    result, errors = assemble(input_data, tree, questions, explanations, dependencies, args.fixture_id)
    if errors:
        print(f"[assemble] 装配失败:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    out_text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    Path(args.out).write_text(out_text + "\n", encoding="utf-8")

    stats = result["tree_stats"]
    n_exp = len(result["node_explanations"]) if result["node_explanations"] else 0
    n_dep = len(result["concept_dependencies"]) if result["concept_dependencies"] else 0
    print(
        f"[assemble] ✓ mode={result['meta']['mode']} · depth={result['meta']['depth_used']} · "
        f"{stats['total_nodes']} 节点 / {stats['leaf_count']} 叶子 / 层数={stats['max_depth']+1} · "
        f"explanations={n_exp} · deps={n_dep} · → {args.out}",
        file=sys.stderr,
    )
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"[assemble]   {w['level']:6s} {w['code']}: {w['message'][:80]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
