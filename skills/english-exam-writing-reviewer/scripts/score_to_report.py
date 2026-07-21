#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CET 作文分数 → 710 总分下的报告分换算。

换算公式（官方）：
    报告分 = 原始分 × (106.5 / 15) = 原始分 × 7.1
    总分 710 分中，作文占 15% = 106.5 分

Usage:
    python score_to_report.py 11          # 直接给分数
    python score_to_report.py review.json # 读取 JSON 中的 final_score
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_RAW = 15
MAX_REPORT = 106.5
RATIO = MAX_REPORT / MAX_RAW  # 7.1


def convert(raw_score: float) -> float:
    if not (0 <= raw_score <= MAX_RAW):
        raise ValueError(f"原始分数必须在 0-{MAX_RAW} 之间：{raw_score}")
    return round(raw_score * RATIO, 1)


def convert_json(input_path: Path, output_path: Path | None = None) -> dict:
    data = json.loads(input_path.read_text(encoding="utf-8"))

    final_score = data.get("final_score")
    if final_score is None:
        final_score = data.get("raw_score", data.get("overall_score", 0))

    converted = convert(float(final_score))
    data["converted_score"] = converted
    data.setdefault("meta", {})
    data["meta"]["conversion"] = {
        "raw_max": MAX_RAW,
        "report_max": MAX_REPORT,
        "ratio": round(RATIO, 2),
    }

    out = output_path or input_path.with_name(input_path.stem + "_converted.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✅ 分数换算完成")
    print(f"   最终分: {final_score}/15")
    print(f"   报告分: {converted}/106.5")
    print(f"   输出:   {out}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="CET 15 分制 → 106.5 报告分换算")
    parser.add_argument("input", help="分数（0-15）或 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出 JSON 文件（仅 JSON 模式）")
    args = parser.parse_args()

    try:
        raw = float(args.input)
        print(f"✅ {raw}/15 → {convert(raw)}/106.5")
        return
    except ValueError:
        pass

    path = Path(args.input)
    if not path.exists():
        print(f"❌ 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    convert_json(path, Path(args.output) if args.output else None)


if __name__ == "__main__":
    main()
