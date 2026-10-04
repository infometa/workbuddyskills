#!/usr/bin/env python3
"""Export a CSV manifest for the already frozen delivery selection only."""
from __future__ import annotations

import argparse
import json

from common import assert_project_input, assert_project_root, file_sha256, safe_project_path, write_csv

FIELDS = ["relative_path", "size_bytes", "sha256", "status"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--selection", default="13_导出成果/delivery-selection.json")
    parser.add_argument("--output", default="13_导出成果/交付清单.csv")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    selection_path = assert_project_input(project, args.selection, ["13_导出成果"])
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    rows = []
    for item in selection.get("outputs", []):
        path = assert_project_input(project, item.get("path", ""), ["08_故事卡", "10_大纲与章节", "13_导出成果"])
        digest = file_sha256(path)
        if digest != item.get("sha256"):
            raise SystemExit(f"selected output changed: {item.get('path')}")
        rows.append({"relative_path": path.relative_to(project).as_posix(), "size_bytes": str(path.stat().st_size), "sha256": digest, "status": "selected"})
    if not rows:
        raise SystemExit("delivery selection contains no outputs")
    output = safe_project_path(project, args.output)
    write_csv(output, FIELDS, rows, project_root=project)
    print(f"manifested {len(rows)} selected outputs -> {output}")


if __name__ == "__main__":
    main()
