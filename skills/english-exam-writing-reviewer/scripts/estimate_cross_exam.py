#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estimate_cross_exam.py —— 跨考试批改推演器（v1.5 新增）

把 references/calibration/cross-exam-analysis.md 中的人工推演规则固化为可调用脚本：
给定一篇作文的"原生考试 + 原生分数"，推算它拿去参加其它考试能得几分。

核心能力
--------
1. **兼容性预检**（native / partial / incompatible 三态）
2. **等效分映射**（基于 cross-exam-analysis §4 换算表）
3. **缺失维度诊断**（告诉用户目标考试下会因为缺什么维度而扣分）
4. **可选字数/文体自检**（读取作文文件，预判是否满足目标考试的硬约束）
5. **批量推演**（一次对比所有 6 个考试）

使用示例
--------
# 单目标：CET-6 14 分作文拿去考研英一 B 能得几分？
python estimate_cross_exam.py --source CET6 --source-score 14 --target Postgrad1B

# 批量：一篇作文在所有 6 个考试下的等效分
python estimate_cross_exam.py --source CET6 --source-score 14 --all

# 机读 JSON（供 Skill 消费）
python estimate_cross_exam.py --source CET6 --source-score 14 --all --format json

# 带作文文件做字数 + 文体预检
python estimate_cross_exam.py --source CET4 --source-score 11 \
    --essay-file references/examples/postgrad1b-example/input.txt \
    --source-subtype argumentative --target Postgrad1B

依赖：仅标准库。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ===== 常量：各考试基本属性 =====
EXAM_PROFILES: dict[str, dict] = {
    "CET4":       {"max": 15, "word_min": 120, "word_max": 180, "allowed_subtypes": ["argumentative", "chart", "cartoon", "letter"]},
    "CET6":       {"max": 15, "word_min": 150, "word_max": 200, "allowed_subtypes": ["argumentative", "chart", "cartoon", "letter"]},
    "Postgrad1A": {"max": 10, "word_min":  80, "word_max": None, "allowed_subtypes": ["letter", "announcement", "memorandum", "notice"]},
    "Postgrad1B": {"max": 20, "word_min": 160, "word_max": 200,  "allowed_subtypes": ["cartoon", "descriptive", "narrative", "expository"]},
    "Postgrad2A": {"max": 10, "word_min":  80, "word_max": None, "allowed_subtypes": ["letter", "notice", "announcement"]},
    "Postgrad2B": {"max": 15, "word_min": 120, "word_max": None, "allowed_subtypes": ["chart", "table", "pie_chart"]},
}

# ===== 档次分布（与 calibrate.py / diff_rubric.py 一致）=====
BAND_RANGES: dict[str, dict[int, tuple[int, int]]] = {
    "CET4":       {14:(13,15), 11:(10,12), 8:(7,9), 5:(4,6), 2:(1,3), 0:(0,0)},
    "CET6":       {14:(13,15), 11:(10,12), 8:(7,9), 5:(4,6), 2:(1,3), 0:(0,0)},
    "Postgrad1A": {5:(9,10),  4:(7,8),   3:(5,6), 2:(3,4), 1:(1,2), 0:(0,0)},
    "Postgrad1B": {5:(17,20), 4:(13,16), 3:(9,12),2:(5,8), 1:(1,4), 0:(0,0)},
    "Postgrad2A": {5:(9,10),  4:(7,8),   3:(5,6), 2:(3,4), 1:(1,2), 0:(0,0)},
    "Postgrad2B": {5:(13,15), 4:(10,12), 3:(7,9), 2:(4,6), 1:(1,3), 0:(0,0)},
}

# ===== 兼容性矩阵（来自 cross-exam-analysis.md §5.1）=====
COMPATIBILITY: dict[tuple[str, str], str] = {
    # argumentative
    ("argumentative", "CET4"):       "native",
    ("argumentative", "CET6"):       "native",
    ("argumentative", "Postgrad1B"): "partial",
    ("argumentative", "Postgrad2B"): "incompatible",  # 缺数据描述
    ("argumentative", "Postgrad1A"): "incompatible",
    ("argumentative", "Postgrad2A"): "incompatible",

    # letter
    ("letter", "Postgrad1A"): "native",
    ("letter", "Postgrad2A"): "partial",
    ("letter", "CET4"):       "partial",
    ("letter", "CET6"):       "partial",
    ("letter", "Postgrad1B"): "incompatible",
    ("letter", "Postgrad2B"): "incompatible",

    # notice / announcement
    ("notice", "Postgrad2A"): "native",
    ("notice", "Postgrad1A"): "partial",
    ("notice", "CET4"):       "partial",
    ("notice", "CET6"):       "partial",
    ("notice", "Postgrad1B"): "incompatible",
    ("notice", "Postgrad2B"): "incompatible",

    # cartoon / 图画论述文
    ("cartoon", "Postgrad1B"): "native",
    ("cartoon", "CET6"):       "partial",
    ("cartoon", "CET4"):       "partial",
    ("cartoon", "Postgrad2B"): "incompatible",
    ("cartoon", "Postgrad1A"): "incompatible",
    ("cartoon", "Postgrad2A"): "incompatible",

    # chart / 图表说明文
    ("chart", "Postgrad2B"): "native",
    ("chart", "CET6"):       "partial",
    ("chart", "CET4"):       "partial",
    ("chart", "Postgrad1B"): "incompatible",
    ("chart", "Postgrad1A"): "incompatible",
    ("chart", "Postgrad2A"): "incompatible",

    # descriptive / narrative / expository（英一 B 专用文体）
    ("descriptive", "Postgrad1B"): "native",
    ("narrative",   "Postgrad1B"): "native",
    ("expository",  "Postgrad1B"): "native",
    ("descriptive", "CET6"):       "partial",
    ("narrative",   "CET6"):       "partial",
    ("expository",  "CET6"):       "partial",
    ("descriptive", "Postgrad2B"): "partial",   # 转图表说明可能勉强
    ("expository",  "Postgrad2B"): "partial",
}

# 未列出的 (subtype, exam) 对按 "incompatible" 保守处理。


# ===== 跨考试等效分映射（百分位对齐法）=====
# 思路：把原生分归一化为"档次百分位"（band_pct ∈ [0, 1]），然后映射到目标考试的等效档次。
# 同时对 partial 情形附加 -0.5 ~ -1 档惩罚；对 incompatible 情形返回 None 并列出缺失维度。

def band_and_position(exam: str, score: float) -> tuple[int, float]:
    """给定考试和原始分，返回 (band, band_internal_position)。
    band_internal_position ∈ [0, 1]：0 为档内最低，1 为档内最高。"""
    ranges = BAND_RANGES[exam]
    # 找到 score 所属 band
    for band, (lo, hi) in ranges.items():
        if band == 0:
            continue
        if lo <= score <= hi:
            span = hi - lo
            pos = (score - lo) / span if span > 0 else 1.0
            return band, pos
    return 0, 0.0


def global_percentile(exam: str, score: float) -> float:
    """全局百分位：score / max。"""
    return float(score) / EXAM_PROFILES[exam]["max"]


def map_band(source_exam: str, source_score: float, target_exam: str) -> tuple[int, float]:
    """
    把源考试分数映射到目标考试的档次 + 目标分数。
    - 对 CET↔CET 之间：按档次同级 +/- 偏移（CET-6 → CET-4 通常 +1 档）
    - 对考研各级别之间：按原档序号平移（Postgrad1B 第四档 → Postgrad2B 第四档）
    - 对 CET↔考研：用全局百分位对齐 + 额外 -0.5 档调整（语言水平迁移成本）
    """
    src_band, src_pos = band_and_position(source_exam, source_score)
    if src_band == 0:
        return 0, 0.0

    is_src_postgrad = source_exam.startswith("Postgrad")
    is_tgt_postgrad = target_exam.startswith("Postgrad")

    # CET4 <-> CET6：同档次编号（14/11/8/5/2 都相同）
    if not is_src_postgrad and not is_tgt_postgrad:
        if source_exam == "CET6" and target_exam == "CET4":
            # CET-6 高档投 CET-4 通常多 1 分（降维打击）；低档基本持平
            bonus = 1 if src_band >= 11 else 0
        elif source_exam == "CET4" and target_exam == "CET6":
            # CET-4 投 CET-6 通常降 1 档
            bonus = -3 if src_band >= 11 else -3 if src_band >= 8 else 0  # 粗略降档（14→11/11→8）
        else:
            bonus = 0
        target_score = source_score + bonus
        # 夹在合法区间
        tgt_max = EXAM_PROFILES[target_exam]["max"]
        target_score = max(0, min(tgt_max, target_score))
        band, _ = band_and_position(target_exam, target_score)
        return band, target_score

    # 考研 <-> 考研：按档次编号同级映射（5/4/3/2/1 一一对应）
    if is_src_postgrad and is_tgt_postgrad:
        tgt_bands = BAND_RANGES[target_exam]
        lo, hi = tgt_bands[src_band]
        span = hi - lo
        target_score = lo + span * src_pos
        # 0.5 步长
        target_score = round(target_score * 2) / 2
        return src_band, target_score

    # 跨大类：CET <-> 考研 —— 用全局百分位 + 惩罚
    pct = global_percentile(source_exam, source_score)
    tgt_max = EXAM_PROFILES[target_exam]["max"]
    raw_target = pct * tgt_max
    # 考研的 partial 惩罚：-5% max（考研语言权重更高）
    if is_tgt_postgrad:
        raw_target *= 0.90
    else:
        # 考研高档投 CET 反而可能加分（语言水平过剩）
        if pct >= 0.70:
            raw_target *= 1.05
    target_score = round(raw_target * 2) / 2 if is_tgt_postgrad else round(raw_target)
    target_score = max(0, min(tgt_max, target_score))
    band, _ = band_and_position(target_exam, target_score)
    return band, target_score


# ===== 缺失维度推断 =====
# 当兼容性 = incompatible 时，列出目标考试会因为缺什么触发扣分。
MISSING_DIMENSIONS: dict[tuple[str, str], list[str]] = {
    ("argumentative", "Postgrad1A"): ["letter_format (称呼/落款)", "signature_compliance", "register_formal"],
    ("argumentative", "Postgrad2A"): ["notice_format", "signature_compliance"],
    ("argumentative", "Postgrad2B"): ["data_accuracy", "chart_vocabulary"],

    ("letter", "Postgrad1B"):       ["interpretation_of_meaning", "three-points (描述+寓意+评论)"],
    ("letter", "Postgrad2B"):       ["data_accuracy", "chart_vocabulary", "three-points"],

    ("notice", "Postgrad1B"):       ["interpretation_of_meaning", "three-points"],
    ("notice", "Postgrad2B"):       ["data_accuracy", "chart_vocabulary"],

    ("cartoon", "Postgrad1A"):      ["letter_format", "signature_compliance"],
    ("cartoon", "Postgrad2A"):      ["notice_format", "signature_compliance"],
    ("cartoon", "Postgrad2B"):      ["data_accuracy", "chart_vocabulary"],

    ("chart",   "Postgrad1A"):      ["letter_format", "signature_compliance"],
    ("chart",   "Postgrad2A"):      ["notice_format", "signature_compliance"],
    ("chart",   "Postgrad1B"):      ["interpretation_of_meaning", "cartoon_narrative"],
}


def get_compatibility(subtype: str, target_exam: str) -> str:
    return COMPATIBILITY.get((subtype, target_exam), "incompatible")


def get_missing_dims(subtype: str, target_exam: str) -> list[str]:
    return MISSING_DIMENSIONS.get((subtype, target_exam), ["（未登记，建议手动分析）"])


# ===== 字数 / 文体自检 =====
def count_words(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", text))


def detect_subtype(text: str, hint: str | None = None) -> str:
    """启发式文体检测。"""
    if hint:
        return hint
    t = text.lower()
    # letter
    if re.search(r"dear\s+\w+", t) and re.search(r"(yours?|sincerely|regards|faithfully)", t):
        return "letter"
    if re.search(r"notice|announcement", t[:200]):
        return "notice"
    # chart
    if re.search(r"(chart|pie|bar|table).{0,50}(show|illustrate|present|reveal)", t):
        return "chart"
    # cartoon
    if re.search(r"(picture|cartoon|image).{0,50}(show|depict|portray)", t):
        return "cartoon"
    # 默认 argumentative
    return "argumentative"


# ===== 核心估算函数（可被 Skill 直接 import） =====
def estimate(source_exam: str, source_score: float, target_exam: str,
             subtype: str = "argumentative",
             essay_text: str | None = None) -> dict:
    """返回单个目标考试的预估结果字典。"""
    if source_exam not in EXAM_PROFILES:
        return {"error": f"未知 source_exam: {source_exam}"}
    if target_exam not in EXAM_PROFILES:
        return {"error": f"未知 target_exam: {target_exam}"}

    # 字数自检（若提供作文）
    word_issue: str | None = None
    if essay_text is not None:
        wc = count_words(essay_text)
        prof = EXAM_PROFILES[target_exam]
        if wc < prof["word_min"]:
            short = (prof["word_min"] - wc) / prof["word_min"]
            word_issue = f"字数 {wc} 不足目标考试最低 {prof['word_min']}（偏短 {short:.0%}）"
        elif prof["word_max"] and wc > prof["word_max"]:
            word_issue = f"字数 {wc} 超过目标考试上限 {prof['word_max']}"

    compat = get_compatibility(subtype, target_exam)

    if compat == "native":
        src_max = EXAM_PROFILES[source_exam]["max"]
        tgt_max = EXAM_PROFILES[target_exam]["max"]
        is_tgt_postgrad = target_exam.startswith("Postgrad")
        if src_max == tgt_max:
            est_score = source_score
            note = "文体与目标考试一致 + 满分相同，可直接按原分参考"
        else:
            pct = source_score / src_max
            raw = pct * tgt_max
            est_score = round(raw * 2) / 2 if is_tgt_postgrad else round(raw)
            est_score = max(0, min(tgt_max, est_score))
            note = (f"文体与目标考试一致，但满分不同（{src_max}→{tgt_max}），"
                    f"按百分位等比对齐：{source_score}/{src_max} ({pct:.0%}) → {est_score}/{tgt_max}")
        est_band, _ = band_and_position(target_exam, est_score)
        return {
            "source_exam": source_exam,
            "source_score": source_score,
            "source_subtype": subtype,
            "target_exam": target_exam,
            "compatibility": "native",
            "estimated_band": est_band,
            "estimated_score": round(est_score, 1),
            "score_max": tgt_max,
            "missing_dimensions": [],
            "caveats": [note] + ([word_issue] if word_issue else []),
            "confidence": "high",
        }

    if compat == "incompatible":
        return {
            "source_exam": source_exam,
            "source_score": source_score,
            "source_subtype": subtype,
            "target_exam": target_exam,
            "compatibility": "incompatible",
            "estimated_band": None,
            "estimated_score": None,
            "score_max": EXAM_PROFILES[target_exam]["max"],
            "missing_dimensions": get_missing_dims(subtype, target_exam),
            "caveats": [
                f"{subtype} 文体在 {target_exam} 下触发 critical 维度缺失，"
                f"Skill 不输出具体分数",
                "建议先按目标考试的文体改写，再做原生批改",
            ] + ([word_issue] if word_issue else []),
            "confidence": "refuse",
        }

    # partial
    est_band, est_score = map_band(source_exam, source_score, target_exam)
    score_max = EXAM_PROFILES[target_exam]["max"]
    caveats = [
        f"{subtype} 文体在 {target_exam} 下非主流题型，可能存在模板不匹配风险",
        f"已按'全局百分位 + 90% 衰减'推演（原 {source_score}/{EXAM_PROFILES[source_exam]['max']} "
        f"→ 目标 {est_score}/{score_max}）",
    ]
    if word_issue:
        caveats.append(word_issue)

    return {
        "source_exam": source_exam,
        "source_score": source_score,
        "source_subtype": subtype,
        "target_exam": target_exam,
        "compatibility": "partial",
        "estimated_band": est_band,
        "estimated_score": est_score,
        "score_max": score_max,
        "missing_dimensions": get_missing_dims(subtype, target_exam) if (subtype, target_exam) in MISSING_DIMENSIONS else [],
        "caveats": caveats,
        "confidence": "medium",
    }


def estimate_all(source_exam: str, source_score: float,
                 subtype: str = "argumentative",
                 essay_text: str | None = None) -> list[dict]:
    return [estimate(source_exam, source_score, tgt, subtype, essay_text)
            for tgt in EXAM_PROFILES]


# ===== 渲染 =====
def render_md(results: list[dict]) -> str:
    src = results[0]
    out = [
        f"# 跨考试批改推演",
        "",
        f"**源考试**：{src['source_exam']} "
        f"**原生分**：{src['source_score']}/{EXAM_PROFILES[src['source_exam']]['max']} "
        f"**文体**：{src['source_subtype']}",
        "",
        "## 推演结果",
        "",
        "| 目标考试 | 兼容性 | 预估档 | 预估分 | 置信度 | 主要说明 |",
        "|---------|-------|-------|-------|-------|---------|",
    ]
    icon = {"native": "✅ native", "partial": "⚠️ partial", "incompatible": "❌ incompatible",
            "refuse": "—"}
    for r in results:
        if r.get("error"):
            continue
        band = r["estimated_band"] if r["estimated_band"] is not None else "—"
        score = f'{r["estimated_score"]}/{r["score_max"]}' if r["estimated_score"] is not None else "—"
        caveat = r["caveats"][0] if r["caveats"] else ""
        out.append(f"| **{r['target_exam']}** | {icon.get(r['compatibility'], r['compatibility'])} "
                   f"| {band} | {score} | {r['confidence']} | {caveat[:60]}{'...' if len(caveat) > 60 else ''} |")

    # 详情
    out.append("")
    out.append("## 详细诊断")
    for r in results:
        if r.get("error"):
            continue
        out.append(f"\n### → {r['target_exam']} ({r['compatibility']})")
        if r.get("missing_dimensions"):
            out.append("**缺失维度**：" + ", ".join(f"`{m}`" for m in r["missing_dimensions"]))
        if r.get("caveats"):
            for c in r["caveats"]:
                out.append(f"- {c}")

    out.append("")
    out.append("---")
    out.append("")
    out.append("## 方法论")
    out.append("")
    out.append("- 推演规则固化自 `references/calibration/cross-exam-analysis.md` §4 + §5；")
    out.append("- CET↔CET 按档次偏移；考研↔考研按档次编号同级映射 + 档内位置保留；")
    out.append("- CET↔考研按全局百分位对齐 × 0.90 partial 衰减（考研语言权重更高）；")
    out.append("- incompatible 情形拒绝输出分数，只列缺失维度和改写建议。")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="跨考试批改推演器（v1.5）",
                                  formatter_class=argparse.RawDescriptionHelpFormatter,
                                  epilog=__doc__)
    ap.add_argument("--source", required=True,
                    choices=list(EXAM_PROFILES.keys()),
                    help="源考试级别")
    ap.add_argument("--source-score", type=float, required=True,
                    help="源考试原始分（0 ~ max）")
    ap.add_argument("--source-subtype", default="argumentative",
                    help="源作文文体（letter / notice / cartoon / chart / argumentative / "
                         "descriptive / narrative / expository）；若提供 --essay-file 会自动检测")
    ap.add_argument("--target", choices=list(EXAM_PROFILES.keys()),
                    help="单个目标考试")
    ap.add_argument("--all", action="store_true",
                    help="对所有 6 个考试做批量推演")
    ap.add_argument("--essay-file", help="作文文件路径（可选，用于字数/文体自检）")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args()

    # 源分数合法性
    src_max = EXAM_PROFILES[args.source]["max"]
    if not (0 <= args.source_score <= src_max):
        print(f"❌ source-score={args.source_score} 超出 {args.source} 合法区间 [0,{src_max}]", file=sys.stderr)
        sys.exit(1)

    essay_text = None
    subtype = args.source_subtype
    if args.essay_file:
        p = Path(args.essay_file)
        if not p.exists():
            print(f"❌ 作文文件不存在: {args.essay_file}", file=sys.stderr)
            sys.exit(1)
        essay_text = p.read_text(encoding="utf-8")
        if args.source_subtype == "argumentative" and not any(
                flag in sys.argv for flag in ["--source-subtype"]):
            subtype = detect_subtype(essay_text)

    if args.all:
        results = estimate_all(args.source, args.source_score, subtype, essay_text)
    elif args.target:
        results = [estimate(args.source, args.source_score, args.target, subtype, essay_text)]
    else:
        ap.error("必须指定 --target 或 --all")

    if args.format == "json":
        print(json.dumps({
            "source": {"exam": args.source, "score": args.source_score, "subtype": subtype},
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        print(render_md(results))


if __name__ == "__main__":
    main()
