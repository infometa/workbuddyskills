#!/usr/bin/env python3
"""
Batch saver for listing-title-writer.

Usage:
  python scripts/save_title_batch_output.py batch-title-output.json
  python scripts/save_title_batch_output.py batch-title-output.json --source-file input.xlsx
  python scripts/save_title_batch_output.py batch-title-output.json --no-xlsx

默认除 JSON 外还导出一份可批量查看的 Excel（标题 / Highlights / 字符数 /
改写逻辑 / 埋词点 / 信息去向 / 校验说明），无需再逐条复制。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from listing_spec import extract_spec_arg  # type: ignore
from save_title_output import (
    _validate,
    apply_spec_to_policy,
    attach_xlsx_artifact,
    build_workbench_payload,
)

SLUG = "linkfox-listing-title-writer-batch"


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("rows") or payload.get("items") or payload.get("results")
    else:
        rows = None
    if not isinstance(rows, list):
        raise ValueError("batch payload must be a list or an object with rows/items/results")
    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"row {idx} must be an object")
        normalized.append(dict(row))
    return normalized


def _save_json_payload(payload: Any, summary_lines: list[str]) -> tuple[str, int]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from linkfox_save import save_json_payload  # type: ignore

    return save_json_payload(SLUG, payload, summary_lines=summary_lines)


def resolve_target_rows(rows: list[dict[str, Any]]) -> list[int]:
    """算出每行写回原表的目标行号（表头占第 1 行）。

    兼容两种调用约定：
      - `source_row` 显式给出工作表行号，最高优先级
      - `row_index` 若整批构成连续 1..N，按「第 N 条数据」解释 → 目标 N+1
        否则按工作表行号解释（≥2 直接用，1 视作 2），与历史行为一致
    """
    indices = [row.get("row_index") for row in rows]
    provided = [int(i) for i in indices if isinstance(i, int) and not isinstance(i, bool)]
    one_based_batch = len(provided) == len(rows) and sorted(provided) == list(range(1, len(rows) + 1))

    targets: list[int] = []
    for position, row in enumerate(rows, start=1):
        explicit = row.get("source_row")
        if isinstance(explicit, int) and not isinstance(explicit, bool) and explicit >= 2:
            targets.append(explicit)
            continue
        raw = row.get("row_index")
        if not isinstance(raw, int) or isinstance(raw, bool):
            targets.append(position + 1)
            continue
        targets.append(raw + 1 if one_based_batch or raw < 2 else raw)
    return targets


def find_target_collisions(targets: list[int]) -> dict[int, list[int]]:
    """返回目标工作表行号到输入位置（1-based）的冲突映射。"""
    positions: dict[int, list[int]] = {}
    for position, target in enumerate(targets, start=1):
        positions.setdefault(target, []).append(position)
    return {target: items for target, items in positions.items() if len(items) > 1}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Batch JSON containing rows[]")
    parser.add_argument("--source-file", help="可选原表（.xlsx/.csv/.tsv）：保留原始列并在右侧追加结果")
    parser.add_argument("--source-xlsx", help="--source-file 的旧别名")
    parser.add_argument("--output-xlsx", help="可选输出 .xlsx 路径；默认写入会话 reports 目录")
    parser.add_argument("--no-xlsx", action="store_true", help="只落 JSON，不导出 Excel")
    argv, spec = extract_spec_arg(sys.argv[1:])
    args = parser.parse_args(argv)

    payload = _load_json(args.json_file)
    rows = _rows_from_payload(payload)
    ok_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []

    targets = resolve_target_rows(rows)
    collisions = find_target_collisions(targets)
    for position, row in enumerate(rows, start=1):
        row.setdefault("row_index", position)
        apply_spec_to_policy(row, spec)
        errors, warnings = _validate(row, spec)
        target = targets[position - 1]
        if target in collisions:
            errors.append(
                f"duplicate worksheet row target: {target}"
                f"（输入位置 {', '.join(str(item) for item in collisions[target])} 冲突）"
            )
            # 冲突组全部禁止写回，避免 failed 行覆盖先前的正确结果。
            row["target_row"] = target
            row["writeback_blocked"] = True
        else:
            row["target_row"] = target
        row["warnings"] = [*row.get("warnings", []), *warnings] if isinstance(row.get("warnings"), list) else warnings
        if errors:
            row["status"] = "failed"
            row["errors"] = errors
            failed_rows.append(row)
        else:
            row["status"] = row.get("status") or "ok"
            ok_rows.append(row)

    validated_rows = [
        (row, list(row.get("errors") or []), list(row.get("warnings") or []))
        for row in rows
    ]
    batch_payload = build_workbench_payload(
        validated_rows,
        source_file=os.path.abspath(args.json_file),
    )

    source_file: str | None = args.source_file or args.source_xlsx
    if source_file:
        source_path = Path(source_file).expanduser().resolve()
        if not source_path.exists():
            print(f"source file not found: {source_path}", file=sys.stderr)
            sys.exit(3)
        source_file = str(source_path)

    xlsx_path = (
        None
        if args.no_xlsx
        else attach_xlsx_artifact(
            batch_payload,
            source_file=source_file,
            out=args.output_xlsx,
            strict=True,
        )
    )

    summary = [
        "已批量落盘 Title + Item Highlights。",
        f"  rows: {len(rows)}",
        f"  ok: {len(ok_rows)}",
        f"  failed: {len(failed_rows)}",
    ]
    if xlsx_path:
        summary.append(f"  xlsx: {xlsx_path}")
    json_path, _ = _save_json_payload(batch_payload, summary)

    if xlsx_path:
        print(f"XLSX artifact: {xlsx_path}")

    if failed_rows:
        print(f"部分行校验失败，详情见: {json_path}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
