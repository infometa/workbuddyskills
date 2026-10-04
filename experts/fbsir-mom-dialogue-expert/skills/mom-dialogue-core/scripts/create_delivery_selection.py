#!/usr/bin/env python3
"""Freeze explicit output files and referenced objects for a permission gate."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import (
    assert_project_input,
    assert_project_root,
    fail,
    file_sha256,
    iso_now,
    new_id,
    safe_project_path,
    write_json_atomic,
)

PATTERNS = {
    "source_ids": re.compile(r"\bSRC-[A-Z0-9]{12,64}\b"),
    "story_ids": re.compile(r"\bSTY-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
    "answer_ids": re.compile(r"\bANS-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
    "person_ids": re.compile(r"\bPER-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--scope", choices=["manuscript", "public"], required=True)
    parser.add_argument("--output", action="append", required=True, help="Project-relative output file")
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--story-id", action="append", default=[])
    parser.add_argument("--answer-id", action="append", default=[])
    parser.add_argument("--person-id", action="append", default=[])
    parser.add_argument("--anonymized-object-id", action="append", default=[])
    parser.add_argument("--sensitive-reviewed-object-id", action="append", default=[])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    identifiers = {
        "source_ids": set(args.source_id),
        "story_ids": set(args.story_id),
        "answer_ids": set(args.answer_id),
        "person_ids": set(args.person_id),
    }
    outputs = []
    allowed_roots = ["08_故事卡", "10_大纲与章节", "13_导出成果"]
    for value in args.output:
        path = assert_project_input(project, value, allowed_relative_dirs=allowed_roots)
        relative = path.relative_to(project).as_posix()
        if relative == "13_导出成果/delivery-selection.json":
            fail("delivery selection cannot select itself")
        outputs.append({"path": relative, "sha256": file_sha256(path)})
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            text = ""
        for field, pattern in PATTERNS.items():
            identifiers[field].update(pattern.findall(text))
    selection = {
        "schema_version": "2.0",
        "selection_id": new_id("DEL"),
        "scope": args.scope,
        "created_at": iso_now(),
        "outputs": sorted(outputs, key=lambda item: item["path"]),
        "source_ids": sorted(identifiers["source_ids"]),
        "story_ids": sorted(identifiers["story_ids"]),
        "answer_ids": sorted(identifiers["answer_ids"]),
        "person_ids": sorted(identifiers["person_ids"]),
        "anonymized_object_ids": sorted(set(args.anonymized_object_id)),
        "sensitive_reviewed_object_ids": sorted(set(args.sensitive_reviewed_object_id)),
        "notes": args.notes,
    }
    output_path = safe_project_path(project, "13_导出成果/delivery-selection.json")
    write_json_atomic(output_path, selection, project_root=project)
    print(f"delivery selection: {selection['selection_id']} -> {output_path}")


if __name__ == "__main__":
    main()
