#!/usr/bin/env python3
"""Apply a structured, lock-aware revision patch to content-state.v1."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    from validate_content_state import validate_state
except ImportError:
    from scripts.validate_content_state import validate_state

ALLOWED_SET_FIELDS = {
    "masthead.text",
    "date.text",
    "headline.original",
    "sub_headline.text",
    "primary_photo.path",
    "primary_photo.focal_point",
    "selected_template",
}


def _get_path(state: dict[str, Any], path: str) -> Any:
    value: Any = state
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"unknown state field: {path}")
        value = value[part]
    return value


def _set_path(state: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    target: Any = state
    for part in parts[:-1]:
        if not isinstance(target, dict) or part not in target:
            raise ValueError(f"unknown state field: {path}")
        target = target[part]
    if not isinstance(target, dict):
        raise ValueError(f"state field is not writable: {path}")
    target[parts[-1]] = value


def apply_patch(state: dict[str, Any], patch: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    if patch.get("base_revision_id") != state.get("revision_id"):
        raise ValueError("patch base_revision_id does not match current revision_id")
    updates = patch.get("set", {})
    if not isinstance(updates, dict):
        raise ValueError("patch.set must be an object")

    locked = set(state.get("locked_fields", []))
    for field, value in updates.items():
        if field not in ALLOWED_SET_FIELDS:
            raise ValueError(f"field is not patchable: {field}")
        if field in locked:
            raise ValueError(f"field is locked and cannot be changed: {field}")
        _set_path(state, field, value)

    next_state = copy.deepcopy(state)
    for field, value in updates.items():
        _set_path(next_state, field, value)

    next_state["locked_fields"] = sorted(set(locked).union(patch.get("lock", [])))
    next_state["locked_fields"] = [field for field in next_state["locked_fields"] if field]
    unlock = set(patch.get("unlock", []))
    next_state["locked_fields"] = [field for field in next_state["locked_fields"] if field not in unlock]
    next_state["rejected_styles"] = sorted(set(state.get("rejected_styles", [])).union(patch.get("reject_styles", [])))
    if "selected_template" in updates:
        next_state["selected_template"] = updates["selected_template"]
    next_state["parent_revision_id"] = state["revision_id"]
    next_state["revision_id"] = str(patch.get("revision_id", f"{state['revision_id']}-next"))
    if patch.get("note"):
        next_state["notes"] = str(patch["note"])

    # A changed headline must be explicitly reconfirmed; never silently claim it is confirmed.
    if "headline.original" in updates:
        next_state["headline"]["confirmed"] = False
    errors = validate_state(next_state, base_dir, check_files=True)
    if errors:
        raise ValueError("patched state invalid: " + "; ".join(errors))
    return next_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a Tietu Toutiao revision patch")
    parser.add_argument("--input", required=True, help="current content-state.v1 JSON")
    parser.add_argument("--patch", required=True, help="revision patch JSON")
    parser.add_argument("--output", required=True, help="next content-state.v1 JSON")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    patch_path = Path(args.patch).resolve()
    output_path = Path(args.output).resolve()
    try:
        state = json.loads(input_path.read_text(encoding="utf-8"))
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
        errors = validate_state(state, input_path.parent, check_files=True)
        if errors:
            raise ValueError("current state invalid: " + "; ".join(errors))
        next_state = apply_patch(state, patch, input_path.parent)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(next_state, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"[OK] patch applied: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
