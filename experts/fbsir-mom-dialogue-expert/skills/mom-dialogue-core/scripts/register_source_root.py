#!/usr/bin/env python3
"""Register one explicitly authorized, read-only source root."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from common import (
    assert_project_root,
    check_existing_components,
    fail,
    is_reparse_point,
    is_within,
    iso_now,
    lexical_path,
    project_file_lock,
    safe_project_path,
    validate_id,
    write_json_atomic,
)
from source_registry import make_root_id, normalized_path_key, read_registry, write_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("source_dir")
    parser.add_argument("--label", default="")
    parser.add_argument("--device-hint", default="")
    parser.add_argument("--root-id", default="")
    parser.add_argument("--exclude", action="append", default=[], help="Source-root-relative directory to exclude")
    args = parser.parse_args()

    project = assert_project_root(args.project_dir)
    source = lexical_path(args.source_dir)
    check_existing_components(source)
    if not source.is_dir() or is_reparse_point(source):
        fail(f"source root does not exist or is unsafe: {source}")
    if source == project or is_within(source, project):
        fail("a source root cannot be the project directory or one of its descendants")

    label = (args.label or source.name or str(source)).strip()
    if not label or len(label) > 120:
        fail("source label must contain 1-120 characters")
    if len(args.device_hint) > 200:
        fail("device hint exceeds 200 characters")
    requested_id = validate_id(args.root_id, "ROOT") if args.root_id else ""
    excludes = []
    for value in args.exclude:
        candidate = Path(value)
        if candidate.drive or candidate.root or candidate.is_absolute() or any(part in {"", ".."} for part in candidate.parts):
            fail(f"exclude path must be a safe source-relative path: {value}")
        excludes.append(candidate.as_posix())
    excludes = sorted(set(excludes))
    now = iso_now()

    with project_file_lock(project, "source-registry"):
        data = read_registry(project)
        roots = data.setdefault("roots", [])
        source_key = normalized_path_key(source)
        existing = next((item for item in roots if normalized_path_key(item["canonical_path"]) == source_key), None)
        if existing:
            if requested_id and requested_id != existing["root_id"]:
                fail(f"source path is already registered as {existing['root_id']}")
            root_id = existing["root_id"]
            existing.update(
                {
                    "label": label,
                    "canonical_path": str(source),
                    "device_hint": args.device_hint or existing.get("device_hint", ""),
                    "availability": "available",
                    "last_scan_id": existing.get("last_scan_id", ""),
                    "last_successful_scan_id": existing.get("last_successful_scan_id", ""),
                    "exclude_paths": excludes or existing.get("exclude_paths", []),
                }
            )
        else:
            root_id = requested_id or make_root_id()
            if any(item["root_id"] == root_id for item in roots):
                fail(f"root id is already registered: {root_id}")
            roots.append(
                {
                    "root_id": root_id,
                    "label": label,
                    "canonical_path": str(source),
                    "device_hint": args.device_hint,
                    "authorized_at": now,
                    "availability": "available",
                    "last_scan_id": "",
                    "last_successful_scan_id": "",
                    "registration_fingerprint": hashlib.sha256(
                        f"{root_id}|{source_key}|{label}|{args.device_hint}".encode("utf-8")
                    ).hexdigest(),
                    "exclude_paths": excludes,
                }
            )
        roots.sort(key=lambda item: item["root_id"])
        write_registry(project, data)

        marker_path = safe_project_path(project, ".mom-dialogue-project.json", must_exist=True)
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        marker["source_roots_registered"] = [item["root_id"] for item in roots]
        write_json_atomic(marker_path, marker, project_root=project)

    print(f"registered source root: {root_id} ({label}) -> {source}")


if __name__ == "__main__":
    main()
