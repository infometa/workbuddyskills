#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrate.py —— calibration 集扫描 + 覆盖矩阵生成器（v0.1.0）

功能
----
1. 扫描 references/calibration/samples/ 下所有 calib-*.md 样例
2. 解析每个样例的 YAML front-matter（paper_id / mode / depth_used / anchor_tags / calibration_status 等）
3. 抽取样例内 "## 回归测试预期值" 下的第一个 JSON block，作为该样例的**预期输出**
4. 输出 5 类报告：
   - 【表格】覆盖矩阵：mode × depth_used（看哪些格子缺样例）
   - 【表格】anchor_tags 覆盖
   - 【文本】gold-standard / edge_case / normal 分类清单
   - 【JSON】机读的 regression_expectations（供 CI 或 Skill 自检用）
   - 【可选】--validate: 针对指定 result.json + provenance-audit.json 校验是否满足 expected_*

使用
----
    python3 calibrate.py                    # 扫描 + 生成覆盖矩阵
    python3 calibrate.py --format json      # 仅机读 JSON
    python3 calibrate.py --coverage-only    # 仅覆盖矩阵
    python3 calibrate.py --validate \
        --sample calib-01-self-instruct-skim.md \
        --result path/to/result.json \
        --audit  path/to/provenance-audit.json

依赖：仅标准库（re / json / 手写 YAML front-matter 解析）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_SAMPLES_DIR = SKILL_ROOT / "references" / "calibration" / "samples"


# =====================================================================
# 1. Front-matter / 预期值解析
# =====================================================================

FRONT_MATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)
EXPECTED_HEADER_RE = re.compile(r"##\s*回归测试预期值")
CODE_FENCE_RE = re.compile(r"```json\s*\n(.+?)\n```", re.DOTALL)


def _parse_yaml_frontmatter(text: str) -> dict[str, Any]:
    """极简 YAML front-matter 解析（支持 key: value / key: [a, b] / key: |）。"""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, Any] = {}
    body = m.group(1)
    for line in body.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        val = raw_val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",") if x.strip()]
            out[key] = items
        elif val.startswith('"') and val.endswith('"'):
            out[key] = val[1:-1]
        elif val.lower() in ("true", "false"):
            out[key] = val.lower() == "true"
        elif val.isdigit():
            out[key] = int(val)
        else:
            out[key] = val
    return out


def _extract_expected_json(text: str) -> dict[str, Any] | None:
    """提取 "## 回归测试预期值" 之后的第一个 ```json 代码块。"""
    m = EXPECTED_HEADER_RE.search(text)
    if not m:
        return None
    rest = text[m.end():]
    fm = CODE_FENCE_RE.search(rest)
    if not fm:
        return None
    try:
        return json.loads(fm.group(1))
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON 解析失败：{e}", file=sys.stderr)
        return None


def load_samples(samples_dir: Path) -> list[dict[str, Any]]:
    """扫描 calib-*.md 样例。"""
    out = []
    if not samples_dir.is_dir():
        return out
    for path in sorted(samples_dir.glob("calib-*.md")):
        text = path.read_text(encoding="utf-8")
        meta = _parse_yaml_frontmatter(text)
        expected = _extract_expected_json(text)
        out.append(
            {
                "path": str(path.relative_to(SKILL_ROOT)),
                "file": path.name,
                "meta": meta,
                "expected": expected,
            }
        )
    return out


# =====================================================================
# 2. 覆盖矩阵 / 报告生成
# =====================================================================

def render_coverage_matrix(samples: list[dict[str, Any]]) -> str:
    modes = sorted({s["meta"].get("mode") or "?" for s in samples})
    depths = sorted({tuple(s["meta"].get("depth_used", []) or []) for s in samples}, key=lambda t: "-".join(t))

    lines = ["## mode × depth 覆盖矩阵\n"]
    header = "| mode \\ depth | " + " | ".join("-".join(d) or "—" for d in depths) + " |"
    sep = "|---|" + "---|" * len(depths)
    lines.extend([header, sep])
    for m in modes:
        row = [m]
        for d in depths:
            count = sum(
                1 for s in samples
                if (s["meta"].get("mode") == m) and tuple(s["meta"].get("depth_used", []) or []) == d
            )
            row.append(str(count) if count else " ")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def render_anchor_tag_coverage(samples: list[dict[str, Any]]) -> str:
    tag_count: dict[str, int] = {}
    for s in samples:
        for t in s["meta"].get("anchor_tags", []) or []:
            tag_count[t] = tag_count.get(t, 0) + 1
    lines = ["## anchor_tags 覆盖\n", "| tag | 样例数 |", "|---|---|"]
    for t in sorted(tag_count):
        lines.append(f"| `{t}` | {tag_count[t]} |")
    return "\n".join(lines) + "\n"


def render_status_lists(samples: list[dict[str, Any]]) -> str:
    by_status: dict[str, list[str]] = {}
    for s in samples:
        by_status.setdefault(s["meta"].get("calibration_status", "unknown"), []).append(s["file"])
    lines = ["## 按 calibration_status 分类\n"]
    for st in sorted(by_status):
        lines.append(f"### {st}")
        for f in by_status[st]:
            lines.append(f"- `{f}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_regression_expectations(samples: list[dict[str, Any]]) -> dict[str, Any]:
    out = {
        "skill_version": "0.1.0",
        "total_samples": len(samples),
        "samples": [],
    }
    for s in samples:
        if not s.get("expected"):
            continue
        out["samples"].append(
            {
                "file": s["file"],
                "paper_id": s["meta"].get("paper_id"),
                "mode": s["meta"].get("mode"),
                "depth_used": s["meta"].get("depth_used"),
                "calibration_status": s["meta"].get("calibration_status"),
                "anchor_tags": s["meta"].get("anchor_tags", []),
                "expected": s["expected"],
            }
        )
    return out


# =====================================================================
# 3. --validate：实际 result.json + audit 对照 expected_*
# =====================================================================

def validate_against_sample(sample_file: Path, result_file: Path, audit_file: Path) -> dict[str, Any]:
    """对指定 result + audit 校验是否满足 sample 的 expected_*；返回 pass/fail 报告。"""
    sample_text = sample_file.read_text(encoding="utf-8")
    expected = _extract_expected_json(sample_text)
    if not expected:
        return {"status": "error", "message": "sample 未包含 ## 回归测试预期值"}

    result = json.loads(result_file.read_text(encoding="utf-8"))
    audit = json.loads(audit_file.read_text(encoding="utf-8"))

    report = {"status": "pass", "checks": [], "sample": sample_file.name}

    # 1) breakdown 检查
    exp_bd = expected.get("expected_breakdown", {})
    actual_bd = audit.get("breakdown", {})
    for k, v in exp_bd.items():
        if k.endswith("_min"):
            real_key = k[:-4]
            actual = actual_bd.get(real_key, 0)
            ok = actual >= v
            report["checks"].append({
                "check": f"breakdown.{real_key} >= {v}",
                "actual": actual,
                "pass": ok,
            })
            if not ok:
                report["status"] = "fail"

    # 2) match_distribution 检查
    exp_md = expected.get("expected_match_distribution", {})
    actual_md = audit.get("match_distribution", {})
    for k, v in exp_md.items():
        if k.endswith("_min"):
            real_key = k[:-4]
            # 特殊：medium_or_above
            if real_key == "medium_or_above":
                actual = actual_md.get("high", 0) + actual_md.get("medium", 0)
            else:
                actual = actual_md.get(real_key, 0)
            ok = actual >= v
            report["checks"].append({
                "check": f"match_distribution.{real_key} >= {v}",
                "actual": actual,
                "pass": ok,
            })
            if not ok:
                report["status"] = "fail"
        elif k.endswith("_max"):
            real_key = k[:-4]
            actual = actual_md.get(real_key, 0)
            ok = actual <= v
            report["checks"].append({
                "check": f"match_distribution.{real_key} <= {v}",
                "actual": actual,
                "pass": ok,
            })
            if not ok:
                report["status"] = "fail"

    # 3) removed 上限
    if "expected_removed_max" in expected:
        removed = len(audit.get("removed_claims", []))
        ok = removed <= expected["expected_removed_max"]
        report["checks"].append({
            "check": f"removed <= {expected['expected_removed_max']}",
            "actual": removed,
            "pass": ok,
        })
        if not ok:
            report["status"] = "fail"

    # 4) required_anchor_matches：每个 anchor 必须在 audit.claims 里存在且达到 min_confidence
    conf_order = ["failed", "low", "medium", "high"]
    for anchor in expected.get("required_anchor_matches", []):
        needle = anchor.get("text", "")
        min_conf = anchor.get("min_confidence", "medium")
        hit = None
        for c in audit.get("claims", []):
            if needle and needle in (c.get("claim_text") or ""):
                hit = c
                break
        if hit is None:
            report["checks"].append({
                "check": f"required_anchor_matches: {needle[:40]!r}",
                "actual": "NOT FOUND in audit",
                "pass": False,
            })
            report["status"] = "fail"
        else:
            actual_conf = hit.get("ngram_match_confidence", "failed")
            ok = conf_order.index(actual_conf) >= conf_order.index(min_conf)
            report["checks"].append({
                "check": f"anchor '{needle[:30]}' >= {min_conf}",
                "actual": actual_conf,
                "pass": ok,
            })
            if not ok:
                report["status"] = "fail"

    return report


# =====================================================================
# 4. main
# =====================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="calibration 集扫描 / 校验器 v0.1.0")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR),
                        help=f"样例目录（默认 {DEFAULT_SAMPLES_DIR.relative_to(SKILL_ROOT)}）")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="输出格式：markdown 覆盖报告 / json 机读期望值")
    parser.add_argument("--coverage-only", action="store_true", help="仅输出覆盖矩阵")

    parser.add_argument("--validate", action="store_true",
                        help="针对指定 sample + result.json + audit 校验 pass/fail")
    parser.add_argument("--sample", help="样例文件名（配合 --validate 使用）")
    parser.add_argument("--result", help="Skill 输出的 result.json（配合 --validate）")
    parser.add_argument("--audit", help="verify_provenance.py 输出的 audit.json（配合 --validate）")

    args = parser.parse_args()

    samples_dir = Path(args.samples_dir).resolve()

    # --validate 分支
    if args.validate:
        if not (args.sample and args.result and args.audit):
            parser.error("--validate 需同时提供 --sample --result --audit")
        sample_path = samples_dir / args.sample
        if not sample_path.exists():
            # 支持传入完整路径
            sample_path = Path(args.sample)
        report = validate_against_sample(sample_path, Path(args.result), Path(args.audit))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "pass" else 1

    # 扫描样例
    samples = load_samples(samples_dir)
    if not samples:
        print(f"[WARN] 未找到样例：{samples_dir}", file=sys.stderr)
        return 1

    if args.format == "json":
        out = build_regression_expectations(samples)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # markdown 模式
    print(f"# Paper-Quick-Reader 校准集报告\n\n扫描目录：`{samples_dir.relative_to(SKILL_ROOT)}`\n")
    print(f"**样例总数：{len(samples)}**\n")
    print(render_coverage_matrix(samples))

    if not args.coverage_only:
        print(render_anchor_tag_coverage(samples))
        print(render_status_lists(samples))
        print("## 样例清单\n")
        print("| 文件 | paper_id | mode | depth | status | anchor_tags |")
        print("|---|---|---|---|---|---|")
        for s in samples:
            m = s["meta"]
            tags = ",".join(m.get("anchor_tags", []) or [])
            depth = "+".join(m.get("depth_used", []) or [])
            print(f"| `{s['file']}` | {m.get('paper_id','?')} | {m.get('mode','?')} | {depth} | {m.get('calibration_status','?')} | {tags} |")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
