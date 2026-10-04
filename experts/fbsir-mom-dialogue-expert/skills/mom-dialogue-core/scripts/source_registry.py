#!/usr/bin/env python3
"""Validated source-root registry helpers."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from common import (
    fail,
    lexical_path,
    new_id,
    project_file_lock,
    safe_project_path,
    validate_id,
    write_json_atomic,
)

REGISTRY_RELATIVE = "00_项目看板/source-roots.json"
REGISTRY_SCHEMA_VERSION = "2.0"


def registry_path(project: Path) -> Path:
    return safe_project_path(project, REGISTRY_RELATIVE)


def normalized_path_key(path: str | Path) -> str:
    value = str(lexical_path(path))
    return os.path.normcase(value).casefold() if os.name == "nt" else value


def validate_root_record(record: dict) -> None:
    required = {
        "root_id",
        "label",
        "canonical_path",
        "authorized_at",
        "availability",
        "last_scan_id",
        "last_successful_scan_id",
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"source registry record is missing fields: {missing}")
    validate_id(str(record.get("root_id", "")), "ROOT")
    if not str(record.get("label", "")).strip():
        fail("source registry label cannot be empty")
    if not Path(str(record.get("canonical_path", ""))).is_absolute():
        fail("source registry canonical_path must be absolute")
    if record.get("availability") not in {"available", "unavailable", "unknown"}:
        fail(f"invalid source availability: {record.get('availability')}")
    for field in ("last_scan_id", "last_successful_scan_id"):
        if record.get(field):
            validate_id(str(record[field]), "SCAN")
    if record.get("registration_fingerprint") and not re.fullmatch(r"[a-f0-9]{64}", str(record["registration_fingerprint"])):
        fail(f"invalid source registration fingerprint: {record.get('root_id')}")
    excludes = record.get("exclude_paths", [])
    if not isinstance(excludes, list) or not all(isinstance(item, str) and item and ".." not in Path(item).parts for item in excludes):
        fail(f"invalid source exclude_paths: {record.get('root_id')}")


def read_registry(project: Path) -> dict:
    path = registry_path(project)
    if not path.exists():
        return {"schema_version": REGISTRY_SCHEMA_VERSION, "roots": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid source registry: {path}: {exc}")
    if data.get("schema_version") != REGISTRY_SCHEMA_VERSION or not isinstance(data.get("roots"), list):
        fail(f"unsupported source registry schema: {path}")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for record in data["roots"]:
        if not isinstance(record, dict):
            fail(f"invalid source registry record: {record!r}")
        validate_root_record(record)
        root_id = record["root_id"]
        path_key = normalized_path_key(record["canonical_path"])
        if root_id in seen_ids:
            fail(f"duplicate source root id: {root_id}")
        if path_key in seen_paths:
            fail(f"duplicate source canonical path: {record['canonical_path']}")
        seen_ids.add(root_id)
        seen_paths.add(path_key)
    return data


def write_registry(project: Path, data: dict) -> None:
    data = dict(data)
    data["schema_version"] = REGISTRY_SCHEMA_VERSION
    for record in data.get("roots", []):
        validate_root_record(record)
    write_json_atomic(registry_path(project), data, project_root=project)


def make_root_id() -> str:
    return new_id("ROOT")


def resolve_root(project: Path, root_id: str | None = None, source_dir: str | Path | None = None) -> dict:
    roots = read_registry(project).get("roots", [])
    if root_id:
        validate_id(root_id, "ROOT")
        for record in roots:
            if record["root_id"] == root_id:
                return record
        fail(f"source root is not registered: {root_id}")
    if source_dir is not None:
        key = normalized_path_key(source_dir)
        for record in roots:
            if normalized_path_key(record["canonical_path"]) == key:
                return record
    if len(roots) == 1:
        return roots[0]
    fail("specify --root-id when zero or multiple source roots are registered")


def update_availability(
    project: Path,
    root_id: str,
    availability: str,
    last_scan_id: str = "",
    successful: bool = False,
) -> None:
    validate_id(root_id, "ROOT")
    with project_file_lock(project, "source-registry"):
        data = read_registry(project)
        for record in data["roots"]:
            if record["root_id"] == root_id:
                record["availability"] = availability
                if last_scan_id:
                    validate_id(last_scan_id, "SCAN")
                    record["last_scan_id"] = last_scan_id
                    if successful:
                        record["last_successful_scan_id"] = last_scan_id
                write_registry(project, data)
                return
    fail(f"source root is not registered: {root_id}")
