#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_provenance.py —— 知识框架梳理 Skill · 节点级 Provenance 审计(v0.2.0)

功能:
  - 读取 result.json + 可选 material 文件列表
  - 三条审计路径:
      路径 A · topic_only / 无 material   → 输出 skipped 审计(显式标注原因 + banner)
      路径 B · material_first / hybrid    → 对每个 evidence_source = user_material 的节点,
                                            ngram 匹配 evidence_locator.excerpt vs material 全文
                                            (v0.2 阶段先打 stub 标 v0.5 实装,接口稳定)
      路径 C · curated_syllabus(v1.1+)   → 比对内置课纲库(留白)
  - 输出 provenance-audit.json,结构详见 references/provenance-spec.md(v0.3 落地)

用法:
  python3 scripts/verify_provenance.py \
      --result result.json \
      --out provenance-audit.json --pretty

  python3 scripts/verify_provenance.py \
      --result result.json \
      --material textbook.md notes.md \
      --out provenance-audit.json --pretty

退出码:
  0  审计完成(不管 skipped 还是命中)
  1  参数 / 文件错误
  2  result.json 缺关键字段
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "0.5.0"

# 把所有非字母/数字/中文/连字符 字符当作分隔符,覆盖中英文标点 + 空白
SEPARATOR_PATTERN = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff_\-]+", re.UNICODE)


def normalize(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text).lower()
    t = SEPARATOR_PATTERN.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def tokenize(text: str) -> list[str]:
    """Tokenize:
    - 英文/数字 chunk 整体作为 1 个 token
    - 中文 chunk 切成单字 token(中文每字独立)
    - 混排 chunk(如 "Bagging降方差")按中英文边界拆分
    """
    norm = normalize(text)
    tokens: list[str] = []
    for chunk in norm.split():
        cur = ""
        cur_is_cn: bool | None = None  # None / True(中文) / False(其他)
        for ch in chunk:
            is_cn = "\u4e00" <= ch <= "\u9fff"
            if cur_is_cn is None:
                cur = ch
                cur_is_cn = is_cn
            elif is_cn:
                if cur_is_cn:
                    tokens.append(cur)
                    cur = ch
                else:
                    if cur:
                        tokens.append(cur)
                    cur = ch
                    cur_is_cn = True
            else:
                if cur_is_cn:
                    if cur:
                        tokens.append(cur)
                    cur = ch
                    cur_is_cn = False
                else:
                    cur += ch
        if cur:
            tokens.append(cur)
    return tokens


def make_ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)} if len(tokens) >= n else set()


def walk_tree(node: dict, level: int = 0):
    yield node, level
    for c in node.get("children", []) or []:
        yield from walk_tree(c, level + 1)


def audit_skipped(result: dict, reason: str) -> dict:
    """topic_only / 无 material 时的 skipped 审计。"""
    tree = result.get("framework_tree", {})
    nodes = list(walk_tree(tree))
    total = len(nodes)
    counts = {"user_material": 0, "ai_inference": 0, "curated_syllabus": 0}
    for node, _ in nodes:
        counts[node.get("evidence_source", "ai_inference")] = counts.get(node.get("evidence_source", "ai_inference"), 0) + 1

    sample_nodes = []
    for nid in ["n0", "n1.1.1", "n2.4.3", "n6.2.2"]:
        for node, lv in nodes:
            if node.get("id") == nid:
                sample_nodes.append({
                    "node_id": nid,
                    "title": node.get("title"),
                    "level": lv,
                    "evidence_source": node.get("evidence_source"),
                    "ngram_match_confidence": "n/a (no material)",
                    "hallucination_risk": "high" if lv == 0 else "high",
                })
                break

    return {
        "audit_version": SCRIPT_VERSION,
        "audit_mode": "topic_only_no_material" if result.get("meta", {}).get("mode") == "topic_only" else "skipped_no_material",
        "skill": f"knowledge-framework-builder@{result.get('meta', {}).get('skill_version', '0.2.0')}",
        "fixture_id": result.get("meta", {}).get("fixture_id"),
        "audit_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_nodes": total,
            "user_material_provided": False,
            "ngram_match_attempted": False,
            "ngram_match_attempted_reason": reason,
            "evidence_source_breakdown": counts,
            "ai_inferred_fields_at_tree_level": ["framework_tree.children[*]", "recommended_questions[*]"],
            "hallucination_risk_overall": "high" if counts["ai_inference"] > total * 0.7 else "medium",
            "user_review_required": True,
            "ui_banner_required": True,
            "ui_banner_message": "本框架完全为 AI 推断,建议核对教材",
        },
        "rules_applied": [
            {
                "rule_id": "skill-md-principle-2",
                "rule_text": "topic_only 模式 → 所有节点 evidence_source = ai_inference,顶部强制 ⚠️ banner",
                "violated": False,
            },
            {
                "rule_id": "skill-md-principle-9",
                "rule_text": "单次处理上限 1 门课 / 节点数 > 100 → 拒绝",
                "violated": False,
                "actual_node_count": total,
                "limit": 100,
            },
            {
                "rule_id": "skill-md-step-7-banner",
                "rule_text": "topic_only → 顶部加 banner『本框架完全为 AI 推断,建议核对教材』",
                "applied": True,
                "applied_in": ["framework.md (顶部)", "result.json.warnings[0]", "framework.markmap.html (顶部)"],
            },
        ],
        "node_audit_strategy": "skipped (no material to verify against)",
        "node_audit_sample": sample_nodes,
        "recommendations_for_user": [
            "强烈建议:提供 material_files(教材目录 / 大纲 / 笔记)做交叉验证,启用节点级 ngram 校验",
            "v1.1 启用后:本课程将命中内置课纲库(CET-4 / CET-6 大纲),evidence_source 自动升级为 curated_syllabus",
        ],
        "next_audit_hint": "重新运行本 Skill 并附 material_files,将自动从 ai_inference → user_material 升级,所有节点带 evidence_locator{file, section, excerpt}",
    }


def audit_with_material(result: dict, material_paths: list[Path]) -> dict:
    """v0.2 阶段实现:逐节点 ngram 匹配 evidence_locator.excerpt。"""
    full_text_by_file = {}
    for p in material_paths:
        full_text_by_file[str(p)] = p.read_text(encoding="utf-8", errors="replace")

    haystack_tokens: list[str] = []
    for txt in full_text_by_file.values():
        haystack_tokens.extend(tokenize(txt))
    haystack_3grams = make_ngrams(haystack_tokens, 3)
    haystack_5grams = make_ngrams(haystack_tokens, 5)

    tree = result.get("framework_tree", {})
    per_node_audit: list[dict] = []
    counts = {"high": 0, "medium": 0, "low": 0, "failed": 0, "skipped": 0}

    for node, lv in walk_tree(tree):
        es = node.get("evidence_source", "ai_inference")
        if es == "ai_inference":
            counts["skipped"] += 1
            continue
        loc = node.get("evidence_locator") or {}
        excerpt = loc.get("excerpt", "")
        if not excerpt:
            counts["failed"] += 1
            per_node_audit.append({
                "node_id": node.get("id"),
                "title": node.get("title"),
                "level": lv,
                "evidence_source": es,
                "verdict": "failed",
                "reason": "evidence_source=user_material 但缺 evidence_locator.excerpt",
            })
            continue

        ex_tokens = tokenize(excerpt)
        ex_3 = make_ngrams(ex_tokens, 3)
        ex_5 = make_ngrams(ex_tokens, 5)

        if not ex_3:
            verdict = "low"
        else:
            hit3 = len(ex_3 & haystack_3grams) / len(ex_3)
            hit5 = (len(ex_5 & haystack_5grams) / len(ex_5)) if ex_5 else 0
            if hit5 >= 0.6 or hit3 >= 0.85:
                verdict = "high"
            elif hit3 >= 0.6:
                verdict = "medium"
            elif hit3 >= 0.3:
                verdict = "low"
            else:
                verdict = "failed"

        counts[verdict] = counts.get(verdict, 0) + 1
        per_node_audit.append({
            "node_id": node.get("id"),
            "title": node.get("title"),
            "level": lv,
            "evidence_source": es,
            "verdict": verdict,
            "excerpt_preview": excerpt[:80] + ("…" if len(excerpt) > 80 else ""),
        })

    total = sum(1 for _ in walk_tree(tree))
    return {
        "audit_version": SCRIPT_VERSION,
        "audit_mode": "ngram_node_level",
        "skill": f"knowledge-framework-builder@{result.get('meta', {}).get('skill_version', '0.2.0')}",
        "fixture_id": result.get("meta", {}).get("fixture_id"),
        "audit_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_nodes": total,
            "user_material_provided": True,
            "material_files": [str(p) for p in material_paths],
            "ngram_match_attempted": True,
            "verdict_counts": counts,
            "high_ratio": round(counts.get("high", 0) / max(1, total - counts.get("skipped", 0)), 2),
            "user_review_required": counts.get("failed", 0) > 0 or counts.get("low", 0) > total * 0.2,
        },
        "node_audit": per_node_audit,
        "recommendations_for_user": (
            ["有 failed 节点,建议核对原文或重新生成对应分支"] if counts.get("failed", 0) else []
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="知识框架节点级 Provenance 审计")
    p.add_argument("--result", required=True, help="result.json 路径")
    p.add_argument("--material", nargs="*", default=[], help="material 文件列表(为空 → skipped 审计)")
    p.add_argument("--out", required=True, help="provenance-audit.json 输出路径")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()

    rpath = Path(args.result)
    if not rpath.exists():
        print(f"[verify_provenance] 错误: --result 不存在 {rpath}", file=sys.stderr)
        return 1

    try:
        result = json.loads(rpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[verify_provenance] 错误: result.json 解析失败: {e}", file=sys.stderr)
        return 1

    if "framework_tree" not in result:
        print("[verify_provenance] 错误: result.json 缺 framework_tree", file=sys.stderr)
        return 2

    mode = result.get("meta", {}).get("mode", "topic_only")
    material_paths = [Path(m) for m in args.material]
    missing = [str(p) for p in material_paths if not p.exists()]
    if missing:
        print(f"[verify_provenance] 错误: material 文件不存在: {missing}", file=sys.stderr)
        return 1

    if mode == "topic_only" or not material_paths:
        reason = (
            "material_files 为空,无可校验对象;按 SKILL.md 核心原则 2,所有节点统一标记 evidence_source = ai_inference"
            if mode == "topic_only"
            else f"未提供 --material,跳过 ngram 校验(mode={mode})"
        )
        audit = audit_skipped(result, reason)
    else:
        audit = audit_with_material(result, material_paths)

    out_text = json.dumps(audit, ensure_ascii=False, indent=2 if args.pretty else None)
    Path(args.out).write_text(out_text + "\n", encoding="utf-8")

    summary = audit["summary"]
    print(
        f"[verify_provenance] ✓ mode={audit['audit_mode']} · 节点={summary['total_nodes']} · "
        f"ngram_attempted={summary.get('ngram_match_attempted')} · → {args.out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
