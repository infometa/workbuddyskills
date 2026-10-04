#!/usr/bin/env python3
"""Atomically COMMIT one reviewed DIFF into the canonical source ledger."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    assert_project_root,
    atomic_write_bytes,
    create_bytes_exclusive,
    create_json_exclusive,
    csv_bytes,
    fail,
    file_sha256,
    iso_now,
    json_digest,
    new_id,
    parse_json_array,
    project_file_lock,
    read_csv,
    safe_project_dir,
    safe_project_path,
    schema_fields,
    schema_path,
)
from source_transaction import compute_diff_rows, load_diff_bundle, source_id_for, source_key

SOURCE_SCHEMA = "source.schema.json"


def as_int(value: str, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("scan_id")
    parser.add_argument("--approve-diff-sha256", required=True)
    parser.add_argument("--accept-migrations", action="store_true")
    parser.add_argument("--confirm-empty", action="store_true")
    parser.add_argument("--confirm-missing", action="store_true")
    parser.add_argument("--ledger", default="02_素材账/source-ledger.csv")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    if not re.fullmatch(r"[a-f0-9]{64}", args.approve_diff_sha256):
        fail("--approve-diff-sha256 must be a lowercase SHA-256 digest")

    with project_file_lock(project, "source-ledger"):
        receipt, inventory, diff_receipt, diff_rows, hashes = load_diff_bundle(project, args.scan_id, args.ledger)
        if receipt.get("status") != "complete":
            fail("COMMIT requires a complete scan")
        if diff_receipt["diff_sha256"] != args.approve_diff_sha256:
            fail("reviewed DIFF digest does not match the staged transaction")
        if int(receipt.get("file_count", 0)) == 0 and not args.confirm_empty:
            fail("empty scan requires --confirm-empty")
        if any(row["status"] == "missing" for row in diff_rows) and not args.confirm_missing:
            fail("missing-source decisions require --confirm-missing")
        if any(row["status"] == "move_candidate" for row in diff_rows) and not args.accept_migrations:
            fail("move candidates require --accept-migrations after review")

        staging = safe_project_path(project, Path("02_素材账") / "scan-runs" / args.scan_id)
        terminal_records = sorted(staging.glob("commit-*.json"))
        if terminal_records:
            latest = json.loads(terminal_records[-1].read_text(encoding="utf-8"))
            current_sha = file_sha256(safe_project_path(project, args.ledger, must_exist=True))
            if latest.get("diff_sha256") == args.approve_diff_sha256 and latest.get("ledger_after_sha256") == current_sha:
                print(f"source commit already exact: {latest['commit_id']}")
                return
            fail("scan already has a terminal commit with different current ledger state")
        prepared = sorted(staging.glob("prepare-*.json"))
        if prepared:
            fail("incomplete prepared commit exists; run recover_source_commit.py before another commit")

        ledger_path = safe_project_path(project, args.ledger, must_exist=True)
        old_rows = read_csv(ledger_path, required=True)
        expected_diff = compute_diff_rows(receipt, inventory, hashes, old_rows)
        if json_digest(expected_diff) != json_digest(diff_rows):
            fail("DIFF semantics do not match the current scan and ledger")

        root_id = receipt["root_id"]
        root_label = receipt.get("root_label", root_id)
        inventory_by_path = {row["relative_path"]: row for row in inventory}
        hashes_by_path = {row["relative_path"]: row for row in hashes}
        old_by_key = {
            row.get("source_key") or source_key(row.get("root_id", ""), row.get("relative_path", "")): row
            for row in old_rows
        }
        now = iso_now()
        fields = schema_fields(schema_path(SOURCE_SCHEMA))
        output_rows: list[dict[str, object]] = []
        consumed_old_keys: set[str] = set()
        current_keys: set[str] = set()

        for diff_row in diff_rows:
            status = diff_row["status"]
            if status == "missing":
                continue
            relative = diff_row["relative_path"]
            key = source_key(root_id, relative)
            current_keys.add(key)
            item = inventory_by_path[relative]
            hash_row = hashes_by_path[relative]
            old = old_by_key.get(key)
            moved = status == "move_candidate"
            if moved:
                old_key = diff_row["migration_from_key"]
                old = old_by_key.get(old_key)
                if not old or old.get("root_id") != root_id:
                    fail(f"invalid same-root migration source: {old_key}")
                consumed_old_keys.add(old_key)
            old = old or {}
            unreadable = status == "unreadable"
            changed = status in {"modified", "move_candidate"}
            source_id = old.get("source_id") or source_id_for(root_id, relative)
            history = parse_json_array(old.get("path_history", ""), "source path_history")
            if moved and old.get("relative_path") and old["relative_path"] not in history:
                history.append(old["relative_path"])
            observed_sha = hash_row.get("sha256", "")
            row = {
                "root_id": root_id,
                "root_label": root_label,
                "scan_id": args.scan_id,
                "source_id": source_id,
                "source_key": key,
                "relative_path": relative,
                "path_history": json.dumps(history, ensure_ascii=False),
                "media_type": item.get("media_type", "unknown"),
                "sha256": old.get("sha256", "") if unreadable and old else observed_sha,
                "size_bytes": old.get("size_bytes", "") if unreadable and old else item.get("size_bytes", ""),
                "modified_ns": old.get("modified_ns", "") if unreadable and old else item.get("modified_ns", ""),
                "source_version": as_int(old.get("source_version", "1")) + (1 if changed and old else 0),
                "provider": old.get("provider", ""),
                "narrator": old.get("narrator", ""),
                "visibility": old.get("visibility", "pending"),
                "manuscript_use": old.get("manuscript_use", "pending"),
                "public_use": old.get("public_use", "no"),
                "status": "unreadable" if unreadable else ("modified" if status == "modified" else "active"),
                "needs_reanalysis": "no" if unreadable or moved else ("yes" if status in {"added", "modified", "cross_root_duplicate_candidate"} else old.get("needs_reanalysis", "no")),
                "scan_error": item.get("error", "") if unreadable else "",
                "first_seen_at": old.get("first_seen_at", now),
                "last_seen_at": now,
                "notes": old.get("notes", ""),
            }
            output_rows.append(row)

        for old in old_rows:
            old_key = old.get("source_key") or source_key(old.get("root_id", ""), old.get("relative_path", ""))
            if old_key in consumed_old_keys or old_key in current_keys:
                continue
            if old.get("root_id") == root_id and any(
                row["status"] == "missing" and row["source_key"] == old_key for row in diff_rows
            ):
                old = dict(old)
                old["status"] = "missing"
                old["needs_reanalysis"] = "no"
                old["scan_id"] = args.scan_id
                old["last_seen_at"] = now
            output_rows.append(old)

        source_ids = [str(row.get("source_id", "")) for row in output_rows]
        source_keys = [str(row.get("source_key", "")) for row in output_rows]
        if len(source_ids) != len(set(source_ids)):
            fail("candidate ledger contains duplicate source_id values")
        if len(source_keys) != len(set(source_keys)):
            fail("candidate ledger contains duplicate source_key values")
        output_rows.sort(key=lambda row: str(row.get("source_id", "")))
        candidate_bytes = csv_bytes(fields, output_rows)
        candidate_sha256 = __import__("hashlib").sha256(candidate_bytes).hexdigest()
        before_sha256 = file_sha256(ledger_path)
        commit_id = new_id("COMMIT")
        history_dir = safe_project_dir(project, "02_素材账/ledger-history")
        backup_relative = history_dir / f"source-ledger.before-{commit_id}.csv"
        prepared_record = {
            "schema_version": "2.0",
            "commit_id": commit_id,
            "state": "prepared",
            "scan_id": args.scan_id,
            "root_id": root_id,
            "prepared_at": now,
            "diff_sha256": args.approve_diff_sha256,
            "ledger_before_sha256": before_sha256,
            "ledger_after_sha256": candidate_sha256,
            "backup_relative_path": backup_relative.relative_to(project).as_posix(),
            "row_count": len(output_rows),
        }
        create_json_exclusive(staging / f"prepare-{commit_id}.json", prepared_record, project)
        create_bytes_exclusive(backup_relative, ledger_path.read_bytes(), project)
        atomic_write_bytes(ledger_path, candidate_bytes, project_root=project)
        actual_after = file_sha256(ledger_path)
        if actual_after != candidate_sha256:
            fail("ledger readback hash differs from prepared post-image")
        terminal_record = {
            **prepared_record,
            "state": "committed",
            "committed_at": iso_now(),
            "ledger_after_sha256": actual_after,
            "accept_migrations": args.accept_migrations,
            "confirm_empty": args.confirm_empty,
            "confirm_missing": args.confirm_missing,
        }
        create_json_exclusive(staging / f"commit-{commit_id}.json", terminal_record, project)

    print(f"source commit complete: {commit_id} ({len(output_rows)} rows, sha256={actual_after})")


if __name__ == "__main__":
    main()
