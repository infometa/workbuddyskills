#!/usr/bin/env python3
"""Write one validated, collision-safe project checkpoint."""
from __future__ import annotations

import argparse
import json
import re

from common import (
    assert_project_root,
    fail,
    iso_now,
    json_arg,
    new_id,
    project_file_lock,
    read_csv,
    safe_project_dir,
    safe_project_path,
    write_json_atomic,
    write_text_atomic,
)
from project_status import update_project_status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--status", choices=["initialized", "in_progress", "blocked", "ready_for_review", "complete"], default="in_progress")
    parser.add_argument("--note", default="")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--processed-source-id", action="append", default=[])
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--pending-item", action="append", default=[])
    parser.add_argument("--locked-chapter", action="append", default=[])
    parser.add_argument("--model-capabilities", default="{}")
    parser.add_argument("--parameters", default="{}")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    source_ids = {row.get("source_id", "") for row in read_csv(safe_project_path(project, "02_素材账/source-ledger.csv"), required=True)}
    chapter_ids = {row.get("chapter_id", "") for row in read_csv(safe_project_path(project, "10_大纲与章节/chapter-ledger.csv"), required=True)}
    unknown_sources = sorted(set(args.processed_source_id) - source_ids)
    unknown_chapters = sorted(set(args.locked_chapter) - chapter_ids)
    if unknown_sources:
        fail(f"checkpoint references unknown sources: {unknown_sources}")
    if unknown_chapters:
        fail(f"checkpoint references unknown chapters: {unknown_chapters}")
    outputs = []
    for value in args.output:
        path = safe_project_path(project, value, must_exist=True)
        if not path.is_file():
            fail(f"checkpoint output is not a file: {value}")
        outputs.append(path.relative_to(project).as_posix())
    model_capabilities = json_arg(args.model_capabilities, {})
    parameters = json_arg(args.parameters, {})
    if not isinstance(model_capabilities, dict) or not isinstance(parameters, dict):
        fail("model capabilities and parameters must be JSON objects")
    batch_id = args.batch_id or new_id("BATCH")
    if not re.fullmatch(r"BATCH-[A-Z0-9_-]+", batch_id):
        fail(f"invalid batch id: {batch_id}")
    checkpoint_id = f"CPK-{new_id('RUN').split('-', 1)[1]}"
    record = {
        "schema_version": "2.0",
        "checkpoint_id": checkpoint_id,
        "created_at": iso_now(),
        "status": args.status,
        "batch_id": batch_id,
        "processed_source_ids": sorted(set(args.processed_source_id)),
        "outputs": sorted(set(outputs)),
        "pending_items": args.pending_item,
        "locked_chapters": sorted(set(args.locked_chapter)),
        "model_capabilities": model_capabilities,
        "processing_parameters": parameters,
        "note": args.note,
    }
    with project_file_lock(project, "checkpoint"):
        target = safe_project_dir(project, "12_版本与检查点") / f"{checkpoint_id}.json"
        write_json_atomic(target, record, project_root=project)
        capsule = (
            "# 续接胶囊\n\n"
            + f"最近检查点：{checkpoint_id}\n"
            + f"当前批次：{batch_id}\n"
            + f"状态：{args.status}\n"
            + f"已处理来源：{', '.join(record['processed_source_ids']) or '无'}\n"
            + f"待处理：{', '.join(record['pending_items']) or '无'}\n"
            + f"已锁定章节：{', '.join(record['locked_chapters']) or '无'}\n"
            + f"备注：{args.note}\n"
        )
        write_text_atomic(safe_project_path(project, "00_项目看板/续接胶囊.md"), capsule, project_root=project)
        update_project_status(project, args.status, args.note)
    print(f"checkpoint: {checkpoint_id}")


if __name__ == "__main__":
    main()
