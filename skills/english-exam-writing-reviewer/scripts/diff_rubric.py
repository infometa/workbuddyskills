#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_rubric.py —— 跨考试/跨级别 rubric 对比工具（v1.4 新增）

功能：给定两个或多个 exam_level，打印核心评分规则差异表。
常用于：
    - 教师备课："我用 CET-6 标准去备英一 B 该注意什么？"
    - 考生决策："我目前 CET-4 中档，目标考研英一 B 要补哪些维度？"
    - Skill 内部：跨考试推演前快速校验 rubric 差异。

使用：
    python diff_rubric.py CET4 Postgrad1B                  # 两两对比
    python diff_rubric.py CET6 Postgrad1B Postgrad2B       # 多级别对比
    python diff_rubric.py --all                            # 全 6 级别对比
    python diff_rubric.py CET4 Postgrad1B --format json    # 机读输出

依赖：仅标准库。
"""

from __future__ import annotations

import argparse
import json
import sys


# ===== 各考试的核心 rubric 配置 =====
RUBRICS: dict[str, dict] = {
    "CET4": {
        "full_name": "全国大学英语四级",
        "score_max": 15,
        "report_score_max": 106.5,
        "band_count": 5,
        "bands": [
            ("第五档", 14, "13-15"),
            ("第四档", 11, "10-12"),
            ("第三档",  8,  "7-9"),
            ("第二档",  5,  "4-6"),
            ("第一档",  2,  "1-3"),
        ],
        "score_increment": 1,
        "word_count": "120-180",
        "dominant_subtypes": ["argumentative"],
        "scoring_method": "整体印象评分法（holistic）",
        "explicit_dimensions": 0,
        "implicit_dimensions": ["切题度", "表达清晰度", "连贯性", "语言准确度"],
        "special_rules": [
            "字数不足 120 按比例扣分",
            "字数少于 60 词最高不超过 7 分",
            "偏题降 1-2 档",
        ],
        "directions_copy_check": False,
        "signature_required": False,
        "data_accuracy_scoring": False,
        "reference_file": "references/official-rubric.md",
    },
    "CET6": {
        "full_name": "全国大学英语六级",
        "score_max": 15,
        "report_score_max": 106.5,
        "band_count": 5,
        "bands": [
            ("第五档", 14, "13-15"),
            ("第四档", 11, "10-12"),
            ("第三档",  8,  "7-9"),
            ("第二档",  5,  "4-6"),
            ("第一档",  2,  "1-3"),
        ],
        "score_increment": 1,
        "word_count": "150-200",
        "dominant_subtypes": ["argumentative"],
        "scoring_method": "整体印象评分法（holistic）",
        "explicit_dimensions": 0,
        "implicit_dimensions": ["切题度", "表达清晰度", "连贯性", "语言准确度"],
        "special_rules": [
            "字数不足 150 按比例扣分",
            "语言要求比 CET-4 更『流畅自然』",
            "词汇和语法结构的多样性权重更高",
        ],
        "directions_copy_check": False,
        "signature_required": False,
        "data_accuracy_scoring": False,
        "reference_file": "references/official-rubric.md",
    },
    "Postgrad1A": {
        "full_name": "考研英语一 A 节（应用文）",
        "score_max": 10,
        "report_score_max": 10,
        "band_count": 5,
        "bands": [
            ("第五档", 5, "9-10"),
            ("第四档", 4, "7-8"),
            ("第三档", 3, "5-6"),
            ("第二档", 2, "3-4"),
            ("第一档", 1, "1-2"),
        ],
        "score_increment": 0.5,
        "word_count": "约 100 词（60-120 可接受）",
        "dominant_subtypes": ["letter", "announcement", "memorandum"],
        "scoring_method": "档次制 + 总体印象评分法",
        "explicit_dimensions": 5,
        "implicit_dimensions": ["任务完成度", "语法结构与词汇", "语言准确性",
                                "衔接与连贯", "格式与语域"],
        "special_rules": [
            "连续 8 词以上与 Directions 原文一致扣 0.5-2 分",
            "署名违反 Directions 要求（如要求 Li Ming 却签真名）扣 0.5 分",
            "字数严重偏短按比例扣分（shortfall_ratio > 0.3 触发降档）",
            "格式错误（缺称呼/落款）critical 级降档",
        ],
        "directions_copy_check": True,
        "signature_required": True,
        "data_accuracy_scoring": False,
        "reference_file": "references/postgrad-official-rubric.md",
    },
    "Postgrad1B": {
        "full_name": "考研英语一 B 节（短文写作，图画论述）",
        "score_max": 20,
        "report_score_max": 20,
        "band_count": 5,
        "bands": [
            ("第五档", 5, "17-20"),
            ("第四档", 4, "13-16"),
            ("第三档", 3, "9-12"),
            ("第二档", 2, "5-8"),
            ("第一档", 1, "1-4"),
        ],
        "score_increment": 0.5,
        "word_count": "160-200 词",
        "dominant_subtypes": ["cartoon", "descriptive", "narrative", "expository"],
        "scoring_method": "档次制 + 总体印象评分法",
        "explicit_dimensions": 5,
        "implicit_dimensions": ["任务完成度", "语法结构与词汇", "语言准确性",
                                "衔接与连贯", "格式与语域"],
        "special_rules": [
            "三要点缺一降一档（描述/寓意/评论）",
            "字数不足 160 按 shortfall_ratio 扣 1-2 分，> 0.5 触发跨档下跌",
            "辩证维度不足 → 第四档高位降至低位",
        ],
        "directions_copy_check": False,
        "signature_required": False,
        "data_accuracy_scoring": False,
        "reference_file": "references/postgrad-official-rubric.md",
    },
    "Postgrad2A": {
        "full_name": "考研英语二 A 节（应用文）",
        "score_max": 10,
        "report_score_max": 10,
        "band_count": 5,
        "bands": [
            ("第五档", 5, "9-10"),
            ("第四档", 4, "7-8"),
            ("第三档", 3, "5-6"),
            ("第二档", 2, "3-4"),
            ("第一档", 1, "1-2"),
        ],
        "score_increment": 0.5,
        "word_count": "约 100 词",
        "dominant_subtypes": ["letter", "notice", "announcement"],
        "scoring_method": "档次制 + 总体印象评分法",
        "explicit_dimensions": 5,
        "implicit_dimensions": ["任务完成度", "语法结构与词汇", "语言准确性",
                                "衔接与连贯", "格式与语域"],
        "special_rules": [
            "与英一 A 扣分规则一致（Directions 照搬、署名、字数）",
            "notice / announcement 语域要求中性偏正式",
        ],
        "directions_copy_check": True,
        "signature_required": True,
        "data_accuracy_scoring": False,
        "reference_file": "references/postgrad-official-rubric.md",
    },
    "Postgrad2B": {
        "full_name": "考研英语二 B 节（短文写作，图表说明）",
        "score_max": 15,
        "report_score_max": 15,
        "band_count": 5,
        "bands": [
            ("第五档", 5, "13-15"),
            ("第四档", 4, "10-12"),
            ("第三档", 3, "7-9"),
            ("第二档", 2, "4-6"),
            ("第一档", 1, "1-3"),
        ],
        "score_increment": 0.5,
        "word_count": "约 150 词",
        "dominant_subtypes": ["chart", "table", "pie_chart"],
        "scoring_method": "档次制 + 总体印象评分法",
        "explicit_dimensions": 5,
        "implicit_dimensions": ["任务完成度", "语法结构与词汇", "语言准确性",
                                "衔接与连贯", "格式与语域"],
        "special_rules": [
            "**数据精准度是额外扣分维度**（独有）：关键数据错位 ≥ 2 处扣 1-2 分",
            "图表专用动词错用（take 40% → account for）warning 级",
            "原因分析需有主次结构",
        ],
        "directions_copy_check": False,
        "signature_required": False,
        "data_accuracy_scoring": True,
        "reference_file": "references/postgrad-official-rubric.md",
    },
}


def render_bands(rubric: dict) -> str:
    return " / ".join(f"{n}({r})" for n, _, r in rubric["bands"])


def render_dimensions(rubric: dict) -> str:
    if rubric["explicit_dimensions"] == 0:
        return f"（隐含 {len(rubric['implicit_dimensions'])} 维：" + \
               " · ".join(rubric["implicit_dimensions"]) + "）"
    return f"显式 {rubric['explicit_dimensions']} 维：" + \
           " · ".join(rubric["implicit_dimensions"])


def render_table(levels: list[str]) -> str:
    if any(lv not in RUBRICS for lv in levels):
        invalid = [lv for lv in levels if lv not in RUBRICS]
        return f"❌ 未知 exam_level: {invalid}"

    rows: list[tuple[str, list[str]]] = []

    def add(label: str, getter):
        rows.append((label, [str(getter(RUBRICS[lv])) for lv in levels]))

    add("中文全称",        lambda r: r["full_name"])
    add("满分",            lambda r: f'{r["score_max"]} 分')
    add("报告分满分",      lambda r: f'{r["report_score_max"]}')
    add("分数增量",        lambda r: f'{r["score_increment"]} 分（{"允许半分" if r["score_increment"]==0.5 else "仅整数"}）')
    add("档次数",          lambda r: r["band_count"])
    add("档次分布",        render_bands)
    add("评分方法",        lambda r: r["scoring_method"])
    add("字数要求",        lambda r: r["word_count"])
    add("主流题型",        lambda r: " / ".join(r["dominant_subtypes"]))
    add("评分维度",        render_dimensions)
    add("Directions 检测", lambda r: "✅ 启用" if r["directions_copy_check"] else "❌ 不适用")
    add("署名检查",        lambda r: "✅ 启用" if r["signature_required"] else "❌ 不适用")
    add("数据精准度维度",  lambda r: "✅ 启用（独有）" if r["data_accuracy_scoring"] else "❌ 不适用")
    add("参考文件",        lambda r: r["reference_file"])

    # 特殊规则单列一段
    out = []
    header = "| 对比维度 | " + " | ".join(levels) + " |"
    sep = "|" + "|".join("---" for _ in range(len(levels) + 1)) + "|"
    out.append(header)
    out.append(sep)
    for label, cells in rows:
        out.append(f"| **{label}** | " + " | ".join(cells) + " |")

    out.append("")
    out.append("## 特殊规则对比")
    for lv in levels:
        out.append(f"\n### {lv} — {RUBRICS[lv]['full_name']}")
        for rule in RUBRICS[lv]["special_rules"]:
            out.append(f"- {rule}")

    return "\n".join(out)


def render_differences(levels: list[str]) -> str:
    """提取关键差异点。"""
    if len(levels) != 2:
        return ""

    a, b = levels
    ra, rb = RUBRICS[a], RUBRICS[b]
    out = [f"\n## 关键差异：{a} → {b}"]

    deltas = []
    if ra["score_max"] != rb["score_max"]:
        deltas.append(f"- **满分变化**：{ra['score_max']} → {rb['score_max']}")
    if ra["score_increment"] != rb["score_increment"]:
        deltas.append(f"- **分数增量**：{ra['score_increment']} → {rb['score_increment']}"
                      f"（{b} {'允许' if rb['score_increment']==0.5 else '不允许'}半分）")
    if ra["directions_copy_check"] != rb["directions_copy_check"]:
        deltas.append(f"- **Directions 检测**：{ra['directions_copy_check']} → "
                      f"{rb['directions_copy_check']}"
                      f"（从 {a} 转到 {b} 需{'启用' if rb['directions_copy_check'] else '禁用'}该检测）")
    if ra["signature_required"] != rb["signature_required"]:
        deltas.append(f"- **署名检查**：{ra['signature_required']} → {rb['signature_required']}")
    if ra["data_accuracy_scoring"] != rb["data_accuracy_scoring"]:
        deltas.append(f"- **数据精准度**：{ra['data_accuracy_scoring']} → "
                      f"{rb['data_accuracy_scoring']}"
                      f"（{'启用图表独有扣分' if rb['data_accuracy_scoring'] else '取消图表独有扣分'}）")
    if ra["word_count"] != rb["word_count"]:
        deltas.append(f"- **字数要求**：{ra['word_count']} → {rb['word_count']}")
    if set(ra["dominant_subtypes"]) != set(rb["dominant_subtypes"]):
        deltas.append(f"- **主流题型**：{'/'.join(ra['dominant_subtypes'])} → "
                      f"{'/'.join(rb['dominant_subtypes'])}")

    if not deltas:
        out.append("_（未发现关键差异；建议扩大对比维度）_")
    else:
        out.extend(deltas)

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="跨考试 rubric 对比工具")
    ap.add_argument("levels", nargs="*",
                    help="要对比的 exam_level（2 个或多个）")
    ap.add_argument("--all", action="store_true",
                    help="对比全部 6 个 exam_level")
    ap.add_argument("--format", choices=["md", "json"], default="md",
                    help="输出格式")
    args = ap.parse_args()

    if args.all:
        levels = list(RUBRICS.keys())
    else:
        levels = args.levels

    if len(levels) < 2:
        ap.print_help()
        print("\n❌ 至少需要 2 个 exam_level", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        payload = {lv: RUBRICS[lv] for lv in levels if lv in RUBRICS}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"# 跨考试 rubric 对比：{' vs '.join(levels)}\n")
    print(render_table(levels))
    if len(levels) == 2:
        print(render_differences(levels))


if __name__ == "__main__":
    main()
