#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_tapd_records.py
拉取员工在 tapd 上的需求/缺陷/任务记录（仅司龄 ≥ 0.5y 调用）

调用：
    python fetch_tapd_records.py --rtx <your-rtx> --since 2022-03-15 [--limit 20]

依赖：
    - tapd MCP（connector:tapd 或 connector:tapd-woa）

输出：
    raw/tapd.json
"""
import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

TAPD_MCP_URL = os.environ.get("TAPD_MCP_URL", "")  # 走 connector，无需直连


def call_tapd_mcp(rtx: str, since: str, limit: int = 20) -> dict:
    """
    调用 tapd MCP，拉取该 RTX 在 since 之后参与的 story/bug/task。

    返回 schema：
    {
        "items": [
            {
                "id": "STORY-12345",
                "title": "...",
                "type": "story" | "bug" | "task",
                "project": "...",
                "status": "...",
                "modified_at": "...",
                "role": "owner" | "participant",
                "labels": ["推荐", "排序"]
            }
        ],
        "stat": {
            "n_total": 30,
            "by_type": { "story": 20, "bug": 8, "task": 2 },
            "top_projects": [ { "project": "Recommendation", "count": 18 } ],
            "top_labels": [ { "label": "推荐", "count": 12 } ]
        }
    }
    """
    raise NotImplementedError(
        "首版未联调 tapd MCP。建议在 codebuddy 配置 connector:tapd（或 tapd-woa）后调用："
        "tapd.search_user_works({rtx, since, limit})。可临时用 --mock 走样例。"
    )


def load_mock(mock_path: str) -> dict:
    p = Path(mock_path) if mock_path else None
    if p is None or not p.exists() or p.is_dir():
        items = [
            {"id": "STORY-12345", "title": "新增多目标排序", "type": "story",
             "project": "Recommendation", "status": "已发布", "modified_at": "2025-04-10",
             "role": "owner", "labels": ["推荐", "排序"]},
            {"id": "STORY-12346", "title": "向量召回引擎升级", "type": "story",
             "project": "Recommendation", "status": "进行中", "modified_at": "2025-05-22",
             "role": "owner", "labels": ["推荐", "向量召回"]},
            {"id": "BUG-9988", "title": "线上排序结果偶发 NaN", "type": "bug",
             "project": "Recommendation", "status": "已解决", "modified_at": "2025-03-18",
             "role": "owner", "labels": ["排序"]},
        ]
        return _add_stat(items)
    with p.open("r", encoding="utf-8") as f:
        items = json.load(f)
    return _add_stat(items)


def _add_stat(items: list) -> dict:
    by_type = Counter(it["type"] for it in items)
    top_proj = Counter(it.get("project", "") for it in items).most_common(5)
    label_flat = [lab for it in items for lab in it.get("labels", [])]
    top_label = Counter(label_flat).most_common(10)
    return {
        "items": items,
        "stat": {
            "n_total": len(items),
            "by_type": dict(by_type),
            "top_projects": [{"project": p, "count": c} for p, c in top_proj if p],
            "top_labels": [{"label": l, "count": c} for l, c in top_label],
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Fetch tapd records for a user")
    ap.add_argument("--rtx", required=True)
    ap.add_argument("--since", required=True, help="hire_date or any YYYY-MM-DD")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--staff-id", default="", help="若提供则用作输出目录")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-file", default="")
    args = ap.parse_args()

    if not args.out:
        sid = args.staff_id or args.rtx
        base = Path.home() / "Desktop" / "codebuddy" / "职业经纪人" / sid / "raw"
        base.mkdir(parents=True, exist_ok=True)
        args.out = str(base / "tapd.json")

    if args.mock:
        print("[INFO] 走 mock 模式", file=sys.stderr)
        data = load_mock(args.mock_file)
    else:
        try:
            data = call_tapd_mcp(args.rtx, args.since, args.limit)
        except NotImplementedError as e:
            print(f"[WARN] {e}", file=sys.stderr)
            sys.exit(2)

    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "out": args.out,
        "n_total": data["stat"]["n_total"],
        "top_projects": data["stat"]["top_projects"][:3],
        "top_labels": data["stat"]["top_labels"][:5],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
