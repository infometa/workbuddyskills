#!/usr/bin/env python3
"""
从 matrix 落盘 JSON 打印 Top N 关键词（禁止 python3 -c 解析大文件）。

Usage:
  python3 scripts/peek_matrix_keywords.py /abs/path/linkfox-listing-keyword-matrix-build-*.json --top 20
  python3 scripts/peek_matrix_keywords.py /abs/path/matrix.json --top 10 --format table
"""

from __future__ import annotations

import argparse
import json
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="预览 keyword matrix scored_table")
    parser.add_argument("file", help="matrix 落盘 JSON 绝对路径")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("scored_table") or data.get("keywords") or []
    if not isinstance(rows, list):
        print("scored_table 不是数组", file=sys.stderr)
        sys.exit(1)

    picked = []
    for i, row in enumerate(rows[: args.top], start=1):
        if not isinstance(row, dict):
            continue
        picked.append(
            {
                "rank": i,
                "keyword": row.get("keyword") or row.get("word") or "",
                "value_score": row.get("value_score"),
                "searches_rank": row.get("searches_rank"),
                "natural_rank": row.get("natural_rank"),
            }
        )

    if args.format == "json":
        print(json.dumps(picked, ensure_ascii=False, indent=2))
        return

    print(f"Top {len(picked)} keywords from {args.file}")
    print("-" * 72)
    for item in picked:
        score = item.get("value_score", "?")
        kw = item.get("keyword", "")
        nr = item.get("natural_rank", "N/A")
        print(f"{item['rank']:2}. [{score}] {kw} | nr={nr}")


if __name__ == "__main__":
    main()
