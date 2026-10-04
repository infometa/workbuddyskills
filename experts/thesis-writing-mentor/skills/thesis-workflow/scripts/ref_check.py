#!/usr/bin/env python3
"""只读参考文献文本预检：字段、GB/T 7714 常见标点与重复条目。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

TYPE_PATTERN = re.compile(r"\[(J|M|D|C|N|R|S|P|EB/OL|DB/OL|CP/DK|Z)\]", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
NUMBERING_PATTERN = re.compile(r"^\s*(?:\[\d+\]|\d+[.)、])\s*")


def split_entries(text: str) -> list[str]:
    """按非空行读取条目；忽略单独的参考文献标题。"""
    entries = []
    for line in text.splitlines():
        value = line.strip()
        if not value or value.lower() in {"参考文献", "references"}:
            continue
        entries.append(value)
    return entries


def strip_numbering(entry: str) -> str:
    return NUMBERING_PATTERN.sub("", entry, count=1).strip()


def extract_doi(entry: str) -> str | None:
    match = DOI_PATTERN.search(entry)
    if not match:
        return None
    return match.group(0).rstrip(".,;。；").lower()


def extract_title(entry: str) -> str | None:
    value = strip_numbering(entry)
    type_match = TYPE_PATTERN.search(value)
    if type_match:
        prefix = value[: type_match.start()].strip(" .。")
        parts = [part.strip() for part in re.split(r"[.。]", prefix) if part.strip()]
        if len(parts) >= 2:
            return parts[-1]
    parts = [part.strip() for part in re.split(r"[.。]", value) if part.strip()]
    if len(parts) >= 2:
        return parts[1]
    return None


def normalize_title(title: str | None) -> str | None:
    if not title:
        return None
    value = unicodedata.normalize("NFKC", title).casefold()
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)
    return value or None


def has_author(entry: str) -> bool:
    value = strip_numbering(entry)
    prefix = re.split(r"[.。]", value, maxsplit=1)[0].strip()
    return bool(prefix and re.search(r"[A-Za-z\u4e00-\u9fff]", prefix))


def has_source(entry: str) -> bool:
    type_match = TYPE_PATTERN.search(entry)
    if not type_match:
        return False
    tail = entry[type_match.end() :].lstrip(" .。")
    year_match = YEAR_PATTERN.search(tail)
    source = tail[: year_match.start()] if year_match else re.split(r"[,，]", tail, maxsplit=1)[0]
    return bool(source.strip(" ,，.。"))


def journal_details(entry: str) -> tuple[bool, bool, bool]:
    year_match = YEAR_PATTERN.search(entry)
    tail = entry[year_match.end() :] if year_match else entry
    volume_match = re.search(r"[,，]\s*(\d+)\s*(?:\(|（|:|：)", tail)
    issue_match = re.search(r"[（(]\s*\d+\s*[）)]", tail)
    pages_match = re.search(r"[:：]\s*[A-Za-z]?\d+\s*[-–—]\s*[A-Za-z]?\d+", tail)
    return bool(volume_match), bool(issue_match), bool(pages_match)


def field_completeness(entries: list[str]) -> dict:
    items = []
    complete_count = 0
    for index, entry in enumerate(entries, start=1):
        missing = []
        hints = []
        if not has_author(entry):
            missing.append("author")
        if not YEAR_PATTERN.search(entry):
            missing.append("year")
        if not extract_title(entry):
            missing.append("title")
        if not has_source(entry):
            missing.append("source")

        type_match = TYPE_PATTERN.search(entry)
        if type_match and type_match.group(1).upper() == "J":
            has_volume, has_issue, has_pages = journal_details(entry)
            if not has_volume:
                missing.append("volume")
            if not has_issue:
                missing.append("issue")
            if not has_pages:
                missing.append("pages")

        if not extract_doi(entry):
            hints.append("DOI 未提供；仅在该文献确有 DOI 且学校或期刊要求时补充，不据此判定条目错误。")

        complete = not missing
        complete_count += int(complete)
        items.append({
            "entry": index,
            "complete": complete,
            "missing": missing,
            "hints": hints,
        })

    return {
        "complete_count": complete_count,
        "incomplete_count": len(entries) - complete_count,
        "items": items,
    }


def punctuation_report(entries: list[str]) -> dict:
    issues = []
    for index, entry in enumerate(entries, start=1):
        value = strip_numbering(entry)
        type_match = TYPE_PATTERN.search(value)
        if not type_match:
            issues.append({"entry": index, "code": "MISSING_TYPE_MARKER", "message": "缺少常见文献类型标识，如 [J]、[M] 或 [D]。"})
        else:
            following = value[type_match.end() :]
            if not re.match(r"\s*[.。]", following):
                issues.append({"entry": index, "code": "PUNCT_AFTER_TYPE", "message": "文献类型标识后通常应使用句点分隔来源。"})

        if re.search(r"[，：；]", value):
            issues.append({"entry": index, "code": "FULLWIDTH_SEPARATOR", "message": "著录字段之间出现全角逗号、冒号或分号，请按学校采用的 GB/T 7714 样式核对半角标点。"})

        if type_match and type_match.group(1).upper() == "J":
            year_match = YEAR_PATTERN.search(value)
            tail = value[year_match.end() :] if year_match else value
            if re.search(r"[,，]\s*\d+\s*[（(]\d+[）)]\s+\d+\s*[-–—]\s*\d+", tail):
                issues.append({"entry": index, "code": "MISSING_PAGE_COLON", "message": "卷(期)与页码之间疑似缺少冒号。"})

        if not re.search(r"[.。]\s*$", value):
            issues.append({"entry": index, "code": "MISSING_TERMINAL_PERIOD", "message": "条目末尾缺少句点。"})

    return {"issue_count": len(issues), "issues": issues}


def duplicate_report(entries: list[str]) -> dict:
    doi_groups: dict[str, list[int]] = defaultdict(list)
    title_groups: dict[str, list[int]] = defaultdict(list)
    titles: dict[int, str] = {}

    for index, entry in enumerate(entries, start=1):
        doi = extract_doi(entry)
        if doi:
            doi_groups[doi].append(index)
        title = extract_title(entry)
        normalized = normalize_title(title)
        if normalized:
            title_groups[normalized].append(index)
            titles[index] = title or ""

    groups = []
    doi_covered: set[int] = set()
    for doi, indexes in sorted(doi_groups.items()):
        if len(indexes) > 1:
            groups.append({"method": "doi", "key": doi, "entries": indexes})
            doi_covered.update(indexes)

    for normalized, indexes in sorted(title_groups.items()):
        remaining = [index for index in indexes if index not in doi_covered]
        if len(remaining) > 1:
            groups.append({
                "method": "normalized_title",
                "key": normalized,
                "title": titles[remaining[0]],
                "entries": remaining,
                "note": "标题重复为次级提示；作者、年份或版本冲突时需人工核对。",
            })

    return {"group_count": len(groups), "groups": groups}


def audit(text: str) -> dict:
    entries = split_entries(text)
    fields = field_completeness(entries)
    punctuation = punctuation_report(entries)
    duplicates = duplicate_report(entries)
    has_errors = bool(fields["incomplete_count"] or punctuation["issue_count"] or duplicates["group_count"])
    return {
        "status": "WARN" if has_errors else "PASS",
        "entry_count": len(entries),
        "field_completeness": fields,
        "punctuation": punctuation,
        "duplicates": duplicates,
        "limitations": [
            "仅做确定性文本预检，不联网、不核验文献真伪，也不写回输入文件。",
            "字段和标点规则是 GB/T 7714 常见模式提示，学校或期刊当前要求优先。",
            "缺少 DOI 仅作为核对提示，不代表该文献或条目必然错误。",
        ],
    }


def render_text(result: dict) -> str:
    lines = [
        f"状态: {result['status']}",
        f"条目数: {result['entry_count']}",
        "",
        "[字段完整性]",
        f"完整 {result['field_completeness']['complete_count']}，不完整 {result['field_completeness']['incomplete_count']}",
    ]
    for item in result["field_completeness"]["items"]:
        if item["missing"]:
            lines.append(f"- 条目 {item['entry']}: 缺少 {', '.join(item['missing'])}")
        for hint in item["hints"]:
            lines.append(f"- 条目 {item['entry']} 提示: {hint}")

    lines.extend(["", "[GB/T 7714 常见标点]"])
    if result["punctuation"]["issues"]:
        for item in result["punctuation"]["issues"]:
            lines.append(f"- 条目 {item['entry']} {item['code']}: {item['message']}")
    else:
        lines.append("- 未发现常见标点问题")

    lines.extend(["", "[重复条目]"])
    if result["duplicates"]["groups"]:
        for group in result["duplicates"]["groups"]:
            lines.append(f"- {group['method']} {group['key']}: 条目 {', '.join(map(str, group['entries']))}")
    else:
        lines.append("- 未发现重复条目")

    lines.extend(["", *[f"限制: {item}" for item in result["limitations"]]])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查参考文献字段、GB/T 7714 常见标点和重复条目。")
    parser.add_argument("input", type=Path, help="UTF-8 或 UTF-8 BOM 参考文献文本文件")
    parser.add_argument("--json", action="store_true", dest="as_json", help="输出 JSON")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"输入文件不存在: {args.input}", file=sys.stderr)
        return 2

    try:
        text = args.input.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        print(f"无法读取输入文件: {exc}", file=sys.stderr)
        return 2

    result = audit(text)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
