#!/usr/bin/env python3
"""Compare an integrity-bound SCAN with the committed source ledger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    assert_project_root,
    fail,
    file_sha256,
    iso_now,
    project_file_lock,
    read_csv,
    safe_project_path,
    write_csv,
    write_json_atomic,
)
from source_transaction import (
    DIFF_FIELDS,
    compute_diff_rows,
    latest_scan_id,
    ledger_sha256,
    load_scan_bundle,
    scan_dir,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--scan-id", default="")
    parser.add_argument("--ledger", default="02_素材账/source-ledger.csv")
    parser.add_argument("--output", default="02_素材账/来源差异.csv")
    args = parser.parse_args()

    project = assert_project_root(args.project_dir)
    scan_id = args.scan_id or latest_scan_id(project)
    receipt, inventory, hashes = load_scan_bundle(project, scan_id)
    if receipt.get("status") != "complete":
        fail(f"DIFF requires a complete scan; got {receipt.get('status')}")

    staging = scan_dir(project, scan_id)
    if list(staging.glob("commit-*.json")):
        fail("this scan is already committed and cannot be rediffed")
    ledger_path = safe_project_path(project, args.ledger, must_exist=True)

    with project_file_lock(project, "source-ledger"):
        before_sha256 = ledger_sha256(project, args.ledger)
        old_rows = read_csv(ledger_path, required=True)
        diff_rows = compute_diff_rows(receipt, inventory, hashes, old_rows)
        diff_path = safe_project_path(project, staging / "diff.csv")
        write_csv(diff_path, DIFF_FIELDS, diff_rows, project_root=project)
        diff_sha256 = file_sha256(diff_path)
        counts = {
            status: sum(row["status"] == status for row in diff_rows)
            for status in sorted({str(row["status"]) for row in diff_rows})
        }
        diff_receipt = {
            "schema_version": "2.0",
            "scan_id": scan_id,
            "root_id": receipt["root_id"],
            "generated_at": iso_now(),
            "scan_receipt_sha256": file_sha256(staging / "receipt.json"),
            "ledger_before_sha256": before_sha256,
            "diff_sha256": diff_sha256,
            "row_count": len(diff_rows),
            "counts": counts,
            "review_required": True,
            "commit_argument": f"--approve-diff-sha256 {diff_sha256}",
        }
        write_json_atomic(staging / "diff-receipt.json", diff_receipt, project_root=project)
        mirror_path = safe_project_path(project, args.output)
        write_csv(mirror_path, DIFF_FIELDS, diff_rows, project_root=project)

    print(f"source diff staged: {scan_id} {json.dumps(counts, ensure_ascii=False)}")
    print(f"review digest: {diff_sha256}")
    print(f"review file: {mirror_path}")


if __name__ == "__main__":
    main()
