#!/usr/bin/env python3
"""Locate uploaded/listing task files for listing-asin-batch-ingest.

Use this before broad filesystem searches when the visible filename does not
match the stored UUID filename.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time


DEFAULT_EXTS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".zip", ".json", ".md", ".html", ".htm"}


def roots() -> list[Path]:
    seen: set[str] = set()
    candidates: list[Path] = []
    acpx = (os.environ.get("ACPX_WORKSPACES") or "").strip()
    if acpx:
        for part in acpx.split(os.pathsep):
            if part.strip():
                candidates.append(Path(part.strip()).expanduser())
    candidates.extend([
        Path.cwd(),
        Path.home() / "linkfox",
        Path(tempfile.gettempdir()),
    ])
    result: list[Path] = []
    for root in candidates:
        try:
            resolved = str(root.resolve())
        except OSError:
            continue
        if resolved in seen or not root.exists():
            continue
        seen.add(resolved)
        result.append(root)
    return result


def score(path: Path, query: str, exts: set[str]) -> int:
    name = path.name.lower()
    q = query.lower()
    stem = Path(query).stem.lower()
    value = 0
    if path.suffix.lower() in exts:
        value += 20
    if name == q:
        value += 100
    elif stem and stem in path.stem.lower():
        value += 60
    elif q and q in name:
        value += 50
    # Prefer ACP session workspaces and recent files.
    text = str(path).lower()
    if ".linkfox" in text or "/linkfox/" in text:
        value += 15
    age = max(0, time.time() - path.stat().st_mtime)
    if age < 3600:
        value += 12
    elif age < 24 * 3600:
        value += 6
    return value


def iter_files(root: Path, max_depth: int, max_files: int):
    count = 0
    base_depth = len(root.parts)
    skip_names = {"node_modules", ".git", ".next", "__pycache__", ".venv", "venv"}
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in skip_names and not d.startswith(".Trash")]
        for filename in files:
            count += 1
            if count > max_files:
                return
            yield current_path / filename


def locate(query: str, exts: set[str], max_depth: int, max_files: int, limit: int):
    hits = []
    query_ext = Path(query).suffix.lower()
    if query_ext:
        exts = {query_ext}
    for root in roots():
        for path in iter_files(root, max_depth, max_files):
            try:
                if not path.is_file():
                    continue
                if path.suffix.lower() not in exts and path.name.lower() != query.lower():
                    continue
                value = score(path, query, exts)
                if value <= 0:
                    continue
                hits.append({
                    "path": str(path.resolve()),
                    "name": path.name,
                    "size": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                    "score": value,
                })
            except OSError:
                continue
    hits.sort(key=lambda item: (item["score"], item["mtime"]), reverse=True)
    return hits[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Visible filename, UUID filename, or suffix hint")
    parser.add_argument("--ext", action="append", default=[], help="Allowed extension, repeatable")
    parser.add_argument("--max-depth", type=int, default=7)
    parser.add_argument("--max-files", type=int, default=20000)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--first", action="store_true", help="Print only the best path")
    args = parser.parse_args()

    exts = set()
    for ext in args.ext:
        exts.add(ext if ext.startswith(".") else f".{ext}")
    if not exts:
        exts = set(DEFAULT_EXTS)
    hits = locate(args.query, exts, args.max_depth, args.max_files, args.limit)
    if args.first:
        if not hits:
            return 2
        print(hits[0]["path"])
    else:
        print(json.dumps({"query": args.query, "matches": hits}, ensure_ascii=False, indent=2))
    return 0 if hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
