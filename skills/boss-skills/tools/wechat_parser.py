#!/usr/bin/env python3
"""
Extract target lines from WeChat exports in txt/html/csv form.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract target lines from WeChat exports.")
    parser.add_argument("--file", required=True, help="Input txt/html/csv file.")
    parser.add_argument("--target", required=True, help="Target speaker name.")
    parser.add_argument("--output", required=True, help="Output txt file.")
    return parser.parse_args()


def html_to_text(content: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    raw = path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() == ".html":
        raw = html_to_text(raw)

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    target = args.target.casefold()
    hits = [line for line in lines if target in line.casefold()]

    out = [f"# WeChat extract for {args.target}", ""]
    out.extend(hits or ["No matching lines found."])
    Path(args.output).write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
