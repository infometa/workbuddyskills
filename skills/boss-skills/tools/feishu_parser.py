#!/usr/bin/env python3
"""
Extract target lines from Feishu exports in json/txt form.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract target lines from Feishu exports.")
    parser.add_argument("--file", required=True, help="Input json/txt file.")
    parser.add_argument("--target", required=True, help="Target speaker name.")
    parser.add_argument("--output", required=True, help="Output txt file.")
    return parser.parse_args()


def walk_json(node, target: str, hits: list[str]) -> None:
    if isinstance(node, dict):
        speaker = str(
            node.get("sender_name")
            or node.get("sender")
            or node.get("user_name")
            or node.get("from")
            or ""
        )
        content = str(node.get("text") or node.get("content") or node.get("body") or "")
        if target in speaker.casefold() and content.strip():
            hits.append(f"{speaker}: {content.strip()}")
        for value in node.values():
            walk_json(value, target, hits)
    elif isinstance(node, list):
        for item in node:
            walk_json(item, target, hits)


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    target = args.target.casefold()
    hits: list[str] = []

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        walk_json(data, target, hits)
    else:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        hits = [line.strip() for line in lines if target in line.casefold() and line.strip()]

    out = [f"# Feishu extract for {args.target}", ""]
    out.extend(hits or ["No matching lines found."])
    Path(args.output).write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
