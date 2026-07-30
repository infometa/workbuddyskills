#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deep_read.py · 对去重排序后的 Top N 笔记执行深读：
  - Top max_full 篇 → xhs read <id> 拿全文
  - Top max_comments 篇 → xhs comments <id> --all 拿评论池
"""
import json, subprocess, time


def _xhs_read(note_id: str) -> dict:
    try:
        r = subprocess.run(
            ["xhs", "read", note_id, "--json"],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return {}
        return json.loads(r.stdout) if r.stdout else {}
    except Exception:
        return {}


def _xhs_comments(note_id: str) -> list:
    try:
        r = subprocess.run(
            ["xhs", "comments", note_id, "--all", "--json"],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            return []
        d = json.loads(r.stdout) if r.stdout else {}
        if isinstance(d, dict):
            data = d.get("data", d)
            return data.get("comments") or data.get("items") or []
        return d if isinstance(d, list) else []
    except Exception:
        return []


def deep_read(ranked: list, max_full: int = 30, max_comments: int = 5) -> list:
    """对 ranked Top N 调 xhs read / comments 拿深度内容"""
    out = []
    for i, note in enumerate(ranked[:max_full]):
        nid = note.get("note_id") or note.get("id")
        if not nid:
            out.append(note)
            continue
        full = _xhs_read(nid)
        if full:
            note["full_content"] = full.get("desc") or full.get("content") or full.get("data", {}).get("desc")
        if i < max_comments:
            comments = _xhs_comments(nid)
            note["comments_sample"] = comments[:50]   # 截断 50 条避免过大
        out.append(note)
        # 礼让 xhs CLI 自带延迟
        time.sleep(0.2)
    return out


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--max-full", type=int, default=30)
    ap.add_argument("--max-comments", type=int, default=5)
    a = ap.parse_args()
    ranked = json.load(open(a.input, encoding="utf-8"))
    out = deep_read(ranked, a.max_full, a.max_comments)
    print(json.dumps(out, ensure_ascii=False, indent=2))
