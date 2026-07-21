#!/usr/bin/env python3
"""
Parse plain text or markdown chat transcripts and extract the target speaker's lines.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LINE_PATTERNS = [
    re.compile(r"^\[(?P<time>[^\]]+)\]\s*(?P<speaker>[^:：]+)\s*[:：]\s*(?P<content>.+)$"),
    re.compile(r"^(?P<time>\d{4}[-/]\d{1,2}[-/]\d{1,2}[^ ]*\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<speaker>[^:：]+)\s*[:：]\s*(?P<content>.+)$"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract target speaker lines from a chat transcript.")
    parser.add_argument("--file", required=True, help="Input txt/md file.")
    parser.add_argument("--target", required=True, help="Target speaker name.")
    parser.add_argument("--output", required=True, help="Output txt file.")
    parser.add_argument("--context", type=int, default=1, help="Context lines before and after each hit.")
    return parser.parse_args()


def normalize_line(line: str) -> str:
    return " ".join(line.strip().split())


def match_message(line: str) -> dict | None:
    for pattern in LINE_PATTERNS:
        match = pattern.match(line.strip())
        if match:
            return match.groupdict()
    return None


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    lines = path.read_text(encoding="utf-8").splitlines()
    target = args.target.casefold()
    blocks: list[str] = []

    for index, line in enumerate(lines):
        parsed = match_message(line)
        speaker_hit = parsed and target in parsed["speaker"].casefold()
        plain_hit = target in line.casefold()
        if not (speaker_hit or plain_hit):
            continue

        start = max(0, index - args.context)
        end = min(len(lines), index + args.context + 1)
        snippet = [normalize_line(lines[i]) for i in range(start, end) if normalize_line(lines[i])]
        blocks.append("\n".join(snippet))

    output_lines = [f"# Extracted transcript for {args.target}", ""]
    if not blocks:
        output_lines.append("No matching lines found.")
    else:
        for idx, block in enumerate(blocks, start=1):
            output_lines.append(f"## Hit {idx}")
            output_lines.append(block)
            output_lines.append("")

    Path(args.output).write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
