#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_jd.py —— JD 解析脚本

v0.3 变更：
  - 词典从内嵌迁移到 references/keyword-taxonomy.json（外置化）
  - 新增 AI archetype 推断（吸收自 santifer/career-ops）
  - 保留 v0.1 POC 的所有核心逻辑

功能：
  - 从输入 JD 纯文本中抽取关键词，按 hard_skills / soft_skills / industry_terms /
    seniority_markers / company_culture 分类
  - 为每个命中关键词附加权重
  - 推断 role_family：tech / biz / design / ops
  - 推断 seniority：intern / junior / mid / senior / staff / principal
  - 🆕 推断 AI archetype（仅当 role_family=tech 且 JD 含 AI 信号时）：
    AI_Platform_LLMOps / AI_Agentic_Automation / Technical_AI_PM /
    AI_Solutions_Architect / AI_Forward_Deployed / AI_Transformation
  - 输出结构化 JSON，供 resume-assistant 工作流 Step 2/3/6 消费

用法：
  python3 scripts/parse_jd.py --jd-file path/to/jd.txt
  python3 scripts/parse_jd.py --jd-file - < jd.txt
  python3 scripts/parse_jd.py --jd-text "算法工程师岗位职责：熟悉 PyTorch ..."
  python3 scripts/parse_jd.py --jd-file jd.txt --role-family tech --pretty
  python3 scripts/parse_jd.py --jd-file jd.txt --taxonomy custom-tax.json

输出：
  默认紧凑 JSON；--pretty 格式化。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TAXONOMY = SCRIPT_DIR.parent / "references" / "keyword-taxonomy.json"


# ============================================================
# 词典加载
# ============================================================

def load_taxonomy(path: Path) -> dict[str, Any]:
    """加载关键词词典。"""
    if not path.exists():
        raise FileNotFoundError(
            f"关键词词典不存在：{path}\n"
            f"  请检查是否缺少 references/keyword-taxonomy.json。"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"词典 JSON 解析失败：{path} → {e}")

    required_keys = {"keywords", "role_family_title_hints", "seniority_hints"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"词典缺少必需字段：{missing}")
    return data


# ============================================================
# 辅助：文本处理
# ============================================================

_ASCII_RE = re.compile(r"^[\x00-\x7f]+$")


def _is_ascii(s: str) -> bool:
    return bool(_ASCII_RE.match(s))


def normalize(text: str) -> str:
    """大小写不敏感。"""
    return text.lower()


def match_keyword(jd_lower: str, aliases: list[str]) -> tuple[bool, list[str]]:
    """
    在 jd_lower 中查找任一 alias。返回 (matched, hit_aliases)。
    匹配策略：
      - 纯 ASCII alias：用宽松词边界（非字母数字为界）→ 避免 own 命中 ownership
      - 含中文 alias：直接 substring（中文分词成本高；本版不做完整分词）
    """
    hits: list[str] = []
    for alias in aliases:
        alias_l = alias.lower()
        if _is_ascii(alias_l):
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(alias_l) + r"(?![A-Za-z0-9_])"
            if re.search(pattern, jd_lower):
                hits.append(alias)
        else:
            if alias_l in jd_lower:
                hits.append(alias)
    return (len(hits) > 0, hits)


# ============================================================
# 核心提取
# ============================================================

def extract_keywords(jd_text: str, keywords_spec: list[dict[str, Any]]) -> list[dict[str, Any]]:
    jd_lower = normalize(jd_text)
    results: list[dict[str, Any]] = []
    for kw in keywords_spec:
        matched, hits = match_keyword(jd_lower, kw["aliases"])
        if matched:
            results.append({
                "id": kw["id"],
                "category": kw["category"],
                "role_family": kw["role_family"],
                "weight": kw["weight"],
                "hit_aliases": hits,
            })
    return results


def infer_role_family(
    jd_text: str,
    matched_keywords: list[dict[str, Any]],
    title_hints: dict[str, list[str]],
    override: str | None = None,
) -> tuple[str, str]:
    """
    返回 (role_family, rationale)。
    1. 若 override，直接用
    2. 从 JD 标题 / 开头 300 字找 title_hints
    3. fallback：看 matched_keywords 里 category=hard_skills 的分布
    """
    if override:
        return override, "用户显式指定"

    head = jd_text[:300].lower()
    for fam, hints in title_hints.items():
        for h in hints:
            if h.lower() in head:
                return fam, f"JD 开头命中标题关键词「{h}」"

    fam_count: dict[str, int] = {}
    for kw in matched_keywords:
        if kw["category"] != "hard_skills":
            continue
        fam = kw["role_family"]
        if fam == "*":
            continue
        fam_count[fam] = fam_count.get(fam, 0) + 1

    if not fam_count:
        return "tech", "无明显信号，默认 tech（保守处理）"

    best = max(fam_count.items(), key=lambda x: x[1])
    return best[0], f"hard_skills 分布推断（{fam_count}）"


def infer_seniority(jd_text: str, seniority_hints: dict[str, list[str]]) -> tuple[str, str]:
    jd_lower = jd_text.lower()
    for level, hints in seniority_hints.items():
        for h in hints:
            if h.lower() in jd_lower:
                return level, f"命中「{h}」"
    return "mid", "无明显信号，默认 mid（保守处理）"


def infer_ai_archetype(
    jd_text: str,
    role_family: str,
    ai_archetypes: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    仅当 role_family=tech 且 JD 出现明确 AI 信号时，推断 archetype。
    返回 {archetype_id, display_name_zh, signals_hit[], framing_hint, confidence}
    或 None（当没有明显 AI 信号）。

    置信度规则：
      - 主 archetype 命中 ≥ 3 个 signal → high
      - 命中 2 个 → medium
      - 命中 1 个 → low
      - 0 → None
    """
    if role_family != "tech" or not ai_archetypes:
        return None

    jd_lower = jd_text.lower()

    # 先做一个 AI 总信号检测 —— 没有 AI 关键词就不推 archetype
    ai_trigger_terms = ["llm", "大模型", "大语言模型", "ai ", " ai", "机器学习",
                        "深度学习", "agent", "智能体", "model", "model training",
                        "算法", "人工智能", "artificial intelligence"]
    if not any(t in jd_lower for t in ai_trigger_terms):
        return None

    # 分别计分
    scores: list[tuple[str, dict[str, Any], list[str]]] = []
    for arch_id, spec in ai_archetypes.items():
        if arch_id.startswith("_"):  # 跳过 _note
            continue
        signals = spec.get("signals", [])
        hits = [s for s in signals if s.lower() in jd_lower]
        if hits:
            scores.append((arch_id, spec, hits))

    if not scores:
        return None

    # 按命中数降序
    scores.sort(key=lambda x: -len(x[2]))
    primary_id, primary_spec, primary_hits = scores[0]

    n = len(primary_hits)
    confidence = "high" if n >= 3 else ("medium" if n == 2 else "low")

    return {
        "archetype": primary_id,
        "display_name_zh": primary_spec.get("display_name_zh", primary_id),
        "signals_hit": primary_hits,
        "framing_hint": primary_spec.get("framing_hint"),
        "confidence": confidence,
        "secondary_candidates": [
            {"archetype": a, "hits": h}
            for a, _, h in scores[1:3]
        ] if len(scores) > 1 else [],
    }


def categorize(matched_keywords: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "hard_skills": [],
        "industry_terms": [],
        "soft_skills": [],
        "seniority_markers": [],
        "company_culture": [],
    }
    for kw in matched_keywords:
        buckets.setdefault(kw["category"], []).append(kw)
    for cat in buckets:
        buckets[cat].sort(key=lambda x: -x["weight"])
    return buckets


def aggregate_stats(matched: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(matched)
    by_cat: dict[str, int] = {}
    weight_sum = 0.0
    for kw in matched:
        by_cat[kw["category"]] = by_cat.get(kw["category"], 0) + 1
        weight_sum += kw["weight"]
    return {
        "total_matched": total,
        "total_weight": round(weight_sum, 3),
        "by_category": by_cat,
    }


def build_result(
    jd_text: str,
    taxonomy: dict[str, Any],
    role_family_override: str | None,
) -> dict[str, Any]:
    matched = extract_keywords(jd_text, taxonomy["keywords"])
    role_family, rf_rationale = infer_role_family(
        jd_text, matched, taxonomy["role_family_title_hints"], role_family_override
    )
    seniority, sn_rationale = infer_seniority(jd_text, taxonomy["seniority_hints"])
    archetype = infer_ai_archetype(jd_text, role_family, taxonomy.get("ai_archetypes"))
    buckets = categorize(matched)
    stats = aggregate_stats(matched)

    warnings: list[str] = []
    if stats["total_matched"] == 0:
        warnings.append("未命中任何关键词；可能是领域超出当前词典覆盖范围。")
    if stats["by_category"].get("hard_skills", 0) == 0:
        warnings.append("未命中 hard_skills；tailor 效果可能受限，建议用户检查 JD 是否完整。")
    if len(jd_text) < 100:
        warnings.append(f"JD 较短（{len(jd_text)} 字符），关键词抽取可能不准确。")

    return {
        "schema_version": "0.3",
        "tool": "parse_jd.py",
        "taxonomy_version": taxonomy.get("_meta", {}).get("schema_version", "unknown"),
        "jd_length_chars": len(jd_text),
        "role_family": role_family,
        "role_family_rationale": rf_rationale,
        "inferred_seniority": seniority,
        "seniority_rationale": sn_rationale,
        "ai_archetype": archetype,
        "stats": stats,
        "matched_keywords_by_category": buckets,
        "warnings": warnings,
    }


# ============================================================
# I/O
# ============================================================

def load_jd(args: argparse.Namespace) -> str:
    if args.jd_text:
        return args.jd_text
    if not args.jd_file:
        raise ValueError("必须提供 --jd-file 或 --jd-text")
    if args.jd_file == "-":
        return sys.stdin.read()
    p = Path(args.jd_file)
    if not p.exists():
        raise FileNotFoundError(f"JD 文件不存在：{p}")
    return p.read_text(encoding="utf-8")


# ============================================================
# CLI
# ============================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="JD 解析：关键词抽取 + role_family / seniority / AI archetype 推断",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--jd-file", help="JD 文件路径，用 '-' 读 stdin")
    src.add_argument("--jd-text", help="JD 文本（直接传字符串）")

    parser.add_argument(
        "--role-family",
        choices=["tech", "biz", "design", "ops"],
        default=None,
        help="显式指定 role_family（跳过推断）",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=DEFAULT_TAXONOMY,
        help=f"关键词词典 JSON 路径（默认：{DEFAULT_TAXONOMY.relative_to(SCRIPT_DIR.parent)}）",
    )
    parser.add_argument("--pretty", action="store_true", help="JSON 格式化输出")
    parser.add_argument("--out", help="输出到文件（默认 stdout）")

    args = parser.parse_args(argv)

    try:
        taxonomy = load_taxonomy(args.taxonomy)
        jd_text = load_jd(args)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    result = build_result(jd_text, taxonomy, args.role_family)

    if args.pretty:
        payload = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        payload = json.dumps(result, ensure_ascii=False)

    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
