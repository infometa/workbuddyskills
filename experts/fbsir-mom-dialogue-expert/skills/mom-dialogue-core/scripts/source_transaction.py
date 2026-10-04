#!/usr/bin/env python3
"""Integrity primitives shared by SCAN, DIFF, and COMMIT."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from common import (
    assert_project_input,
    fail,
    file_sha256,
    json_digest,
    read_csv,
    safe_project_path,
    safe_source_scope,
    schema_fields,
    schema_path,
    validate_id,
)
from source_registry import normalized_path_key, read_registry

INVENTORY_FIELDS = schema_fields(schema_path("inventory.schema.json"))
HASH_FIELDS = schema_fields(schema_path("hash-manifest.schema.json"))
DIFF_FIELDS = schema_fields(schema_path("source-diff.schema.json"))
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def source_id_for(root_id: str, relative_path: str) -> str:
    value = f"{root_id}::{relative_path.replace(chr(92), '/')}"
    return "SRC-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12].upper()


def source_key(root_id: str, relative_path: str) -> str:
    return f"{root_id}::{relative_path.replace(chr(92), '/')}"


def scan_dir(project: Path, scan_id: str) -> Path:
    validate_id(scan_id, "SCAN")
    return safe_project_path(project, Path("02_素材账") / "scan-runs" / scan_id)


def read_header(path: Path) -> list[str]:
    import csv

    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle), [])


def bundle_digest(inventory: list[dict[str, str]], hashes: list[dict[str, str]]) -> str:
    hash_by_path = {row.get("relative_path", ""): row for row in hashes}
    projection = []
    for item in sorted(inventory, key=lambda row: row.get("relative_path", "")):
        relative = item.get("relative_path", "")
        hashed = hash_by_path.get(relative, {})
        projection.append(
            {
                "root_id": str(item.get("root_id", "")),
                "scan_id": str(item.get("scan_id", "")),
                "relative_path": str(relative),
                "media_type": str(item.get("media_type", "")),
                "size_bytes": str(item.get("size_bytes", "")),
                "modified_ns": str(item.get("modified_ns", "")),
                "inventory_status": str(item.get("status", "")),
                "hash_status": str(hashed.get("status", "")),
                "sha256": str(hashed.get("sha256", "")),
                "error": str(item.get("error", "") or hashed.get("error", "")),
            }
        )
    return json_digest(projection)


def ledger_sha256(project: Path, ledger_relative: str = "02_素材账/source-ledger.csv") -> str:
    path = safe_project_path(project, ledger_relative, must_exist=True)
    return file_sha256(path)


def load_scan_bundle(project: Path, scan_id: str) -> tuple[dict, list[dict[str, str]], list[dict[str, str]]]:
    staging = scan_dir(project, scan_id)
    receipt_path = assert_project_input(project, staging / "receipt.json", ["02_素材账/scan-runs"])
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid scan receipt: {exc}")
    errors: list[str] = []
    required = {
        "schema_version",
        "scan_id",
        "root_id",
        "source_path",
        "scope_relative_path",
        "started_at",
        "completed_at",
        "status",
        "file_count",
        "error_count",
        "skipped_count",
        "hashed_count",
        "reused_count",
        "inventory_sha256",
        "hashes_sha256",
        "inventory_digest",
    }
    missing = sorted(required - set(receipt))
    if missing:
        errors.append(f"missing receipt fields: {missing}")
    if receipt.get("schema_version") != "2.0":
        errors.append("unsupported scan receipt schema_version")
    if receipt.get("scan_id") != scan_id:
        errors.append("scan_id mismatch")
    try:
        validate_id(str(receipt.get("root_id", "")), "ROOT")
    except SystemExit:
        errors.append("invalid root_id")
    if receipt.get("status") not in {"complete", "partial", "unavailable", "failed"}:
        errors.append(f"invalid scan status: {receipt.get('status')}")
    roots = {item["root_id"]: item for item in read_registry(project).get("roots", [])}
    root_record = roots.get(receipt.get("root_id"))
    if not root_record:
        errors.append("root_id is not registered")
    else:
        if normalized_path_key(root_record["canonical_path"]) != normalized_path_key(receipt.get("registered_root_path", root_record["canonical_path"])):
            errors.append("registered source root path mismatch")
        try:
            expected_source_path = safe_source_scope(root_record["canonical_path"], str(receipt.get("scope_relative_path", "")))
            if normalized_path_key(expected_source_path) != normalized_path_key(str(receipt.get("source_path", ""))):
                errors.append("scan source_path does not match registered root and scope")
        except SystemExit:
            errors.append("scan scope is outside the registered source root")

    inventory: list[dict[str, str]] = []
    hashes: list[dict[str, str]] = []
    inventory_path = staging / "inventory.csv"
    hashes_path = staging / "hashes.csv"
    if receipt.get("status") in {"complete", "partial"}:
        try:
            inventory_path = assert_project_input(project, inventory_path, ["02_素材账/scan-runs"])
            hashes_path = assert_project_input(project, hashes_path, ["02_素材账/scan-runs"])
            if read_header(inventory_path) != INVENTORY_FIELDS:
                errors.append("inventory header mismatch")
            if read_header(hashes_path) != HASH_FIELDS:
                errors.append("hashes header mismatch")
            inventory = read_csv(inventory_path, required=True)
            hashes = read_csv(hashes_path, required=True)
            if file_sha256(inventory_path) != receipt.get("inventory_sha256"):
                errors.append("inventory file hash mismatch")
            if file_sha256(hashes_path) != receipt.get("hashes_sha256"):
                errors.append("hashes file hash mismatch")
        except SystemExit:
            errors.append("scan staging files are missing or unsafe")
    elif inventory_path.exists() or hashes_path.exists():
        errors.append("unavailable/failed scan must not carry a partial inventory")

    inventory_paths: set[str] = set()
    hash_paths: set[str] = set()
    for row in inventory:
        relative = row.get("relative_path", "")
        if not relative or relative in inventory_paths:
            errors.append(f"duplicate or empty inventory path: {relative}")
        inventory_paths.add(relative)
        if row.get("root_id") != receipt.get("root_id") or row.get("scan_id") != scan_id:
            errors.append(f"inventory identity mismatch: {relative}")
        if row.get("status") not in {"observed", "unreadable"}:
            errors.append(f"invalid inventory status: {relative}")
    for row in hashes:
        relative = row.get("relative_path", "")
        if not relative or relative in hash_paths:
            errors.append(f"duplicate or empty hash path: {relative}")
        hash_paths.add(relative)
        if row.get("root_id") != receipt.get("root_id") or row.get("scan_id") != scan_id:
            errors.append(f"hash identity mismatch: {relative}")
        status = row.get("status")
        digest = row.get("sha256", "")
        if status not in {"hashed", "reused", "unreadable"}:
            errors.append(f"invalid hash status: {relative}")
        if status in {"hashed", "reused"} and not SHA256_PATTERN.fullmatch(digest):
            errors.append(f"invalid sha256: {relative}")
        if status == "unreadable" and digest:
            errors.append(f"unreadable row carries sha256: {relative}")
    if inventory_paths != hash_paths:
        errors.append("inventory and hash path sets differ")
    if len(inventory) != int(receipt.get("file_count", -1)):
        errors.append("file_count mismatch")
    if receipt.get("status") in {"complete", "partial"}:
        if sum(row.get("status") == "hashed" for row in hashes) != int(receipt.get("hashed_count", -1)):
            errors.append("hashed_count mismatch")
        if sum(row.get("status") == "reused" for row in hashes) != int(receipt.get("reused_count", -1)):
            errors.append("reused_count mismatch")
        if sum(row.get("status") == "unreadable" for row in hashes) != int(receipt.get("error_count", -1)):
            errors.append("error_count mismatch")
    if receipt.get("status") in {"complete", "partial"} and bundle_digest(inventory, hashes) != receipt.get("inventory_digest"):
        errors.append("combined inventory digest mismatch")
    if receipt.get("status") == "complete" and int(receipt.get("error_count", -1)) != 0:
        errors.append("complete scan cannot contain errors")
    if receipt.get("status") == "partial" and int(receipt.get("error_count", 0)) == 0:
        errors.append("partial scan must contain at least one error")
    if errors:
        fail("invalid scan receipt:\n- " + "\n- ".join(errors), code=1)
    return receipt, inventory, hashes


def latest_scan_id(project: Path) -> str:
    root = safe_project_path(project, "02_素材账/scan-runs")
    if not root.exists():
        fail("no scan runs found")
    candidates: list[tuple[str, str]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        path = safe_project_path(project, child / "receipt.json")
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            candidates.append((str(data.get("completed_at", "")), child.name))
        except Exception:
            continue
    if not candidates:
        fail("no valid scan receipt found")
    return sorted(candidates)[-1][1]


def compute_diff_rows(
    receipt: dict,
    inventory: list[dict[str, str]],
    hashes: list[dict[str, str]],
    old_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    root_id = receipt["root_id"]
    hash_by_path = {row["relative_path"]: row for row in hashes}
    old_by_key = {
        row.get("source_key") or source_key(row.get("root_id", ""), row.get("relative_path", "")): row
        for row in old_rows
    }
    current_keys = {source_key(root_id, row["relative_path"]) for row in inventory}
    absent_same_root = [
        row
        for row in old_rows
        if row.get("root_id") == root_id
        and (row.get("source_key") or source_key(root_id, row.get("relative_path", ""))) not in current_keys
    ]
    rows: list[dict[str, object]] = []
    used_move_keys: set[str] = set()
    for item in sorted(inventory, key=lambda row: row["relative_path"]):
        relative = item["relative_path"]
        key = source_key(root_id, relative)
        previous = old_by_key.get(key)
        hash_row = hash_by_path[relative]
        digest = hash_row.get("sha256", "")
        candidate_id = source_id_for(root_id, relative)
        base = {
            "root_id": root_id,
            "scan_id": receipt["scan_id"],
            "source_id": previous.get("source_id", "") if previous else "",
            "candidate_source_id": candidate_id,
            "source_key": key,
            "relative_path": relative,
            "sha256": digest,
            "status": "",
            "needs_reanalysis": "no",
            "migration_from_key": "",
            "reason": "",
        }
        if previous:
            if item.get("status") == "unreadable" or not digest:
                base.update(status="unreadable", reason="scan_could_not_read_file")
            elif previous.get("sha256") != digest or previous.get("size_bytes") != item.get("size_bytes"):
                base.update(status="modified", needs_reanalysis="yes", reason="hash_or_size_changed")
            else:
                base.update(status="unchanged", needs_reanalysis=previous.get("needs_reanalysis", "no"), reason="same_hash_and_size")
        elif digest:
            moves = [row for row in absent_same_root if row.get("sha256") == digest]
            moves = [row for row in moves if (row.get("source_key") or source_key(root_id, row.get("relative_path", ""))) not in used_move_keys]
            if len(moves) == 1:
                old = moves[0]
                old_key = old.get("source_key") or source_key(root_id, old.get("relative_path", ""))
                used_move_keys.add(old_key)
                base.update(
                    source_id=old.get("source_id", ""),
                    status="move_candidate",
                    needs_reanalysis="no",
                    migration_from_key=old_key,
                    reason="same_root_unique_hash_move_candidate",
                )
            elif any(row.get("root_id") != root_id and row.get("sha256") == digest for row in old_rows):
                base.update(status="cross_root_duplicate_candidate", needs_reanalysis="yes", reason="same_hash_exists_in_another_root_new_identity_required")
            else:
                base.update(status="added", needs_reanalysis="yes", reason="not_in_committed_ledger")
        else:
            base.update(status="unreadable", reason="new_file_unreadable")
        rows.append(base)

    for old in old_rows:
        if old.get("root_id") != root_id:
            continue
        key = old.get("source_key") or source_key(root_id, old.get("relative_path", ""))
        if key not in current_keys and key not in used_move_keys and old.get("status") != "missing":
            rows.append(
                {
                    "root_id": root_id,
                    "scan_id": receipt["scan_id"],
                    "source_id": old.get("source_id", ""),
                    "candidate_source_id": "",
                    "source_key": key,
                    "relative_path": old.get("relative_path", ""),
                    "sha256": old.get("sha256", ""),
                    "status": "missing",
                    "needs_reanalysis": "no",
                    "migration_from_key": "",
                    "reason": "not_in_complete_scan",
                }
            )
    return sorted(rows, key=lambda row: (str(row["status"]), str(row["relative_path"])))


def load_diff_bundle(
    project: Path,
    scan_id: str,
    ledger_relative: str = "02_素材账/source-ledger.csv",
) -> tuple[dict, list[dict[str, str]], dict, list[dict[str, str]], list[dict[str, str]]]:
    receipt, inventory, hashes = load_scan_bundle(project, scan_id)
    staging = scan_dir(project, scan_id)
    diff_path = assert_project_input(project, staging / "diff.csv", ["02_素材账/scan-runs"])
    diff_receipt_path = assert_project_input(project, staging / "diff-receipt.json", ["02_素材账/scan-runs"])
    try:
        diff_receipt = json.loads(diff_receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid diff receipt: {exc}")
    errors: list[str] = []
    if diff_receipt.get("schema_version") != "2.0" or diff_receipt.get("scan_id") != scan_id:
        errors.append("diff receipt identity mismatch")
    if diff_receipt.get("root_id") != receipt.get("root_id"):
        errors.append("diff root_id mismatch")
    if diff_receipt.get("scan_receipt_sha256") != file_sha256(staging / "receipt.json"):
        errors.append("scan receipt changed after diff")
    if diff_receipt.get("diff_sha256") != file_sha256(diff_path):
        errors.append("diff file hash mismatch")
    if diff_receipt.get("ledger_before_sha256") != ledger_sha256(project, ledger_relative):
        errors.append("committed ledger changed after diff; rerun DIFF")
    if read_header(diff_path) != DIFF_FIELDS:
        errors.append("diff header mismatch")
    diff_rows = read_csv(diff_path, required=True)
    if len(diff_rows) != int(diff_receipt.get("row_count", -1)):
        errors.append("diff row_count mismatch")
    allowed_statuses = {"added", "modified", "unreadable", "unchanged", "missing", "move_candidate", "cross_root_duplicate_candidate"}
    for row in diff_rows:
        if row.get("root_id") != receipt.get("root_id") or row.get("scan_id") != scan_id:
            errors.append(f"diff row identity mismatch: {row.get('relative_path')}")
        if row.get("status") not in allowed_statuses:
            errors.append(f"invalid diff status: {row.get('status')}")
    if errors:
        fail("invalid diff transaction:\n- " + "\n- ".join(errors), code=1)
    return receipt, inventory, diff_receipt, diff_rows, hashes
