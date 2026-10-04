#!/usr/bin/env python3
"""Validate a local NGO challenge draft without network or file writes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_THEMES = {
    "文書撰寫",
    "數據整理",
    "知識查找",
    "流程管理",
    "其他",
}

SCHEMA_VERSION = "1.2"

REQUIRED_TEXT_FIELDS = (
    "title",
    "organization_name",
    "theme",
    "pain_point",
    "current_situation",
    "current_method",
    "desired_outcome",
)


def validate(data: dict) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f'schema_version must be "{SCHEMA_VERSION}"')

    publishable = data.get("publishable")
    state = data.get("conversation_state")
    metadata = data.get("internal_metadata")

    if not isinstance(publishable, dict):
        return ["publishable must be an object"]
    if not isinstance(state, dict):
        errors.append("conversation_state must be an object")
        state = {}
    if not isinstance(metadata, dict):
        errors.append("internal_metadata must be an object")
        metadata = {}

    for field in REQUIRED_TEXT_FIELDS:
        value = publishable.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"publishable.{field} is required")

    theme = publishable.get("theme")
    if isinstance(theme, str) and theme and theme not in ALLOWED_THEMES:
        errors.append(f"publishable.theme '{theme}' is not in allowed themes: {', '.join(sorted(ALLOWED_THEMES))}")

    for field in ("success_criteria", "materials", "boundaries"):
        value = publishable.get(field)
        if not isinstance(value, list) or not any(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"publishable.{field} must contain at least one confirmed item")

    if metadata.get("fit_status") != "pass":
        errors.append("internal_metadata.fit_status must be 'pass' before synchronization")

    if state.get("explicit_confirmation") is not True:
        errors.append("conversation_state.explicit_confirmation must be true")

    if state.get("status") not in {"ready_to_sync", "syncing", "synced"}:
        errors.append("conversation_state.status is not ready for synchronization")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an NGO challenge JSON file")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()

    with args.json_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    errors = validate(data)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({"valid": True, "errors": []}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
