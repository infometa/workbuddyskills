#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语考试作文字数统计工具（CET + 考研）。

官方规则：
- CET-4（2016 大纲）：120-180 词
- CET-6（2016 大纲）：150-200 词
- 考研英语一/二 A 节（应用文）：约 100 词（下限约 80）
- 考研英语一 B 节：160-200 词
- 考研英语二 B 节：约 150 词（下限约 120）
- 题目给出的起始句/结束句/主题句 **不计入** 字数
- 连字符词 / 缩略词 / 数字 均计 1 个

Usage:
    python word_count.py --essay "<text>" --exam-level CET4
    python word_count.py --essay-file essay.txt --exam-level Postgrad1B \\
                         --given "Given opening sentence."
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|\d+(?:[.,]\d+)*")

# (min, max) —— max=None 表示无硬上限（考研 A 节、英二 B 节允许适度超出）
REQUIREMENTS = {
    "CET4":       (120, 180),
    "CET6":       (150, 200),
    "POSTGRAD1A": (80,  None),   # 英一 A 节，约 100 词
    "POSTGRAD1B": (160, 200),    # 英一 B 节 160-200 词
    "POSTGRAD2A": (80,  None),   # 英二 A 节，约 100 词
    "POSTGRAD2B": (120, None),   # 英二 B 节 约 150 词
}

# 用于错误提示
LEVEL_ALIASES = {
    "cet4": "CET4", "CET4": "CET4",
    "cet6": "CET6", "CET6": "CET6",
    "postgrad1a": "POSTGRAD1A", "Postgrad1A": "POSTGRAD1A", "POSTGRAD1A": "POSTGRAD1A",
    "postgrad1b": "POSTGRAD1B", "Postgrad1B": "POSTGRAD1B", "POSTGRAD1B": "POSTGRAD1B",
    "postgrad2a": "POSTGRAD2A", "Postgrad2A": "POSTGRAD2A", "POSTGRAD2A": "POSTGRAD2A",
    "postgrad2b": "POSTGRAD2B", "Postgrad2B": "POSTGRAD2B", "POSTGRAD2B": "POSTGRAD2B",
}


def count_words(text: str) -> int:
    """
    统计有效英文单词数。

    规则：
    - 连字符词（well-known）计 1 个
    - 缩略词（don't、I'm）计 1 个
    - 纯数字（2026、3.14）计 1 个
    - 英文数字（twenty-six）计 1 个（通过连字符规则自然处理）
    - 中文/标点/空白 不计
    """
    if not text:
        return 0
    return len(WORD_PATTERN.findall(text))


def analyze(
    essay: str,
    given_sentences: list[str] | None = None,
    exam_level: str = "CET4",
) -> dict:
    canonical = LEVEL_ALIASES.get(exam_level) or LEVEL_ALIASES.get(exam_level.lower())
    if canonical is None:
        raise ValueError(
            f"exam_level 必须是 {list(REQUIREMENTS.keys())} 之一（大小写不敏感），"
            f"当前: {exam_level}"
        )
    exam_level = canonical

    requirement_min, requirement_max = REQUIREMENTS[exam_level]
    total_raw = count_words(essay)

    given_sentences = given_sentences or []
    given_deducted = sum(count_words(s) for s in given_sentences)

    effective = max(0, total_raw - given_deducted)
    if requirement_max is None:
        within_range = effective >= requirement_min
        over_limit = False
    else:
        within_range = requirement_min <= effective <= requirement_max
        over_limit = effective > requirement_max
    shortfall = max(0, requirement_min - effective)
    shortfall_ratio = shortfall / requirement_min if requirement_min else 0.0

    if shortfall_ratio == 0:
        penalty_hint = "无"
        penalty_triggered = False
    elif shortfall_ratio <= 0.10:
        penalty_hint = "酌情 0-1 分"
        penalty_triggered = True
    elif shortfall_ratio <= 0.25:
        penalty_hint = "酌情 1-2 分"
        penalty_triggered = True
    elif shortfall_ratio <= 0.50:
        penalty_hint = "酌情 2-3 分"
        penalty_triggered = True
    else:
        penalty_hint = "≥3 分，可能触发降档"
        penalty_triggered = True

    return {
        "exam_level": exam_level,
        "total_raw": total_raw,
        "given_sentences_deducted": given_deducted,
        "effective": effective,
        "requirement_min": requirement_min,
        "requirement_max": requirement_max,
        "within_range": within_range,
        "over_limit": over_limit,
        "shortfall": shortfall,
        "shortfall_ratio": round(shortfall_ratio, 3),
        "penalty_triggered": penalty_triggered,
        "penalty_hint": penalty_hint,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="英语考试作文字数统计（CET + 考研）")
    parser.add_argument("--essay", help="作文正文（直接传入）")
    parser.add_argument("--essay-file", help="作文正文文件路径（UTF-8）")
    parser.add_argument(
        "--given",
        nargs="*",
        default=[],
        help="题目给出的起始/结束/主题句（可多个），不计入字数",
    )
    parser.add_argument(
        "--exam-level",
        choices=list(LEVEL_ALIASES.keys()),
        default="CET4",
        help="考试级别（CET4 / CET6 / Postgrad1A / Postgrad1B / Postgrad2A / Postgrad2B）",
    )
    parser.add_argument("--output", help="输出 JSON 文件路径（默认 stdout）")
    args = parser.parse_args()

    if args.essay_file:
        essay = Path(args.essay_file).read_text(encoding="utf-8")
    elif args.essay:
        essay = args.essay
    else:
        print("❌ 请通过 --essay 或 --essay-file 提供作文正文", file=sys.stderr)
        sys.exit(1)

    result = analyze(essay, args.given, args.exam_level)
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        print(f"✅ 结果已写入 {args.output}")
    print(payload)


if __name__ == "__main__":
    main()
