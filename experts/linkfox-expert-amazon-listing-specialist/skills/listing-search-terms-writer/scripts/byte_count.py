#!/usr/bin/env python3
"""打印字符串 UTF-8 字节数。禁止 agent 用 python3 -c 做字节校验。

Usage:
  python3 scripts/byte_count.py "search terms here"
  echo -n "text" | python3 scripts/byte_count.py
"""

from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
print(len(text.encode("utf-8")))
