#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrate.py —— calibration 集回归测试 + 覆盖矩阵生成器（v1.4 新增）

功能
----
1. 扫描 references/calibration/samples/** 下所有 .md 样例；
2. 解析每个样例的 YAML front-matter（exam_level / task_subtype / band /
   raw_score / raw_score_max 等元数据）；
3. 抽取样例内 "## 回归测试预期值" 下的第一个 JSON block，作为该样例的
   **预期输出**；
4. 输出 6 类报告：
   - 【表格】覆盖矩阵：exam_level × band（看哪些格子缺样例）
   - 【表格】文体矩阵：exam_level × task_subtype（v1.2 新增）
   - 【表格】v1.6 细粒度子类矩阵（letter_category × chart_subtype × calibration_status）
   - 【文本】金标样例清单（带 gold-standard/anchor_tags 的样例）
   - 【文本】低频/理论题型清单（low_frequency_theoretical 标记）
   - 【JSON】机读的 regression_expectations（供 CI 或 Skill 自检用）

使用
----
    python calibrate.py                      # 默认扫描当前 skill 的 references/calibration 目录
    python calibrate.py --format json        # 仅输出机读 JSON
    python calibrate.py --coverage-only      # 仅输出覆盖矩阵
    python calibrate.py --check-band-range   # 额外校验 raw_score ∈ band 区间
    python calibrate.py --check-v16          # v1.6 新字段合法性校验（letter_category / chart_subtype / calibration_status 枚举）

依赖：仅标准库（re / json / yaml-less 手写解析，不依赖 PyYAML）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ===== 各考试合法 band → (raw_score 区间) =====
BAND_RANGES = {
    "CET4":       {14:(13,15), 11:(10,12), 8:(7,9), 5:(4,6), 2:(1,3), 0:(0,0)},
    "CET6":       {14:(13,15), 11:(10,12), 8:(7,9), 5:(4,6), 2:(1,3), 0:(0,0)},
    "Postgrad1A": {5:(9,10), 4:(7,8), 3:(5,6), 2:(3,4), 1:(1,2), 0:(0,0)},
    "Postgrad1B": {5:(17,20), 4:(13,16), 3:(9,12), 2:(5,8), 1:(1,4), 0:(0,0)},
    "Postgrad2A": {5:(9,10), 4:(7,8), 3:(5,6), 2:(3,4), 1:(1,2), 0:(0,0)},
    "Postgrad2B": {5:(13,15), 4:(10,12), 3:(7,9), 2:(4,6), 1:(1,3), 0:(0,0)},
}

# v1.6.1 新增：枚举合法值
LEGAL_LETTER_CATEGORIES = {
    "inquiry", "application", "recommendation", "invitation",
    "suggestion", "complaint", "reply", "apology",
    "congratulation", "thank_you", "other",
}

LEGAL_CHART_SUBTYPES = {
    "bar_chart", "pie_chart", "table", "line_graph",
    "multi_bar", "multi_pie", "mixed",
}

LEGAL_CALIBRATION_STATUS = {
    "normal", "low_frequency_theoretical", "out_of_calibration",
}

# v1.6.1 新增：按 exam_level 细化的 task_subtype 白名单（与 references/exam-level-matrix.md 对齐）
LEGAL_TASK_SUBTYPES = {
    "CET4":       {"argumentative", "letter", "proverb", "news_report",
                   "cartoon", "chart"},
    "CET6":       {"argumentative", "letter", "proverb", "news_report",
                   "cartoon", "chart"},
    "Postgrad1A": {"letter", "notice", "announcement", "summary", "memorandum"},
    "Postgrad1B": {"cartoon_standard", "narrative", "descriptive",
                   "expository", "argumentative"},
    "Postgrad2A": {"letter", "notice", "announcement", "summary", "memorandum"},
    "Postgrad2B": {"bar_chart", "pie_chart", "table", "line_graph",
                   "multi_bar", "multi_pie", "mixed", "chart"},
}


FRONT_MATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE
)

JSON_BLOCK_RE = re.compile(
    r"## 回归测试预期值\s*\n\s*```json\s*\n(.*?)\n```",
    re.DOTALL
)


def parse_front_matter(text: str) -> dict:
    """极简 YAML 解析：仅支持 key: value / key: [list] / key: | 多行字符串。"""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    meta: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or line.startswith("#"):
            i += 1
            continue
        # key: | 多行
        mm = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*\|\s*$", line)
        if mm:
            key = mm.group(1)
            i += 1
            buf: list[str] = []
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                if lines[i].startswith("  "):
                    buf.append(lines[i][2:])
                else:
                    buf.append("")
                i += 1
            meta[key] = "\n".join(buf).rstrip()
            continue
        # key: [a, b, c]
        mm = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*\[(.*)\]\s*$", line)
        if mm:
            key, arr = mm.group(1), mm.group(2)
            items = [x.strip().strip('"').strip("'") for x in arr.split(",") if x.strip()]
            meta[key] = items
            i += 1
            continue
        # key: value
        mm = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.+?)\s*$", line)
        if mm:
            key, val = mm.group(1), mm.group(2).strip('"').strip("'")
            if val.isdigit():
                meta[key] = int(val)
            elif re.match(r"^-?\d+\.\d+$", val):
                meta[key] = float(val)
            else:
                meta[key] = val
        i += 1
    return meta


def parse_expectation(text: str) -> dict | None:
    m = JSON_BLOCK_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def scan_samples(root: Path) -> list[dict]:
    """扫描 references/calibration/samples/**/*.md 并返回条目列表。"""
    out: list[dict] = []
    for md in sorted(root.rglob("*.md")):
        if md.name == "README.md":
            continue
        text = md.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        if not meta or "exam_level" not in meta:
            continue
        exp = parse_expectation(text)
        out.append({
            "path": str(md.relative_to(root.parent.parent)),
            "meta": meta,
            "expectation": exp,
        })
    return out


def check_band_range(sample: dict) -> str | None:
    """校验 band/raw_score 在预期区间内；返回错误信息（若无则 None）。"""
    meta = sample["meta"]
    exam = meta.get("exam_level")
    band = meta.get("band")
    raw = meta.get("raw_score")
    if exam not in BAND_RANGES:
        return f"未知 exam_level={exam}"
    if band not in BAND_RANGES[exam]:
        return f"band={band} 不在 {exam} 合法 band 集合中"
    lo, hi = BAND_RANGES[exam][band]
    if not (lo <= raw <= hi):
        return f"raw_score={raw} 越界 {exam} band={band} 的 [{lo},{hi}]"
    return None


def render_coverage(samples: list[dict]) -> str:
    """exam_level × band 覆盖矩阵。"""
    exams = ["CET4", "CET6", "Postgrad1A", "Postgrad1B", "Postgrad2A", "Postgrad2B"]
    # 每个考试的 band 列（不同考试 band 集合不同）
    out = []
    out.append("## 覆盖矩阵：exam_level × band\n")
    for exam in exams:
        bands_raw = sorted(BAND_RANGES[exam].keys(), reverse=True)
        bands = [b for b in bands_raw if b != 0]  # 不列 0 档
        header = "| exam_level | " + " | ".join(f"band {b}" for b in bands) + " | 合计 |"
        sep = "|" + "|".join("---" for _ in range(len(bands) + 2)) + "|"
        row_cells = []
        total = 0
        for b in bands:
            cnt = sum(1 for s in samples
                      if s["meta"].get("exam_level") == exam and s["meta"].get("band") == b)
            total += cnt
            row_cells.append("✅ " + str(cnt) if cnt else "—")
        out.append(header)
        out.append(sep)
        out.append(f"| **{exam}** | " + " | ".join(row_cells) + f" | **{total}** |")
        out.append("")
    return "\n".join(out)


def render_subtype(samples: list[dict]) -> str:
    """exam_level × task_subtype 文体矩阵。"""
    pairs = sorted({(s["meta"].get("exam_level", "?"), s["meta"].get("task_subtype", "?"))
                    for s in samples})
    exams = sorted({e for e, _ in pairs})
    subtypes = sorted({t for _, t in pairs})
    out = ["## 文体矩阵：exam_level × task_subtype\n"]
    header = "| exam_level \\ subtype | " + " | ".join(subtypes) + " |"
    sep = "|" + "|".join("---" for _ in range(len(subtypes) + 1)) + "|"
    out.append(header)
    out.append(sep)
    for e in exams:
        cells = []
        for t in subtypes:
            cnt = sum(1 for s in samples
                      if s["meta"].get("exam_level") == e and s["meta"].get("task_subtype") == t)
            cells.append(str(cnt) if cnt else "—")
        out.append(f"| **{e}** | " + " | ".join(cells) + " |")
    return "\n".join(out)


def check_v16_fields(sample: dict) -> list[str]:
    """v1.6.1：校验 letter_category / chart_subtype / calibration_status 合法性。"""
    meta = sample["meta"]
    errors: list[str] = []
    exam = meta.get("exam_level")
    subtype = meta.get("task_subtype")
    letter_cat = meta.get("letter_category")
    chart_sub = meta.get("chart_subtype")
    calib = meta.get("calibration_status")

    # task_subtype 合法性
    if exam in LEGAL_TASK_SUBTYPES and subtype:
        if subtype not in LEGAL_TASK_SUBTYPES[exam]:
            errors.append(
                f"task_subtype='{subtype}' 不在 {exam} 合法集："
                f"{sorted(LEGAL_TASK_SUBTYPES[exam])}"
            )

    # letter_category 仅在 task_subtype=letter 时才应出现
    if letter_cat:
        if subtype != "letter":
            errors.append(f"letter_category='{letter_cat}' 只应在 task_subtype=letter 时出现（当前 {subtype}）")
        elif letter_cat not in LEGAL_LETTER_CATEGORIES:
            errors.append(
                f"letter_category='{letter_cat}' 非法，合法集："
                f"{sorted(LEGAL_LETTER_CATEGORIES)}"
            )

    # chart_subtype 仅在 task_subtype=chart 或 task_subtype 本身就是 chart 细分时出现
    if chart_sub and chart_sub not in LEGAL_CHART_SUBTYPES:
        errors.append(
            f"chart_subtype='{chart_sub}' 非法，合法集：{sorted(LEGAL_CHART_SUBTYPES)}"
        )

    # calibration_status 合法性
    if calib and calib not in LEGAL_CALIBRATION_STATUS:
        errors.append(
            f"calibration_status='{calib}' 非法，合法集：{sorted(LEGAL_CALIBRATION_STATUS)}"
        )
    return errors


def render_v16_breakdown(samples: list[dict]) -> str:
    """v1.6.1：letter_category × chart_subtype × calibration_status 细粒度统计。"""
    out = ["## v1.6 细粒度子类统计\n"]

    # letter_category 分布
    letter_samples = [s for s in samples if s["meta"].get("letter_category")]
    if letter_samples:
        out.append("### letter_category（考研 A 节信件功能分类）")
        buckets: dict[str, list] = {}
        for s in letter_samples:
            cat = s["meta"].get("letter_category")
            buckets.setdefault(cat, []).append(s)
        out.append("| letter_category | 样例数 | 样例路径 |")
        out.append("|---|---|---|")
        for cat in sorted(LEGAL_LETTER_CATEGORIES):
            rows = buckets.get(cat, [])
            paths = "<br>".join(Path(s["path"]).name for s in rows) or "—"
            out.append(f"| {cat} | {len(rows)} | {paths} |")
        out.append("")

    # chart_subtype 分布（针对 Postgrad2B 或 task_subtype=chart 的 CET）
    chart_samples = [
        s for s in samples
        if s["meta"].get("chart_subtype")
        or (s["meta"].get("task_subtype") in LEGAL_CHART_SUBTYPES)
    ]
    if chart_samples:
        out.append("### chart_subtype（图表子类分布）")
        buckets = {}
        for s in chart_samples:
            sub = s["meta"].get("chart_subtype") or s["meta"].get("task_subtype")
            buckets.setdefault(sub, []).append(s)
        out.append("| chart_subtype | 样例数 | 样例路径 |")
        out.append("|---|---|---|")
        for sub in sorted(LEGAL_CHART_SUBTYPES):
            rows = buckets.get(sub, [])
            paths = "<br>".join(Path(s["path"]).name for s in rows) or "—"
            out.append(f"| {sub} | {len(rows)} | {paths} |")
        out.append("")

    # calibration_status 分布
    out.append("### calibration_status（校准成熟度分布）")
    status_buckets: dict[str, list] = {}
    for s in samples:
        st = s["meta"].get("calibration_status", "normal")
        status_buckets.setdefault(st, []).append(s)
    out.append("| calibration_status | 样例数 |")
    out.append("|---|---|")
    for st in sorted(LEGAL_CALIBRATION_STATUS):
        rows = status_buckets.get(st, [])
        out.append(f"| {st} | {len(rows)} |")

    # 低频/理论清单
    lft = status_buckets.get("low_frequency_theoretical", [])
    if lft:
        out.append("")
        out.append("### 低频/理论题型清单（置信度降低，评分仅供参考）")
        for s in lft:
            out.append(f"- `{s['path']}` · {s['meta'].get('exam_level')} · "
                       f"{s['meta'].get('task_subtype')}")
    return "\n".join(out)


def render_gold_standards(samples: list[dict]) -> str:
    out = ["## 金标样例（anchor_tags 含 gold-standard-* 或 reference_source 标注）\n"]
    gs = []
    for s in samples:
        tags = s["meta"].get("anchor_tags", []) or []
        ref = str(s["meta"].get("reference_source", ""))
        if any("gold" in t for t in tags) or "gold" in ref or "金标" in ref:
            gs.append(s)
    if not gs:
        out.append("_（当前无样例标记为金标）_")
        return "\n".join(out)
    for s in gs:
        tags = " · ".join(s["meta"].get("anchor_tags", []) or [])
        out.append(f"- **{s['path']}** — {tags or '（无 tag）'}")
    return "\n".join(out)


def render_regression_json(samples: list[dict]) -> dict:
    """汇总所有含 expectation 的样例为机读 JSON。"""
    out = {
        "total_samples": len(samples),
        "samples_with_expectation": sum(1 for s in samples if s["expectation"]),
        "expectations": [],
    }
    for s in samples:
        if not s["expectation"]:
            continue
        out["expectations"].append({
            "path": s["path"],
            "exam_level": s["meta"].get("exam_level"),
            "task_subtype": s["meta"].get("task_subtype"),
            "expected": s["expectation"],
        })
    return out


def main() -> None:
    here = Path(__file__).resolve().parent
    default_root = here.parent / "references" / "calibration" / "samples"

    ap = argparse.ArgumentParser(description="calibration 集回归/覆盖矩阵工具")
    ap.add_argument("--root", default=str(default_root),
                    help="samples 根目录（默认 ../references/calibration/samples）")
    ap.add_argument("--format", choices=["md", "json", "both"], default="md",
                    help="输出格式")
    ap.add_argument("--coverage-only", action="store_true", help="仅输出覆盖矩阵")
    ap.add_argument("--check-band-range", action="store_true",
                    help="校验 raw_score 是否在 band 区间内")
    ap.add_argument("--check-v16", action="store_true",
                    help="v1.6 新字段合法性校验（task_subtype / letter_category / chart_subtype / calibration_status 枚举）")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"❌ 目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    samples = scan_samples(root)
    if not samples:
        print("❌ 未发现任何样例", file=sys.stderr)
        sys.exit(2)

    # 校验
    errors: list[str] = []
    if args.check_band_range:
        for s in samples:
            err = check_band_range(s)
            if err:
                errors.append(f"[{s['path']}] {err}")
    if args.check_v16:
        for s in samples:
            for err in check_v16_fields(s):
                errors.append(f"[{s['path']}] {err}")

    # 输出
    if args.format in ("md", "both"):
        print(f"# Calibration 报告（共 {len(samples)} 篇样例）\n")
        print(render_coverage(samples))
        if not args.coverage_only:
            print()
            print(render_subtype(samples))
            print()
            print(render_v16_breakdown(samples))
            print()
            print(render_gold_standards(samples))

    if args.format in ("json", "both"):
        payload = render_regression_json(samples)
        if args.check_band_range:
            payload["validation_errors"] = errors
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if errors:
        print(f"\n❌ 校验失败：共 {len(errors)} 个错误", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(3)

    if args.format in ("md", "both"):
        print(f"\n✅ 校验通过（{len(samples)} 篇）")


if __name__ == "__main__":
    main()
