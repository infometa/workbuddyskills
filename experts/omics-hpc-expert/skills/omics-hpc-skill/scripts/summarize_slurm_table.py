#!/usr/bin/env python3
"""Summarize SLURM parsable2 (pipe-delimited) table output.

Designed to consume the output of commands like:
    squeue --parsable2 -u <user> | python summarize_slurm_table.py
    sacct  --parsable2 -u <user> | python summarize_slurm_table.py
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys


def read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def parse_parsable2(text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse pipe-delimited output (--parsable2) into header + list of dicts."""
    raw_lines = [line for line in text.splitlines() if line.strip()]
    if not raw_lines:
        return [], []

    header = raw_lines[0].split("|")
    rows: list[dict[str, str]] = []
    for line in raw_lines[1:]:
        values = line.split("|")
        row = {h: (values[i] if i < len(values) else "") for i, h in enumerate(header)}
        rows.append(row)
    return header, rows


def find_field(header: list[str], *candidates: str) -> str | None:
    """Find the first matching field name in the header."""
    for c in candidates:
        for h in header:
            if h.upper() == c.upper():
                return h
    return None


def counter_str(counter: Counter[str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(counter.items()))


def summarize(header: list[str], rows: list[dict[str, str]]) -> str:
    if not header:
        return "No table data detected."
    if not rows:
        return f"Detected header with 0 rows. Columns: {', '.join(header)}."

    parts: list[str] = [f"Total: {len(rows)} row(s)."]

    # State summary
    state_field = find_field(header, "ST", "STATE", "State")
    if state_field:
        state_counter: Counter[str] = Counter(r.get(state_field, "?") for r in rows)
        parts.append(f"By state: {counter_str(state_counter)}.")

    # Partition summary
    part_field = find_field(header, "PARTITION", "Partition")
    if part_field:
        part_counter: Counter[str] = Counter(r.get(part_field, "?") for r in rows)
        if len(part_counter) > 1 or (len(part_counter) == 1 and "?" not in part_counter):
            parts.append(f"By partition: {counter_str(part_counter)}.")

    # User summary (useful for admin-wide queries)
    user_field = find_field(header, "USER", "User")
    if user_field:
        user_counter: Counter[str] = Counter(r.get(user_field, "?") for r in rows)
        if len(user_counter) > 1:
            parts.append(f"By user: {counter_str(user_counter)}.")

    parts.append(f"Columns: {', '.join(header)}.")
    return " ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize SLURM --parsable2 output (pipe-delimited). "
            "Feed squeue or sacct output via stdin or --input."
        ),
    )
    parser.add_argument(
        "--input", default=None,
        help="File containing parsable2 output. If omitted, read from stdin.",
    )
    args = parser.parse_args()

    text = read_text(args.input)
    header, rows = parse_parsable2(text)
    print(summarize(header, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
