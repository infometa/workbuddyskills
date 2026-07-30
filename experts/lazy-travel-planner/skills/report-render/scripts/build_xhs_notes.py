#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_xhs_notes.py · 把 search-orchestrator 的 evidence 转成 HTML 模板需要的"按主题分组"结构

输入：00 编排底座输出的 candidates.json（含 evidence 字段）
输出：
[
  {
    "theme": "目的地总览",
    "notes": [
      { "title": "...", "url": "https://www.xiaohongshu.com/discovery/item/<id>",
        "cover": "https://...", "author": "...", "likes": 1234, "comments": 89,
        "snippet": "...", "sentiment": "positive|negative|neutral" }
    ]
  },
  ...
]
"""
import argparse, json, pathlib, re

THEMES = [
    ("避雷防坑", ["避雷", "被坑", "踩雷", "不推荐", "智商税"]),
    ("美食推荐", ["美食", "好吃", "餐厅", "店", "苍蝇馆子", "本地人"]),
    ("住宿体验", ["酒店", "民宿", "住", "房"]),
    ("景点攻略", ["攻略", "必去", "景点", "玩"]),
    ("拍照机位", ["拍照", "机位", "出片", "氛围"]),
]

POSITIVE_KW = ["好吃", "推荐", "值得", "惊艳", "舒服", "干净", "氛围好", "性价比", "必去"]
NEGATIVE_KW = ["踩雷", "不值", "排队", "贵", "脏", "服务差", "拥挤", "智商税", "避雷", "坑"]


def detect_theme(text: str) -> str:
    for theme, kw in THEMES:
        for k in kw:
            if k in text:
                return theme
    return "其他参考"


def detect_sentiment(text: str) -> str:
    pos = sum(1 for k in POSITIVE_KW if k in text)
    neg = sum(1 for k in NEGATIVE_KW if k in text)
    if neg > pos and neg >= 2:
        return "negative"
    if pos > neg and pos >= 2:
        return "positive"
    return "neutral"


def extract_raw_notes(data) -> list:
    """兼容编排输出、xhs CLI 原始输出、WebSearch 兜底输出等多种结构。"""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    for key in ("evidence", "raw_notes", "notes", "items", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return value

    nested = []
    for key in ("groups", "themes"):
        value = data.get(key)
        if isinstance(value, list):
            for group in value:
                if isinstance(group, dict):
                    nested.extend(group.get("notes") or group.get("items") or [])
            if nested:
                return nested

    for value in data.values():
        if isinstance(value, dict):
            nested.extend(extract_raw_notes(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nested.extend(extract_raw_notes(item))
    return nested


def normalize_note(raw: dict) -> dict:
    """把 xhs CLI 不同来源的字段拍平为统一结构"""
    nid = raw.get("note_id") or raw.get("id") or raw.get("noteId") or ""
    interact = raw.get("interact_info") or {}
    title = (raw.get("display_title") or raw.get("title")
             or raw.get("name") or raw.get("desc") or raw.get("snippet") or "")[:60]
    desc = (raw.get("full_content") or raw.get("desc") or raw.get("content")
            or raw.get("snippet") or raw.get("summary") or "")
    cover = ""
    if isinstance(raw.get("cover"), dict):
        cover = raw["cover"].get("url_default") or raw["cover"].get("url") or ""
    elif isinstance(raw.get("cover"), str):
        cover = raw["cover"]
    elif isinstance(raw.get("images_list"), list) and raw["images_list"]:
        first = raw["images_list"][0]
        if isinstance(first, dict):
            cover = first.get("url") or ""
        elif isinstance(first, str):
            cover = first

    likes = (raw.get("liked_count") or raw.get("likes")
             or interact.get("liked_count") or 0)
    comments = (raw.get("comment_count") or raw.get("comments")
                or interact.get("comment_count") or 0)
    author = raw.get("author") or raw.get("source") or ""
    if isinstance(raw.get("user"), dict):
        author = raw["user"].get("nickname") or raw["user"].get("nick_name") or ""
    elif raw.get("nickname"):
        author = raw["nickname"]

    full_text = title + " " + desc
    url = (raw.get("url") or raw.get("link") or raw.get("note_url") or
           (f"https://www.xiaohongshu.com/discovery/item/{nid}" if nid else ""))
    return {
        "id": nid,
        "title": title,
        "url": url or "https://www.xiaohongshu.com/",
        "cover": cover,
        "author": author,
        "likes": _readable_count(likes),
        "comments": _readable_count(comments),
        "snippet": desc[:120].replace("\n", " "),
        "sentiment": detect_sentiment(full_text),
        "theme": detect_theme(full_text),
    }


def _readable_count(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return n
    if n >= 10000:
        return f"{n/10000:.1f}万".rstrip("0").rstrip(".")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="00 编排底座输出的 candidates.json")
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-per-theme", type=int, default=8,
                    help="每个主题最多展示 N 篇")
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))
    raw_notes = extract_raw_notes(data)

    grouped = {}
    for raw in raw_notes:
        n = normalize_note(raw)
        if not (n.get("title") or n.get("snippet")):
            continue
        grouped.setdefault(n["theme"], []).append(n)

    # 排序：每个主题内按 likes 降序
    out = []
    theme_order = ["景点攻略", "美食推荐", "住宿体验", "拍照机位", "避雷防坑", "其他参考"]
    for theme in theme_order:
        notes = grouped.get(theme) or []
        if not notes:
            continue
        def _likes_int(x):
            v = x.get("likes")
            if isinstance(v, str) and "万" in v:
                try: return int(float(v.replace("万", "")) * 10000)
                except: return 0
            try: return int(v or 0)
            except: return 0
        notes.sort(key=_likes_int, reverse=True)
        out.append({"theme": theme, "notes": notes[:a.max_per_theme]})

    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "groups": len(out),
                      "total_notes": sum(len(g["notes"]) for g in out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
