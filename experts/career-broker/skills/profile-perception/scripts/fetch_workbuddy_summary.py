#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_workbuddy_summary.py
拉取员工在 workbuddy 上的工作内容总结（增量补充，可选）

调用：
    python fetch_workbuddy_summary.py --rtx <your-rtx> --since 2022-03-15

输出：
    raw/workbuddy.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

WORKBUDDY_TOKEN = os.environ.get("WORKBUDDY_TOKEN", "")


def call_workbuddy_mcp(rtx: str, since: str) -> dict:
    """
    返回 schema：
    {
        "summary_md": "<人话工作总结>",
        "key_outcomes": ["XX 项目落地", "..."],
        "period": { "since": "2022-03-15", "until": "2026-06-02" }
    }
    """
    raise NotImplementedError("首版未联调 workbuddy MCP，可静默跳过。")


def load_mock(mock_path: str) -> dict:
    p = Path(mock_path) if mock_path else None
    if p is None or not p.exists() or p.is_dir():
        return {
            "summary_md": "近 1 年主要在做推荐系统排序模型升级，从 MMoE 升级到 PLE，重构线上特征流。",
            "key_outcomes": [
                "线上 CTR 提升 3.2%",
                "推动向量召回引擎从 0-1 上线",
                "组内分享 5 次",
            ],
            "period": {"since": "2022-03-15", "until": "2026-06-02"},
        }
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtx", required=True)
    ap.add_argument("--since", required=True)
    ap.add_argument("--staff-id", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-file", default="")
    ap.add_argument("--silent-on-fail", action="store_true",
                    help="未授权或失败时静默退出（exit 0），不阻断主流程")
    args = ap.parse_args()

    if not args.out:
        sid = args.staff_id or args.rtx
        base = Path.home() / "Desktop" / "codebuddy" / "职业经纪人" / sid / "raw"
        base.mkdir(parents=True, exist_ok=True)
        args.out = str(base / "workbuddy.json")

    if args.mock or not WORKBUDDY_TOKEN:
        if not args.mock and args.silent_on_fail:
            print("[INFO] WORKBUDDY_TOKEN 缺失，静默跳过", file=sys.stderr)
            sys.exit(0)
        print("[INFO] 走 mock 模式", file=sys.stderr)
        data = load_mock(args.mock_file)
    else:
        try:
            data = call_workbuddy_mcp(args.rtx, args.since)
        except NotImplementedError as e:
            if args.silent_on_fail:
                print(f"[INFO] {e}（已静默）", file=sys.stderr)
                sys.exit(0)
            print(f"[WARN] {e}", file=sys.stderr)
            sys.exit(2)

    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": args.out, "n_outcomes": len(data.get("key_outcomes", []))},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
