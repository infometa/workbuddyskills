#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_gongfeng_records.py
拉取员工在工蜂（git.woa.com）的代码仓库 / 语言 / 提交频率（仅司龄 ≥ 0.5y 调用）

调用：
    python fetch_gongfeng_records.py --rtx <your-rtx> --since 2022-03-15 [--limit 10]

依赖：
    - 工蜂 MCP（connector:gongfeng-woa 或独立 gongfeng-mcp）

输出：
    raw/gongfeng.json
"""
import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

GONGFENG_MCP_URL = os.environ.get("GONGFENG_MCP_URL", "")


def call_gongfeng_mcp(rtx: str, since: str, limit: int = 10) -> dict:
    """
    调用 gongfeng MCP（list_user_repos）

    返回 schema：
    {
        "repos": [
            {
                "repo_url": "https://git.woa.com/group/proj",
                "name": "proj",
                "role": "owner" | "maintainer" | "developer",
                "languages": ["Go", "Python"],
                "commit_count": 156,
                "last_commit_at": "2026-05-30",
                "is_archived": false
            }
        ],
        "stat": {
            "n_repos": 8,
            "n_active_repos": 6,
            "languages_top3": ["Python", "Go", "TypeScript"],
            "total_commits": 612
        }
    }
    """
    raise NotImplementedError(
        "首版未联调工蜂 MCP。建议接 connector:gongfeng-woa 后调用 gongfeng.list_user_repos。"
        "临时使用 --mock。"
    )


def load_mock(mock_path: str) -> dict:
    p = Path(mock_path) if mock_path else None
    if p is None or not p.exists() or p.is_dir():
        repos = [
            {
                "repo_url": "https://git.woa.com/teg-ailab/rec-rank",
                "name": "rec-rank",
                "role": "owner",
                "languages": ["Python", "Go"],
                "commit_count": 156,
                "last_commit_at": "2026-05-30",
                "is_archived": False,
            },
            {
                "repo_url": "https://git.woa.com/teg-ailab/feature-store",
                "name": "feature-store",
                "role": "developer",
                "languages": ["Go"],
                "commit_count": 88,
                "last_commit_at": "2026-04-21",
                "is_archived": False,
            },
            {
                "repo_url": "https://git.woa.com/teg-ailab/exp-toolkit",
                "name": "exp-toolkit",
                "role": "owner",
                "languages": ["Python", "TypeScript"],
                "commit_count": 42,
                "last_commit_at": "2025-11-12",
                "is_archived": False,
            },
        ]
        return _add_stat(repos)
    with p.open("r", encoding="utf-8") as f:
        repos = json.load(f)
    return _add_stat(repos)


def _add_stat(repos: list) -> dict:
    lang_flat = [l for r in repos for l in r.get("languages", [])]
    lang_top = [l for l, _ in Counter(lang_flat).most_common(3)]
    return {
        "repos": repos,
        "stat": {
            "n_repos": len(repos),
            "n_active_repos": sum(1 for r in repos if not r.get("is_archived")),
            "languages_top3": lang_top,
            "total_commits": sum(r.get("commit_count", 0) for r in repos),
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Fetch gongfeng records for a user")
    ap.add_argument("--rtx", required=True)
    ap.add_argument("--since", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--staff-id", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-file", default="")
    args = ap.parse_args()

    if not args.out:
        sid = args.staff_id or args.rtx
        base = Path.home() / "Desktop" / "codebuddy" / "职业经纪人" / sid / "raw"
        base.mkdir(parents=True, exist_ok=True)
        args.out = str(base / "gongfeng.json")

    if args.mock:
        print("[INFO] 走 mock 模式", file=sys.stderr)
        data = load_mock(args.mock_file)
    else:
        try:
            data = call_gongfeng_mcp(args.rtx, args.since, args.limit)
        except NotImplementedError as e:
            print(f"[WARN] {e}", file=sys.stderr)
            sys.exit(2)

    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "out": args.out,
        "n_repos": data["stat"]["n_repos"],
        "languages_top3": data["stat"]["languages_top3"],
        "total_commits": data["stat"]["total_commits"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
