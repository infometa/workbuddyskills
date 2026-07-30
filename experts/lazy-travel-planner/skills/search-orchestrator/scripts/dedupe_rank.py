#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedupe_rank.py · 把 xhs_batch_search 的多源 raw 结果去重 + 排序
关键字段：note_id（去重）、likes / comments / collected_count（排序）
"""
import json, math


def _note_id(note: dict) -> str:
    return (note.get("note_id") or note.get("id") or note.get("display_title") or
            note.get("title") or "")[:64]


def _score(note: dict) -> float:
    likes = float(note.get("likes") or note.get("liked_count") or note.get("interact_info", {}).get("liked_count") or 0)
    comments = float(note.get("comments") or note.get("comment_count") or note.get("interact_info", {}).get("comment_count") or 0)
    collected = float(note.get("collected_count") or note.get("interact_info", {}).get("collected_count") or 0)
    # log 归一化避免单条爆款主导
    return math.log10(likes + comments * 1.5 + collected + 1)


def dedupe_and_rank(raw_results: list) -> list:
    """
    raw_results: [{ok, query, notes:[...]}, ...]
    返回 [note, ...]，去重后按 score 降序
    """
    pool = {}
    for r in raw_results:
        if not r.get("ok"):
            continue
        q = r.get("query", "")
        for note in r.get("notes") or []:
            nid = _note_id(note)
            if not nid:
                continue
            if nid in pool:
                pool[nid]["matched_queries"].append(q)
                continue
            note["matched_queries"] = [q]
            note["_score"] = _score(note)
            pool[nid] = note

    # 多查询命中加权（被多个查询命中说明高度相关）
    for nid, n in pool.items():
        n["_score"] += 0.3 * (len(n["matched_queries"]) - 1)

    return sorted(pool.values(), key=lambda x: x["_score"], reverse=True)


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    a = ap.parse_args()
    raw = json.load(open(a.input, encoding="utf-8"))
    out = dedupe_and_rank(raw)
    print(json.dumps(out, ensure_ascii=False, indent=2))
