#!/usr/bin/env python3
"""
listing-quality-scorer 落盘器 — 裸 payload + skill-output-protocol。

Usage:
  python3 scripts/save_quality_score_output.py '<json>'
  cat quality-score.json | python3 scripts/save_quality_score_output.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

SLUG = "linkfox-listing-quality-scorer"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _read_input(argv: list[str]) -> str:
    if not argv or argv[0] == "-":
        if sys.stdin.isatty():
            print("用法: save_quality_score_output.py '<json>' | save_quality_score_output.py file.json", file=sys.stderr)
            sys.exit(1)
        return sys.stdin.read()
    arg = argv[0]
    if os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return f.read()
    return arg


def _score_panel(payload: dict[str, Any]) -> dict[str, Any]:
    panel = payload.get("scorePanel") if isinstance(payload.get("scorePanel"), dict) else payload
    if not isinstance(panel, dict):
        raise ValueError("缺少 scorePanel 对象")
    if "overall" not in panel:
        raise ValueError("scorePanel 缺少 overall")
    items = panel.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("scorePanel.items 必须是非空数组")
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"scorePanel.items[{idx}] 必须是对象")
        if not item.get("name"):
            raise ValueError(f"scorePanel.items[{idx}] 缺少 name")
        if "score" not in item:
            raise ValueError(f"scorePanel.items[{idx}] 缺少 score（不可评分时填 null）")
        if not item.get("state"):
            raise ValueError(f"scorePanel.items[{idx}] 缺少 state")
    return panel


def main() -> None:
    argv = sys.argv[1:]
    inline = "--inline" in argv
    if inline:
        argv = [a for a in argv if a != "--inline"]

    try:
        payload = json.loads(_read_input(argv))
    except json.JSONDecodeError as exc:
        print(f"输入不是合法 JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(payload, dict):
        print("顶层必须是 JSON 对象", file=sys.stderr)
        sys.exit(1)

    try:
        panel = _score_panel(payload)
    except ValueError as exc:
        print(f"schema 校验未通过: {exc}", file=sys.stderr)
        sys.exit(2)

    if "scorePanel" not in payload:
        payload = {"scorePanel": panel}

    from linkfox_save import save_json_payload  # type: ignore

    overall = panel.get("overall")
    grade = panel.get("grade") or "—"
    issue_count = len(panel.get("topIssues") or payload.get("topIssues") or [])
    summary = [
        "已落盘 Listing 质量评分。",
        f"  overall: {'—' if overall is None else overall} · grade: {grade}",
        f"  dimensions: {len(panel.get('items') or [])}",
        f"  topIssues: {issue_count}",
    ]

    # 载荷自描述：UI 的 skill-data-router 按 `kind` 精确路由，没有 kind 的裸 JSON
    # 只能落到 FormattedJsonView 兜底。已有 kind 时不覆盖调用方的值。
    payload.setdefault("kind", "listingQualityScore")
    payload.setdefault("schema_version", 1)

    abs_path, _size_bytes = save_json_payload(SLUG, payload, summary_lines=summary)
    if inline:
        print("\n----- FULL JSON (--inline) -----")
        with open(abs_path, encoding="utf-8") as f:
            print(f.read())


if __name__ == "__main__":
    main()
