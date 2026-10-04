#!/usr/bin/env python3
"""Close or classify an interrupted prepared source-ledger commit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    assert_project_root,
    create_json_exclusive,
    fail,
    file_sha256,
    iso_now,
    project_file_lock,
    safe_project_path,
)
from source_transaction import scan_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("scan_id")
    parser.add_argument("--ledger", default="02_素材账/source-ledger.csv")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    staging = scan_dir(project, args.scan_id)

    with project_file_lock(project, "source-ledger"):
        pending = []
        for path in sorted(staging.glob("prepare-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if not (staging / f"commit-{data.get('commit_id', '')}.json").exists() and not (staging / f"abort-{data.get('commit_id', '')}.json").exists():
                pending.append((path, data))
        if len(pending) != 1:
            fail(f"expected exactly one unresolved prepared commit, found {len(pending)}")
        _, prepared = pending[0]
        ledger = safe_project_path(project, args.ledger, must_exist=True)
        current_sha256 = file_sha256(ledger)
        commit_id = prepared["commit_id"]
        if current_sha256 == prepared.get("ledger_after_sha256"):
            record = {**prepared, "state": "committed_recovered", "recovered_at": iso_now()}
            create_json_exclusive(staging / f"commit-{commit_id}.json", record, project)
            print(f"recovered committed source ledger: {commit_id}")
            return
        if current_sha256 == prepared.get("ledger_before_sha256"):
            record = {**prepared, "state": "aborted_before_write", "recovered_at": iso_now()}
            create_json_exclusive(staging / f"abort-{commit_id}.json", record, project)
            print(f"recorded safely aborted source commit: {commit_id}")
            return
        fail("ledger matches neither prepared pre-image nor post-image; manual recovery required")


if __name__ == "__main__":
    main()
