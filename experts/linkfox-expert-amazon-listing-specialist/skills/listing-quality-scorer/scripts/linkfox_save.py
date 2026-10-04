#!/usr/bin/env python3
"""Listing quality scorer JSON 落盘。"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def save_json_payload(slug: str, payload: Any, *, summary_lines: list[str] | None = None) -> tuple[str, int]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    try:
        from linkfox_paths import resolve_data_path  # type: ignore
    except ModuleNotFoundError:
        core_scripts = Path(script_dir).parents[1] / "listing-core" / "scripts"
        if not (core_scripts / "linkfox_paths.py").is_file():
            raise RuntimeError(f"listing-core path helper not found: {core_scripts}")
        sys.path.insert(0, str(core_scripts))
        from linkfox_paths import resolve_data_path  # type: ignore

    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    out_path = resolve_data_path(slug, time.time())
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(serialized)
    size_bytes = len(serialized.encode("utf-8"))
    abs_path = os.path.abspath(out_path)
    print(f"Saved full response: {abs_path} ({size_bytes} bytes)")
    for line in summary_lines or []:
        print(line)
    return abs_path, size_bytes
