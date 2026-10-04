#!/usr/bin/env python3
"""Run deterministic surface-level risk checks on a resume rewrite.

This script does not decide whether a claim is true. It flags newly introduced numbers,
role-escalation words, unresolved placeholders, and obvious formulaic wording so the
user or coach can review them against the source material.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?%?|\d+[+＋]?|[¥￥$]\s*\d+(?:\.\d+)?)")
PLACEHOLDER_PATTERN = re.compile(r"(?:____+|\[[^\]]*(?:待填写|请补充|待确认)[^\]]*\])")

ROLE_TERMS_ZH = ["主导", "牵头", "独立负责", "带领", "管理团队", "决策"]
ROLE_TERMS_EN = ["spearheaded", "led", "owned", "directed", "managed", "architected"]
FORMULAIC_ZH = ["赋能", "打造", "夯实", "抓手", "闭环", "颗粒度", "组合拳", "全方位"]
FORMULAIC_EN = ["spearheaded", "orchestrated", "leveraged", "utilized", "synergy", "cutting-edge"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_numbers(text: str) -> list[str]:
    return sorted(set(NUMBER_PATTERN.findall(text)))


def find_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term.lower() in lowered]


def audit(source: str, rewrite: str) -> dict[str, object]:
    source_numbers = set(extract_numbers(source))
    rewrite_numbers = set(extract_numbers(rewrite))
    added_numbers = sorted(rewrite_numbers - source_numbers)

    source_role_terms = set(find_terms(source, ROLE_TERMS_ZH + ROLE_TERMS_EN))
    rewrite_role_terms = set(find_terms(rewrite, ROLE_TERMS_ZH + ROLE_TERMS_EN))
    added_role_terms = sorted(rewrite_role_terms - source_role_terms)
    placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(rewrite)))
    formulaic_terms = find_terms(rewrite, FORMULAIC_ZH + FORMULAIC_EN)

    issues: list[dict[str, object]] = []
    if added_numbers:
        issues.append(
            {
                "severity": "high",
                "type": "new_numbers",
                "message": "改写中出现源文没有的数字，必须核对来源和口径。",
                "items": added_numbers,
            }
        )
    if added_role_terms:
        issues.append(
            {
                "severity": "high",
                "type": "role_escalation",
                "message": "改写中出现源文没有的高责任角色词，需确认是否存在语气升级。",
                "items": added_role_terms,
            }
        )
    if placeholders:
        issues.append(
            {
                "severity": "medium",
                "type": "unresolved_placeholders",
                "message": "改写仍含占位符，投递前必须补充或删除。",
                "items": placeholders,
            }
        )
    if formulaic_terms:
        issues.append(
            {
                "severity": "low" if len(formulaic_terms) < 3 else "medium",
                "type": "formulaic_language",
                "message": "检测到可能模板化或 AI 化的表达，建议结合语境改为具体动作。",
                "items": formulaic_terms,
            }
        )

    return {
        "summary": {
            "issue_count": len(issues),
            "high_risk_count": sum(issue["severity"] == "high" for issue in issues),
            "requires_user_review": any(issue["severity"] in {"high", "medium"} for issue in issues),
        },
        "issues": issues,
        "limits": [
            "脚本只检查表层文本差异，不能证明陈述真实。",
            "同义改写、技术上下文和责任边界仍需人工语义审核。",
        ],
    }


def render_markdown(result: dict[str, object]) -> str:
    summary = result["summary"]
    lines = [
        "## 简历改写风险检查",
        "",
        f"- 风险项：{summary['issue_count']}",
        f"- 高风险项：{summary['high_risk_count']}",
        f"- 是否需要用户复核：{'是' if summary['requires_user_review'] else '否'}",
        "",
    ]
    issues = result["issues"]
    if not issues:
        lines.append("未发现新增数字、角色升级词、占位符或明显模板化表达。")
    else:
        for issue in issues:
            lines.append(f"### [{issue['severity']}] {issue['type']}")
            lines.append(f"- {issue['message']}")
            lines.append(f"- 命中：{'、'.join(issue['items'])}")
            lines.append("")
    lines.append("> 该检查不能替代事实核对；终稿仍需用户确认。")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="检查简历改写中的表层事实风险。")
    parser.add_argument("--source", required=True, type=Path, help="原始文本文件")
    parser.add_argument("--rewrite", required=True, type=Path, help="候选改写文件")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    result = audit(read_text(args.source), read_text(args.rewrite))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 1 if result["summary"]["high_risk_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
