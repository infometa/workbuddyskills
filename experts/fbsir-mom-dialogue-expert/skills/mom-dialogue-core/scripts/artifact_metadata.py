#!/usr/bin/env python3
"""Parse the deliberately simple JSON-compatible Markdown frontmatter format."""
from __future__ import annotations

import json
from pathlib import Path


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="strict")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc
    metadata: dict[str, object] = {}
    for index, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"frontmatter line {index} has no colon")
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or key in metadata:
            raise ValueError(f"invalid or duplicate frontmatter key on line {index}")
        if raw.startswith("[") or raw.startswith("{") or raw.startswith('"'):
            try:
                metadata[key] = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"frontmatter line {index} is not valid JSON: {exc}") from exc
        elif raw in {"true", "false", "null"}:
            metadata[key] = json.loads(raw)
        else:
            metadata[key] = raw
    return metadata, "\n".join(lines[end + 1 :])
