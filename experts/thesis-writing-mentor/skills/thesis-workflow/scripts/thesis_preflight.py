#!/usr/bin/env python3
"""Dependency-free preflight checks for thesis Markdown/plain-text drafts.

This is a deterministic text audit. It does not verify research truth, statistical
correctness, journal fit, or visual layout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PLACEHOLDER_PATTERNS = [
    r"AUTHOR_INPUT_NEEDED",
    r"\[TODO(?::[^\]]*)?\]",
    r"\[待补(?:充|证据|数据|引用)?\]",
    r"待核验",
]

OVERCLAIM_TERMS = [
    "首次证明",
    "填补了空白",
    "完全证明",
    "必然导致",
    "普遍适用",
    "unprecedented",
    "proves that",
    "always",
    "never",
]

AI_SLOP_TERMS = [
    "具有重要意义",
    "不言而喻",
    "毋庸置疑",
    "值得注意的是",
    "it is worth noting that",
    "plays a crucial role",
]


def issue(code: str, severity: str, message: str, line: int | None = None) -> dict:
    item = {"code": code, "severity": severity, "message": message}
    if line is not None:
        item["line"] = line
    return item


def line_number(text: str, start: int) -> int:
    return text.count("\n", 0, start) + 1


def audit(text: str) -> dict:
    issues: list[dict] = []

    for pattern in PLACEHOLDER_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            issues.append(issue("PLACEHOLDER", "P0", f"存在未关闭占位符：{match.group(0)}", line_number(text, match.start())))

    for term in OVERCLAIM_TERMS:
        for match in re.finditer(re.escape(term), text, re.IGNORECASE):
            issues.append(issue("OVERCLAIM", "P1", f"可能存在无边界强化主张：{match.group(0)}", line_number(text, match.start())))

    for term in AI_SLOP_TERMS:
        for match in re.finditer(re.escape(term), text, re.IGNORECASE):
            issues.append(issue("VAGUE_LANGUAGE", "P2", f"建议检查空泛或模板化表达：{match.group(0)}", line_number(text, match.start())))

    headings = []
    for idx, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((idx, len(match.group(1)), match.group(2)))
    for previous, current in zip(headings, headings[1:]):
        if current[1] > previous[1] + 1:
            issues.append(issue("HEADING_JUMP", "P2", f"标题层级从 H{previous[1]} 跳到 H{current[1]}：{current[2]}", current[0]))

    caption_patterns = (
        ("图", r"(?im)^\s*(?:图|Fig(?:ure)?\.?)\s*([A-Za-z]?\d+)\s*[：:. ]"),
        ("表", r"(?im)^\s*(?:表|Table)\s*([A-Za-z]?\d+)\s*[：:. ]"),
    )
    for kind, pattern in caption_patterns:
        captions = re.findall(pattern, text)
        duplicates = [value for value, count in Counter(captions).items() if count > 1]
        if duplicates:
            issues.append(issue("DUPLICATE_CAPTION", "P2", f"{kind}题注编号可能重复：{', '.join(sorted(duplicates))}"))

    cn_citations = set(re.findall(r"\[(\d+)\]", text))
    refs_match = re.search(r"(?im)^#{0,6}\s*(参考文献|references)\s*$", text)
    if cn_citations and refs_match:
        body_citations = set(re.findall(r"\[(\d+)\]", text[: refs_match.start()]))
        ref_numbers = set(re.findall(r"(?m)^\s*\[(\d+)\]", text[refs_match.end() :]))
        missing_refs = sorted(body_citations - ref_numbers, key=int)
        uncited_refs = sorted(ref_numbers - body_citations, key=int)
        if missing_refs:
            issues.append(issue("MISSING_REFERENCE", "P0", f"正文引用缺少参考文献条目：{', '.join(missing_refs)}"))
        if uncited_refs:
            issues.append(issue("UNCITED_REFERENCE", "P1", f"参考文献未在正文引用：{', '.join(uncited_refs)}"))

    severity_counts = Counter(item["severity"] for item in issues)
    return {
        "status": "FAIL" if severity_counts["P0"] else "WARN" if issues else "PASS",
        "summary": {"P0": severity_counts["P0"], "P1": severity_counts["P1"], "P2": severity_counts["P2"]},
        "issues": issues,
        "limitations": [
            "只做确定性文本预检，不验证研究事实、统计分析、期刊适配或版式渲染。",
            "图表检查只识别独立成行的题注，正文交叉引用与复杂排版仍需人工复核。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a thesis Markdown or text file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true", help="Treat P1/P2 warnings as failure.")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2
    text = args.input.read_text(encoding="utf-8")
    result = audit(text)

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {result['status']}")
        print(f"P0={result['summary']['P0']} P1={result['summary']['P1']} P2={result['summary']['P2']}")
        for item in result["issues"]:
            location = f" line {item['line']}" if "line" in item else ""
            print(f"[{item['severity']}] {item['code']}{location}: {item['message']}")
        for note in result["limitations"]:
            print(f"LIMIT: {note}")

    if result["summary"]["P0"]:
        return 1
    if args.strict and result["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
