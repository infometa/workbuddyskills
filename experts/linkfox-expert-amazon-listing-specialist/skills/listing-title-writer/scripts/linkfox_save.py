#!/usr/bin/env python3
"""通用 JSON 落盘：linkfox_paths + skill-output-protocol stdout。"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any


def save_json_payload(slug: str, payload: Any, *, summary_lines: list[str] | None = None) -> tuple[str, int]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
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
