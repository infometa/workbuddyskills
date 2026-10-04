#!/usr/bin/env python3
"""Create one integrity-bound, immutable SCAN staging run."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from pathlib import Path

from common import (
    append_quality_issue,
    assert_project_root,
    file_sha256,
    is_within,
    iso_now,
    iter_safe_files,
    lexical_path,
    new_id,
    read_csv,
    relative_posix,
    safe_project_dir,
    safe_project_path,
    safe_source_scope,
    validate_id,
    write_csv,
    write_json_atomic,
)
from source_registry import resolve_root, update_availability
from source_transaction import HASH_FIELDS, INVENTORY_FIELDS, bundle_digest, source_key


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def empty_receipt(
    scan_id: str,
    root_record: dict,
    source_path: Path,
    scope: str,
    started: str,
    status: str,
    note: str,
) -> dict:
    empty_hash = hashlib.sha256(b"").hexdigest()
    return {
        "schema_version": "2.0",
        "scan_id": scan_id,
        "root_id": root_record["root_id"],
        "root_label": root_record["label"],
        "registered_root_path": root_record["canonical_path"],
        "source_path": str(source_path),
        "scope_relative_path": scope,
        "hash_mode": "none",
        "started_at": started,
        "completed_at": iso_now(),
        "status": status,
        "file_count": 0,
        "error_count": 1,
        "skipped_count": 0,
        "hashed_count": 0,
        "reused_count": 0,
        "inventory_sha256": empty_hash,
        "hashes_sha256": empty_hash,
        "inventory_digest": hashlib.sha256(b"[]").hexdigest(),
        "empty_confirmation_required": True,
        "notes": note,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--root-id", required=True)
    parser.add_argument("--scope", default="")
    parser.add_argument("--scan-id", default="")
    parser.add_argument("--hash-mode", choices=["incremental", "full"], default="incremental")
    args = parser.parse_args()

    project = assert_project_root(args.project_dir)
    root_record = resolve_root(project, root_id=args.root_id)
    source_root = lexical_path(root_record["canonical_path"])
    source_path = safe_source_scope(source_root, args.scope)
    scan_id = validate_id(args.scan_id, "SCAN") if args.scan_id else new_id("SCAN")
    staging = safe_project_dir(project, Path("02_素材账") / "scan-runs" / scan_id)
    if any(staging.iterdir()):
        raise SystemExit(f"scan staging directory is not empty: {staging}")
    started = iso_now()

    if not source_path.is_dir():
        update_availability(project, root_record["root_id"], "unavailable", scan_id)
        receipt = empty_receipt(scan_id, root_record, source_path, args.scope, started, "unavailable", "registered root or scope is unavailable")
        write_json_atomic(staging / "receipt.json", receipt, project_root=project)
        print(f"scan unavailable: {scan_id} -> {staging}")
        return

    old_rows = read_csv(safe_project_path(project, "02_素材账/source-ledger.csv"))
    old_by_key = {row.get("source_key", ""): row for row in old_rows if row.get("root_id") == root_record["root_id"]}
    inventory: list[dict[str, object]] = []
    hashes: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    def note_skip(path: Path, reason: str) -> None:
        relative = relative_posix(path, source_root) if is_within(path, source_root) else str(path)
        skipped.append({"relative_path": relative, "reason": reason})

    excluded = [project] if is_within(project, source_path) else []
    for relative_exclude in root_record.get("exclude_paths", []):
        excluded_path = safe_source_scope(source_root, relative_exclude)
        if is_within(excluded_path, source_path):
            excluded.append(excluded_path)
    try:
        for path in iter_safe_files(source_path, exclude_roots=excluded, on_skip=note_skip):
            relative = relative_posix(path, source_root)
            try:
                stat_result = path.stat()
                media_type = mimetypes.guess_type(path.name)[0] or "unknown"
                previous = old_by_key.get(source_key(root_record["root_id"], relative), {})
                can_reuse = (
                    args.hash_mode == "incremental"
                    and previous.get("sha256", "")
                    and previous.get("size_bytes", "") == str(stat_result.st_size)
                    and previous.get("modified_ns", "") == str(stat_result.st_mtime_ns)
                    and previous.get("status") not in {"missing", "unreadable"}
                )
                if can_reuse:
                    sha256 = previous["sha256"]
                    hash_status = "reused"
                else:
                    sha256 = digest(path)
                    hash_status = "hashed"
                inventory.append(
                    {
                        "root_id": root_record["root_id"],
                        "scan_id": scan_id,
                        "relative_path": relative,
                        "name": path.name,
                        "suffix": path.suffix.lower(),
                        "media_type": media_type,
                        "size_bytes": stat_result.st_size,
                        "modified_ns": stat_result.st_mtime_ns,
                        "status": "observed",
                        "error": "",
                    }
                )
                hashes.append(
                    {
                        "root_id": root_record["root_id"],
                        "scan_id": scan_id,
                        "relative_path": relative,
                        "sha256": sha256,
                        "size_bytes": stat_result.st_size,
                        "status": hash_status,
                        "error": "",
                    }
                )
            except OSError as exc:
                error = str(exc)
                errors.append({"relative_path": relative, "error": error})
                inventory.append(
                    {
                        "root_id": root_record["root_id"],
                        "scan_id": scan_id,
                        "relative_path": relative,
                        "name": path.name,
                        "suffix": path.suffix.lower(),
                        "media_type": mimetypes.guess_type(path.name)[0] or "unknown",
                        "size_bytes": "",
                        "modified_ns": "",
                        "status": "unreadable",
                        "error": error,
                    }
                )
                hashes.append(
                    {
                        "root_id": root_record["root_id"],
                        "scan_id": scan_id,
                        "relative_path": relative,
                        "sha256": "",
                        "size_bytes": "",
                        "status": "unreadable",
                        "error": error,
                    }
                )
    except OSError as exc:
        errors.append({"relative_path": args.scope or ".", "error": f"scan interrupted: {exc}"})

    inventory.sort(key=lambda row: str(row["relative_path"]))
    hashes.sort(key=lambda row: str(row["relative_path"]))
    write_csv(staging / "inventory.csv", INVENTORY_FIELDS, inventory, project_root=project)
    write_csv(staging / "hashes.csv", HASH_FIELDS, hashes, project_root=project)
    if errors:
        write_json_atomic(staging / "errors.json", errors, project_root=project)
        for item in errors:
            append_quality_issue(project, item["relative_path"], "source_scan_error", item["error"])
    if skipped:
        write_json_atomic(staging / "skipped.json", skipped, project_root=project)

    inventory_path = safe_project_path(project, staging / "inventory.csv", must_exist=True)
    hashes_path = safe_project_path(project, staging / "hashes.csv", must_exist=True)
    status = "partial" if errors else "complete"
    receipt = {
        "schema_version": "2.0",
        "scan_id": scan_id,
        "root_id": root_record["root_id"],
        "root_label": root_record["label"],
        "registered_root_path": root_record["canonical_path"],
        "source_path": str(source_path),
        "scope_relative_path": args.scope,
        "hash_mode": args.hash_mode,
        "started_at": started,
        "completed_at": iso_now(),
        "status": status,
        "file_count": len(inventory),
        "error_count": len(errors),
        "skipped_count": len(skipped),
        "hashed_count": sum(row["status"] == "hashed" for row in hashes),
        "reused_count": sum(row["status"] == "reused" for row in hashes),
        "inventory_sha256": file_sha256(inventory_path),
        "hashes_sha256": file_sha256(hashes_path),
        "inventory_digest": bundle_digest(inventory, hashes),
        "empty_confirmation_required": len(inventory) == 0,
        "notes": "staged and integrity-bound; committed ledger unchanged",
    }
    write_json_atomic(staging / "receipt.json", receipt, project_root=project)
    update_availability(project, root_record["root_id"], "available", scan_id, successful=status == "complete")
    print(
        f"scan staged: {scan_id} ({status}, files={len(inventory)}, hashed={receipt['hashed_count']}, "
        f"reused={receipt['reused_count']}, errors={len(errors)}, skipped={len(skipped)}) -> {staging}"
    )


if __name__ == "__main__":
    main()
