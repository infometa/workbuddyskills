#!/usr/bin/env python3
"""Report exact-hash duplicate candidates from the committed source ledger."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

from common import assert_project_root, read_csv, safe_project_path, schema_fields, schema_path, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--output", default="02_素材账/重复候选.csv")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    ledger = safe_project_path(project, "02_素材账/source-ledger.csv", must_exist=True)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(ledger, required=True):
        if row.get("sha256") and row.get("status") not in {"missing", "unreadable"}:
            groups[row["sha256"]].append(row)
    output_rows = []
    for digest, items in sorted(groups.items()):
        if len(items) < 2:
            continue
        output_rows.append(
            {
                "sha256": digest,
                "duplicate_count": str(len(items)),
                "paths": json.dumps(sorted(row["source_key"] for row in items), ensure_ascii=False),
                "source_ids": json.dumps(sorted(row["source_id"] for row in items), ensure_ascii=False),
                "status": "candidate",
            }
        )
    output = safe_project_path(project, args.output)
    fields = schema_fields(schema_path("duplicate-candidate.schema.json"))
    write_csv(output, fields, output_rows, project_root=project)
    print(f"duplicate groups: {len(output_rows)} -> {output}")


if __name__ == "__main__":
    main()
