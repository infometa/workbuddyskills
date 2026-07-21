#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_ai_flavor.py —— AI 文风审计脚本（Provenance 第三维度）

功能：
  扫描简历 markdown / 纯文本，按 references/ai-phrase-blacklist.json 检测
  AI 味短语与高频同义词滥用，输出结构化 JSON 审计报告 + 可选人类可读摘要。

用法：
  python3 scripts/audit_ai_flavor.py --file my-resume.md
  python3 scripts/audit_ai_flavor.py --file - < resume.md
  python3 scripts/audit_ai_flavor.py --text "spearheaded the initiative to ..."
  python3 scripts/audit_ai_flavor.py --file resume.md --pretty --summary
  python3 scripts/audit_ai_flavor.py --file resume.md --lang en --exit-on error

参数：
  --lang auto | en | zh | both   指定扫描语言集（默认 auto：用启发式判断）
  --pretty                       JSON 格式化输出
  --summary                      同时打印人类可读摘要到 stderr
  --exit-on none | warn | error  命中指定级别时以非 0 退出（CI 集成用）
  --blacklist PATH               自定义黑名单 JSON 路径

输出 schema：
  {
    schema_version, tool, input_length_chars, detected_lang,
    summary: {total_hits, by_severity, by_category},
    hits: [
      {term, category, language, severity, count, positions[],
       replacement, reason, lines[]}
    ],
    diversity_warnings: [...],
    recommendations: [...]
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BLACKLIST = SCRIPT_DIR.parent / "references" / "ai-phrase-blacklist.json"


# ============================================================
# 加载黑名单
# ============================================================

def load_blacklist(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"AI 文风黑名单不存在：{path}\n"
            f"  请检查是否缺少 references/ai-phrase-blacklist.json。"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"黑名单 JSON 解析失败：{path} → {e}")

    for key in ("english", "chinese"):
        if key not in data:
            raise ValueError(f"黑名单缺少必需字段：{key}")
    return data


# ============================================================
# 语言识别（启发式）
# ============================================================

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def detect_lang(text: str) -> str:
    """返回 'zh' / 'en' / 'mixed'。启发式：CJK 字符占比。"""
    cjk = len(_CJK_RE.findall(text))
    total = max(1, len([c for c in text if not c.isspace()]))
    ratio = cjk / total
    if ratio > 0.3:
        return "mixed" if ratio < 0.7 else "zh"
    return "en"


# ============================================================
# 核心扫描
# ============================================================

def _positions_english(text_lower: str, term: str) -> list[int]:
    """
    英文词做宽松词边界匹配。
    不用 re.escape + \\b，因为 term 可能含连字符/空格。
    """
    term_l = term.lower()
    positions: list[int] = []

    pattern = r"(?<![A-Za-z0-9_])" + re.escape(term_l) + r"(?![A-Za-z0-9_])"
    for m in re.finditer(pattern, text_lower):
        positions.append(m.start())
    return positions


def _positions_chinese(text: str, term: str) -> list[int]:
    """中文直接 substring（分词成本高，简历短文本接受假阳性）。"""
    positions: list[int] = []
    start = 0
    while True:
        idx = text.find(term, start)
        if idx < 0:
            break
        positions.append(idx)
        start = idx + 1
    return positions


def _line_contexts(text: str, positions: list[int], window: int = 40) -> list[str]:
    """为每个命中位置返回上下文片段（单行内，前后 window 字符截断）。"""
    lines: list[str] = []
    for pos in positions:
        line_start = text.rfind("\n", 0, pos) + 1
        line_end = text.find("\n", pos)
        line_end = len(text) if line_end < 0 else line_end
        line = text[line_start:line_end].strip()
        if len(line) > 120:
            local = pos - line_start
            s = max(0, local - window)
            e = min(len(line), local + window)
            line = ("…" if s > 0 else "") + line[s:e] + ("…" if e < len(line) else "")
        lines.append(line)
    return lines


def _severity_for(count: int, thresholds: dict[str, int]) -> str:
    info_max = thresholds.get("info_max", 2)
    warn_max = thresholds.get("warn_max", 5)
    if count <= info_max:
        return "info"
    if count <= warn_max:
        return "warn"
    return "error"


def scan_bucket(
    text: str,
    text_lower: str,
    bucket: dict[str, dict[str, Any]],
    language: str,
    thresholds: dict[str, int],
) -> list[dict[str, Any]]:
    """扫描某个 category bucket（比如 english.overused_verbs）。"""
    hits: list[dict[str, Any]] = []
    for term, spec in bucket.items():
        if term.startswith("_"):
            continue
        if language == "en":
            positions = _positions_english(text_lower, term)
        else:
            positions = _positions_chinese(text, term)

        if not positions:
            continue

        hits.append({
            "term": term,
            "category": spec.get("category", "unknown"),
            "language": language,
            "severity": _severity_for(len(positions), thresholds),
            "count": len(positions),
            "positions": positions,
            "replacement": spec.get("replacement"),
            "reason": spec.get("reason"),
            "lines": _line_contexts(text, positions),
        })
    return hits


def scan_diversity(
    text: str,
    diversity_spec: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """扫描中文 diversity_limits：同词高频也报 WARN。"""
    warnings: list[dict[str, Any]] = []
    for term, spec in diversity_spec.items():
        if term.startswith("_"):
            continue
        max_allowed = spec.get("max_per_resume", 5)
        positions = _positions_chinese(text, term)
        count = len(positions)
        if count > max_allowed:
            warnings.append({
                "term": term,
                "count": count,
                "max_allowed": max_allowed,
                "severity": "warn",
                "suggestions": spec.get("suggestions", []),
                "note": spec.get("note"),
                "lines_sample": _line_contexts(text, positions[:3]),
            })
    return warnings


def scan_context_sensitive(
    text: str,
    text_lower: str,
    context_spec: dict[str, Any],
    thresholds: dict[str, int],
) -> list[dict[str, Any]]:
    """英文 context_sensitive：同句内 ≥2 个才报 WARN。"""
    items = context_spec.get("items", [])
    if not items:
        return []

    # 拆句（简单：按 . ! ? 换行 拆分）
    sentences = re.split(r"(?<=[\.!?。！？])\s+|\n+", text_lower)
    warnings: list[dict[str, Any]] = []
    for sent in sentences:
        hits_in_sent = [w for w in items if re.search(
            r"(?<![A-Za-z0-9_])" + re.escape(w.lower()) + r"(?![A-Za-z0-9_])", sent
        )]
        if len(hits_in_sent) >= 2:
            warnings.append({
                "terms": hits_in_sent,
                "category": "context_sensitive",
                "severity": "warn",
                "sentence_preview": sent.strip()[:120],
                "reason": "这些词在技术语境单独使用合法，但同句出现 ≥2 个通常是 AI 堆砌",
            })
    return warnings


# ============================================================
# 聚合
# ============================================================

def build_report(text: str, blacklist: dict[str, Any], lang: str) -> dict[str, Any]:
    detected = lang if lang != "auto" else detect_lang(text)
    text_lower = text.lower()
    thresholds = blacklist.get("severity_thresholds", {"info_max": 2, "warn_max": 5})

    all_hits: list[dict[str, Any]] = []
    diversity_warnings: list[dict[str, Any]] = []
    context_warnings: list[dict[str, Any]] = []

    run_en = detected in ("en", "mixed") or lang == "en" or lang == "both"
    run_zh = detected in ("zh", "mixed") or lang == "zh" or lang == "both"

    if run_en:
        en = blacklist.get("english", {})
        for bucket_key in ("overused_verbs", "corporate_buzzwords", "filler_phrases",
                           "punctuation_signals"):
            all_hits.extend(scan_bucket(
                text, text_lower, en.get(bucket_key, {}), "en", thresholds
            ))
        context_warnings.extend(scan_context_sensitive(
            text, text_lower, en.get("context_sensitive", {}), thresholds
        ))

    if run_zh:
        zh = blacklist.get("chinese", {})
        for bucket_key in ("buzzword_verbs", "buzzword_nouns", "empty_phrases"):
            all_hits.extend(scan_bucket(
                text, text_lower, zh.get(bucket_key, {}), "zh", thresholds
            ))
        diversity_warnings.extend(scan_diversity(
            text, zh.get("diversity_limits", {})
        ))

    # 聚合统计
    by_severity: dict[str, int] = {"info": 0, "warn": 0, "error": 0}
    by_category: dict[str, int] = {}
    for h in all_hits:
        by_severity[h["severity"]] = by_severity.get(h["severity"], 0) + 1
        by_category[h["category"]] = by_category.get(h["category"], 0) + 1
    for w in diversity_warnings + context_warnings:
        by_severity[w["severity"]] = by_severity.get(w["severity"], 0) + 1

    recommendations: list[str] = []
    if by_severity["error"] > 0:
        recommendations.append("存在 ERROR 级别 AI 味命中，建议逐条替换后重新审计。")
    if by_severity["warn"] > 3:
        recommendations.append("WARN 数量偏高，建议整体降低套路用词密度。")
    if by_severity.get("info", 0) > 0 and by_severity["warn"] == 0 and by_severity["error"] == 0:
        recommendations.append("仅 INFO 级提示，可选择性替换或保留。")
    if not all_hits and not diversity_warnings and not context_warnings:
        recommendations.append("未检出 AI 文风命中，整体语感较自然。")

    return {
        "schema_version": "0.3",
        "tool": "audit_ai_flavor.py",
        "blacklist_version": blacklist.get("_meta", {}).get("schema_version", "unknown"),
        "input_length_chars": len(text),
        "detected_lang": detected,
        "scanned_langs": [l for l, run in [("en", run_en), ("zh", run_zh)] if run],
        "summary": {
            "total_hits": len(all_hits),
            "by_severity": by_severity,
            "by_category": by_category,
            "diversity_warnings": len(diversity_warnings),
            "context_warnings": len(context_warnings),
        },
        "hits": sorted(all_hits, key=lambda x: (-x["count"], x["term"])),
        "diversity_warnings": diversity_warnings,
        "context_warnings": context_warnings,
        "recommendations": recommendations,
    }


# ============================================================
# 人类可读摘要
# ============================================================

SEVERITY_ICONS = {"info": "·", "warn": "!", "error": "!!"}


def format_summary(report: dict[str, Any]) -> str:
    lines: list[str] = []
    s = report["summary"]
    lines.append(f"AI 文风审计 —— 扫描语言：{', '.join(report['scanned_langs'])} "
                 f"（检测为 {report['detected_lang']}）")
    lines.append(f"  总命中：{s['total_hits']}  "
                 f"[error: {s['by_severity']['error']} | "
                 f"warn: {s['by_severity']['warn']} | "
                 f"info: {s['by_severity']['info']}]")
    if s.get("diversity_warnings"):
        lines.append(f"  同词高频：{s['diversity_warnings']} 处")
    if s.get("context_warnings"):
        lines.append(f"  语境堆砌：{s['context_warnings']} 处")

    if report["hits"]:
        lines.append("")
        lines.append("命中词：")
        for h in report["hits"][:15]:
            icon = SEVERITY_ICONS[h["severity"]]
            rep = f" → {h['replacement']}" if h.get("replacement") else ""
            lines.append(f"  {icon} [{h['severity']:5s}] {h['term']:22s} "
                         f"x{h['count']}  ({h['category']}, {h['language']}){rep}")
            if h.get("reason"):
                lines.append(f"      原因：{h['reason']}")
        if len(report["hits"]) > 15:
            lines.append(f"  ...（还有 {len(report['hits']) - 15} 条，见 JSON）")

    if report["diversity_warnings"]:
        lines.append("")
        lines.append("同词高频告警：")
        for w in report["diversity_warnings"]:
            suggs = " / ".join(w["suggestions"]) if w["suggestions"] else "（无推荐）"
            lines.append(f"  ! 「{w['term']}」出现 {w['count']} 次（建议 ≤ {w['max_allowed']}）"
                         f" → 可替换为：{suggs}")

    if report["context_warnings"]:
        lines.append("")
        lines.append("语境堆砌告警：")
        for w in report["context_warnings"][:5]:
            lines.append(f"  ! {' + '.join(w['terms'])} → {w['sentence_preview']}")

    if report["recommendations"]:
        lines.append("")
        lines.append("建议：")
        for r in report["recommendations"]:
            lines.append(f"  • {r}")

    return "\n".join(lines)


# ============================================================
# I/O
# ============================================================

def load_input(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if not args.file:
        raise ValueError("必须提供 --file 或 --text")
    if args.file == "-":
        return sys.stdin.read()
    p = Path(args.file)
    if not p.exists():
        raise FileNotFoundError(f"输入文件不存在：{p}")
    return p.read_text(encoding="utf-8")


# ============================================================
# CLI
# ============================================================

EXIT_CODES = {"none": 0, "info": 0, "warn": 0, "error": 0}  # placeholder


def decide_exit_code(report: dict[str, Any], trigger: str) -> int:
    """根据 --exit-on 决定返回码。"""
    sev = report["summary"]["by_severity"]
    if trigger == "none":
        return 0
    if trigger == "warn" and (sev["warn"] > 0 or sev["error"] > 0):
        return 3
    if trigger == "error" and sev["error"] > 0:
        return 3
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI 文风审计（Provenance 第三维度）：扫描简历内容是否含 AI 味短语。",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径，用 '-' 读 stdin")
    src.add_argument("--text", help="文本字符串")

    parser.add_argument(
        "--lang",
        choices=["auto", "en", "zh", "both"],
        default="auto",
        help="扫描语言（默认 auto：按文本启发式识别）",
    )
    parser.add_argument(
        "--blacklist",
        type=Path,
        default=DEFAULT_BLACKLIST,
        help=f"黑名单 JSON 路径（默认：{DEFAULT_BLACKLIST.relative_to(SCRIPT_DIR.parent)}）",
    )
    parser.add_argument("--pretty", action="store_true", help="JSON 格式化")
    parser.add_argument("--summary", action="store_true", help="同时打印人类可读摘要到 stderr")
    parser.add_argument(
        "--exit-on",
        choices=["none", "warn", "error"],
        default="none",
        help="命中指定级别时以非 0 退出（CI 集成用，默认 none = 始终 0）",
    )
    parser.add_argument("--out", help="将 JSON 写入文件（默认 stdout）")

    args = parser.parse_args(argv)

    try:
        blacklist = load_blacklist(args.blacklist)
        text = load_input(args)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    report = build_report(text, blacklist, args.lang)

    payload = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    else:
        print(payload)

    if args.summary:
        print(format_summary(report), file=sys.stderr)

    return decide_exit_code(report, args.exit_on)


if __name__ == "__main__":
    sys.exit(main())
