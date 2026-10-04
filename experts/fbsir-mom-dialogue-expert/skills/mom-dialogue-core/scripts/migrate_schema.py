#!/usr/bin/env python3
"""Explicit, backed-up migration from the 0.9.x project shape to schema 2.0."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from common import (
    assert_project_root,
    atomic_write_bytes,
    file_sha256,
    iso_now,
    new_id,
    project_file_lock,
    read_csv,
    safe_project_dir,
    safe_project_path,
    schema_fields,
    schema_path,
    utc_stamp,
    validate_id,
    write_csv,
    write_json_atomic,
)
from source_registry import REGISTRY_SCHEMA_VERSION, normalized_path_key


def old_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle), [])


def defaults(path: str, row: dict[str, str], now: str) -> dict[str, str]:
    value = dict(row)
    array_fields = {
        "02_素材账/source-ledger.csv": ["path_history"],
        "03_人物与关系/person-ledger.csv": ["aliases", "languages", "source_ids"],
        "03_人物与关系/relationship-ledger.csv": ["source_ids"],
        "03_人物与关系/role-ledger.csv": ["permissions", "source_ids"],
        "05_媒体索引/media-index.csv": ["person_ids"],
        "06_事件与生活轨迹/event-ledger.csv": ["person_ids", "source_ids"],
        "07_问题与回答/question-ledger.csv": ["source_ids"],
        "07_问题与回答/answer-ledger.csv": ["source_ids"],
        "09_心愿与家庭行动/action-ledger.csv": ["source_ids", "story_ids", "owner_person_ids"],
        "10_大纲与章节/chapter-ledger.csv": ["story_ids", "source_ids"],
        "11_隐私与授权/consent-ledger.csv": ["evidence_source_ids"],
    }
    for field in array_fields.get(path, []):
        value[field] = value.get(field) or "[]"
    if path == "02_素材账/source-ledger.csv":
        value.setdefault("source_version", "1")
        value["source_version"] = value.get("source_version") or "1"
        value["visibility"] = value.get("visibility") or "pending"
        value["manuscript_use"] = value.get("manuscript_use") or "pending"
        value["public_use"] = value.get("public_use") or "no"
        value["needs_reanalysis"] = value.get("needs_reanalysis") or "yes"
        value["scan_error"] = value.get("scan_error", "")
        if value.get("status") == "move_candidate":
            value["status"] = "pending"
    elif path == "03_人物与关系/person-ledger.csv":
        value["birth_year_precision"] = value.get("birth_year_precision") or "unknown"
        value["status"] = value.get("status") or "unknown"
    elif path == "03_人物与关系/relationship-ledger.csv":
        value["status"] = value.get("status") or "unknown"
    elif path == "05_媒体索引/media-index.csv":
        value["timecode_precision"] = value.get("timecode_precision") or "unknown"
        value["source_status"] = value.get("source_status") or "pending"
        value["coverage_status"] = value.get("coverage_status") or "planned"
        value["status"] = value.get("status") or "pending"
    elif path == "06_事件与生活轨迹/event-ledger.csv":
        value["source_status"] = value.get("source_status") or "unknown"
        value["status"] = value.get("status") or "unknown"
    elif path == "11_隐私与授权/consent-ledger.csv":
        legacy_id = value.get("source_or_story_id", "")
        value["object_id"] = value.get("object_id") or legacy_id
        if not value.get("object_type"):
            value["object_type"] = "source" if legacy_id.startswith("SRC-") else "story"
        value["family_visibility"] = value.get("family_visibility") or "pending"
        value["manuscript_use"] = value.get("manuscript_use") or "pending"
        value["public_use"] = value.get("public_use") or "pending"
        value["anonymize"] = {"yes": "required", "true": "required"}.get(value.get("anonymize", "").lower(), value.get("anonymize") or "no")
        value["sensitive"] = value.get("sensitive") or "no"
        value["status"] = value.get("status") or "pending"
        value["recorded_at"] = value.get("recorded_at") or now
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    now = iso_now()
    catalog_path = schema_path("schema-catalog.json")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    changes = []

    with project_file_lock(project, "schema-migration"):
        registry_path = safe_project_path(project, "00_项目看板/source-roots.json")
        if not registry_path.exists():
            legacy_path = safe_project_path(project, "00_项目看板/source-registry.json")
            roots = []
            if legacy_path.exists():
                legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
                for item in legacy.get("roots", []):
                    root_id = item.get("root_id", "")
                    try:
                        validate_id(root_id, "ROOT")
                    except SystemExit:
                        root_id = new_id("ROOT")
                    canonical = item.get("canonical_path", "")
                    roots.append(
                        {
                            "root_id": root_id,
                            "label": item.get("label") or root_id,
                            "canonical_path": canonical,
                            "device_hint": item.get("device_hint", ""),
                            "authorized_at": item.get("authorized_at") or now,
                            "availability": item.get("availability") if item.get("availability") in {"available", "unavailable", "unknown"} else "unknown",
                            "last_scan_id": item.get("last_scan", ""),
                            "last_successful_scan_id": item.get("last_scan", "") if item.get("availability") == "available" else "",
                            "registration_fingerprint": hashlib.sha256(f"{root_id}|{normalized_path_key(canonical)}".encode("utf-8")).hexdigest(),
                            "exclude_paths": [],
                        }
                    )
                changes.append({"path": "00_项目看板/source-roots.json", "action": "migrated_from_source-registry"})
            write_json_atomic(registry_path, {"schema_version": REGISTRY_SCHEMA_VERSION, "roots": roots}, project_root=project)

        for entry in catalog["ledgers"]:
            path = safe_project_path(project, entry["path"])
            fields = schema_fields(schema_path(entry["schema"]))
            header = old_header(path)
            if header == fields:
                continue
            old_rows = read_csv(path) if path.exists() else []
            if path.exists():
                backup_dir = safe_project_dir(project, "12_版本与检查点/schema-migration-backups")
                backup = backup_dir / f"{path.stem}.{utc_stamp()}.csv"
                atomic_write_bytes(backup, path.read_bytes(), project_root=project)
            transformed = []
            for row in old_rows:
                prepared = defaults(entry["path"], row, now)
                transformed.append({field: prepared.get(field, "") for field in fields})
            write_csv(path, fields, transformed, project_root=project)
            changes.append({"path": entry["path"], "action": "created" if not header else "header_migrated", "rows": len(transformed)})

        marker_path = safe_project_path(project, ".mom-dialogue-project.json", must_exist=True)
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        roots_data = json.loads(registry_path.read_text(encoding="utf-8"))
        marker = {
            "project_type": "fbsir-mom-dialogue",
            "schema_version": "2.0",
            "created_at": marker.get("created_at") or now,
            "source_files_read_only": True,
            "write_scope": "project-directory-only",
            "source_roots_registered": [item["root_id"] for item in roots_data.get("roots", [])],
        }
        write_json_atomic(marker_path, marker, project_root=project)
        state_path = safe_project_path(project, "00_项目看板/schema-state.json")
        write_json_atomic(
            state_path,
            {"schemaVersion": "2.0", "catalogSha256": file_sha256(catalog_path), "migratedAt": now, "changeCount": len(changes)},
            project_root=project,
        )
        report_path = safe_project_path(project, f"13_导出成果/schema-migration-{utc_stamp()}.json")
        write_json_atomic(report_path, {"schemaVersion": "2.0", "migratedAt": now, "changes": changes}, project_root=project)
    print(f"schema migration complete: changes={len(changes)} -> {report_path}")


if __name__ == "__main__":
    main()
