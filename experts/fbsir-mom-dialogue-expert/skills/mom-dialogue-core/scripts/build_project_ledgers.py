#!/usr/bin/env python3
"""Check or explicitly migrate all CSV ledgers from the schema catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import assert_project_root, ensure_csv_schema, iso_now, safe_project_path, utc_stamp, write_json_atomic


def load_catalog() -> dict:
    path = Path(__file__).resolve().parents[1] / "schemas" / "schema-catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "2.0" or not isinstance(data.get("ledgers"), list):
        raise SystemExit(f"invalid schema catalog: {path}")
    return data


def check_or_migrate(project: Path, fix: bool) -> list[dict[str, object]]:
    changes = []
    for entry in load_catalog()["ledgers"]:
        path, fields, mismatch = ensure_csv_schema(project, entry["path"], entry["schema"], repair=fix)
        if mismatch:
            changes.append({"path": entry["path"], "schema": entry["schema"], "fields": fields, "fixed": fix, "exists_after": path.exists()})
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--fix", action="store_true", help="Create/migrate ledgers; without this flag the command is read-only")
    parser.add_argument("--check-only", action="store_true", help="Explicit read-only alias")
    args = parser.parse_args()
    if args.fix and args.check_only:
        parser.error("--fix and --check-only are mutually exclusive")
    project = assert_project_root(args.project_dir)
    changes = check_or_migrate(project, args.fix)
    if changes and not args.fix:
        print("schema mismatches:")
        for item in changes:
            print(f"- {item['path']} -> {item['schema']}")
        raise SystemExit(1)
    if args.fix:
        report = {
            "schemaVersion": "2.0",
            "generatedAt": iso_now(),
            "project": str(project),
            "changedCount": len(changes),
            "changes": changes,
        }
        report_path = safe_project_path(project, f"13_导出成果/schema-migration-{utc_stamp()}.json")
        write_json_atomic(report_path, report, project_root=project)
        print(f"schema-driven ledgers ready: changed={len(changes)} -> {report_path}")
    else:
        print("ledger schema check: PASS")


if __name__ == "__main__":
    main()
