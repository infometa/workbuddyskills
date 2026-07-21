#!/usr/bin/env python3
"""
wordbook_manager.py — english-intensive-reader
Manage the local wordbook.json: add / list / delete / export (Anki CSV / Markdown).

Usage:
    python wordbook_manager.py add --word "pressing" --pos "adj." --definition "紧迫的" ...
    python wordbook_manager.py list [--level cet6] [--mastered false]
    python wordbook_manager.py stats
    python wordbook_manager.py delete --word "pressing"
    python wordbook_manager.py mark-mastered --word "pressing"
    python wordbook_manager.py export --format anki --output wordbook-anki.csv
    python wordbook_manager.py export --format md --output wordbook.md
"""

import sys
import os
import json
import argparse
import csv
from datetime import datetime, timezone
from typing import Optional, List, Dict


DEFAULT_WORDBOOK = "./wordbook.json"
WORDBOOK_VERSION = "1.0"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_wordbook(path: str) -> dict:
    """Load wordbook from JSON file. Create empty file if not exists."""
    if not os.path.exists(path):
        empty = _empty_wordbook()
        save_wordbook(path, empty)
        return empty

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate structure
        if "words" not in data:
            data["words"] = []
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ 单词本文件损坏：{e}，请检查 {path}", file=sys.stderr)
        sys.exit(1)


def save_wordbook(path: str, data: dict) -> None:
    """Save wordbook to JSON file."""
    data["updated_at"] = _now_iso()
    data["total_words"] = len(data.get("words", []))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _empty_wordbook() -> dict:
    now = _now_iso()
    return {
        "version": WORDBOOK_VERSION,
        "created_at": now,
        "updated_at": now,
        "total_words": 0,
        "words": [],
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _next_id(words: List[dict]) -> str:
    if not words:
        return "w001"
    max_num = max(int(w["id"][1:]) for w in words if w.get("id", "w000")[1:].isdigit())
    return f"w{max_num + 1:03d}"


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def add_word(
    path: str,
    word: str,
    pos: str,
    definition: str,
    collocations: List[str],
    example: str,
    source: str,
    level: str,
    tags: Optional[List[str]] = None,
) -> dict:
    """Add a word to the wordbook. Skip if already exists."""
    data = load_wordbook(path)
    words = data["words"]

    # Check for duplicate (case-insensitive)
    existing = next(
        (w for w in words if w["word"].lower() == word.lower() and w["pos"] == pos),
        None,
    )
    if existing:
        return {
            "action": "skipped",
            "message": f"「{word}」已在单词本中（加入于 {existing['added_at'][:10]}）",
            "word": existing,
        }

    new_word = {
        "id": _next_id(words),
        "word": word,
        "pos": pos,
        "definition": definition,
        "collocations": collocations,
        "example": example,
        "example_source": source,
        "level_tag": level,
        "added_at": _now_iso(),
        "review_count": 0,
        "last_reviewed_at": None,
        "mastered": False,
        "tags": tags or [],
    }

    words.append(new_word)
    save_wordbook(path, data)

    return {
        "action": "added",
        "message": f"✅ 「{word}」已加入单词本（当前共 {len(words)} 词）",
        "word": new_word,
    }


def list_words(
    path: str,
    level: Optional[str] = None,
    mastered: Optional[bool] = None,
    limit: int = 50,
) -> List[dict]:
    """List words with optional filters."""
    data = load_wordbook(path)
    words = data["words"]

    if level:
        words = [w for w in words if w.get("level_tag") == level]
    if mastered is not None:
        words = [w for w in words if w.get("mastered") == mastered]

    return words[:limit]


def get_stats(path: str) -> dict:
    """Get wordbook statistics."""
    data = load_wordbook(path)
    words = data["words"]

    by_level = {}
    for w in words:
        lvl = w.get("level_tag", "unknown")
        by_level[lvl] = by_level.get(lvl, 0) + 1

    mastered_count = sum(1 for w in words if w.get("mastered"))
    unreviewed_count = sum(1 for w in words if w.get("review_count", 0) == 0)

    latest = max(words, key=lambda w: w.get("added_at", ""), default=None)

    return {
        "total": len(words),
        "by_level": by_level,
        "mastered": mastered_count,
        "unreviewed": unreviewed_count,
        "latest_word": latest["word"] if latest else None,
        "latest_added_at": latest["added_at"][:10] if latest else None,
    }


def delete_word(path: str, word: str) -> dict:
    """Delete a word from the wordbook."""
    data = load_wordbook(path)
    original_count = len(data["words"])
    data["words"] = [w for w in data["words"] if w["word"].lower() != word.lower()]

    if len(data["words"]) == original_count:
        return {"action": "not_found", "message": f"「{word}」不在单词本中"}

    save_wordbook(path, data)
    return {"action": "deleted", "message": f"✅ 「{word}」已从单词本删除"}


def mark_mastered(path: str, word: str, mastered: bool = True) -> dict:
    """Mark a word as mastered or unmastered."""
    data = load_wordbook(path)
    for w in data["words"]:
        if w["word"].lower() == word.lower():
            w["mastered"] = mastered
            w["last_reviewed_at"] = _now_iso()
            w["review_count"] = w.get("review_count", 0) + 1
            save_wordbook(path, data)
            status = "已掌握" if mastered else "未掌握"
            return {"action": "updated", "message": f"✅ 「{word}」标记为{status}"}

    return {"action": "not_found", "message": f"「{word}」不在单词本中"}


def export_anki(path: str, output: str) -> dict:
    """Export wordbook as Anki-compatible CSV (tab-separated)."""
    data = load_wordbook(path)
    words = data["words"]

    if not words:
        return {"action": "empty", "message": "单词本为空，无法导出"}

    with open(output, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        # Anki format: Front, Back, Tags
        for w in words:
            collocations_str = " / ".join(w.get("collocations", []))
            front = w["word"]
            back = (
                f"{w['pos']} {w['definition']}\n"
                f"搭配：{collocations_str}\n"
                f"例句：{w.get('example', '')}"
            )
            tags = " ".join(w.get("tags", []) + [w.get("level_tag", "")])
            writer.writerow([front, back, tags])

    return {
        "action": "exported",
        "message": f"✅ 已导出 {len(words)} 个单词到 {output}（Anki CSV 格式）",
        "count": len(words),
        "output": output,
    }


def export_markdown(path: str, output: str) -> dict:
    """Export wordbook as Markdown table."""
    data = load_wordbook(path)
    words = data["words"]

    if not words:
        return {"action": "empty", "message": "单词本为空，无法导出"}

    lines = [
        "# 📚 单词本",
        f"> 共 {len(words)} 词 | 导出时间：{_now_iso()[:10]}",
        "",
        "| 单词 | 词性 | 释义 | 搭配 | 例句 | 档位 | 已掌握 |",
        "|------|------|------|------|------|------|--------|",
    ]

    for w in words:
        collocations_str = " / ".join(w.get("collocations", [])[:2])
        example_short = w.get("example", "")[:60] + ("..." if len(w.get("example", "")) > 60 else "")
        mastered_icon = "✅" if w.get("mastered") else "⬜"
        lines.append(
            f"| **{w['word']}** | {w['pos']} | {w['definition']} "
            f"| {collocations_str} | {example_short} | {w.get('level_tag', '')} | {mastered_icon} |"
        )

    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "action": "exported",
        "message": f"✅ 已导出 {len(words)} 个单词到 {output}（Markdown 格式）",
        "count": len(words),
        "output": output,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Wordbook manager for english-intensive-reader")
    parser.add_argument("--wordbook", default=DEFAULT_WORDBOOK, help="Path to wordbook.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = subparsers.add_parser("add", help="Add a word")
    add_p.add_argument("--word", required=True)
    add_p.add_argument("--pos", required=True)
    add_p.add_argument("--definition", required=True)
    add_p.add_argument("--collocations", default="", help="Comma-separated collocations")
    add_p.add_argument("--example", default="")
    add_p.add_argument("--source", default="")
    add_p.add_argument("--level", default="cet6",
                       choices=["cet4", "cet6", "kaoyan", "foreign_press"])
    add_p.add_argument("--tags", default="", help="Comma-separated tags")

    # list
    list_p = subparsers.add_parser("list", help="List words")
    list_p.add_argument("--level", choices=["cet4", "cet6", "kaoyan", "foreign_press"])
    list_p.add_argument("--mastered", choices=["true", "false"])
    list_p.add_argument("--limit", type=int, default=50)

    # stats
    subparsers.add_parser("stats", help="Show statistics")

    # delete
    del_p = subparsers.add_parser("delete", help="Delete a word")
    del_p.add_argument("--word", required=True)

    # mark-mastered
    mark_p = subparsers.add_parser("mark-mastered", help="Mark word as mastered")
    mark_p.add_argument("--word", required=True)
    mark_p.add_argument("--unmark", action="store_true", help="Mark as unmastered")

    # export
    exp_p = subparsers.add_parser("export", help="Export wordbook")
    exp_p.add_argument("--format", required=True, choices=["anki", "md"])
    exp_p.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.command == "add":
        result = add_word(
            path=args.wordbook,
            word=args.word,
            pos=args.pos,
            definition=args.definition,
            collocations=[c.strip() for c in args.collocations.split(",") if c.strip()],
            example=args.example,
            source=args.source,
            level=args.level,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()],
        )
        print(result["message"])

    elif args.command == "list":
        mastered = None
        if args.mastered == "true":
            mastered = True
        elif args.mastered == "false":
            mastered = False
        words = list_words(args.wordbook, level=args.level, mastered=mastered, limit=args.limit)
        if not words:
            print("单词本为空或无匹配词条")
        else:
            for w in words:
                mastered_icon = "✅" if w.get("mastered") else "⬜"
                print(f"{mastered_icon} [{w['id']}] {w['word']} {w['pos']} — {w['definition']} ({w.get('level_tag', '')})")

    elif args.command == "stats":
        stats = get_stats(args.wordbook)
        print(f"📚 单词本统计")
        print(f"总词数：{stats['total']}")
        for lvl, cnt in stats.get("by_level", {}).items():
            print(f"  ├── {lvl}：{cnt} 词")
        print(f"已掌握：{stats['mastered']} 词（{int(stats['mastered']/max(stats['total'],1)*100)}%）")
        print(f"未复习：{stats['unreviewed']} 词")
        if stats["latest_word"]:
            print(f"最近添加：{stats['latest_word']}（{stats['latest_added_at']}）")

    elif args.command == "delete":
        result = delete_word(args.wordbook, args.word)
        print(result["message"])

    elif args.command == "mark-mastered":
        result = mark_mastered(args.wordbook, args.word, mastered=not args.unmark)
        print(result["message"])

    elif args.command == "export":
        if args.format == "anki":
            result = export_anki(args.wordbook, args.output)
        else:
            result = export_markdown(args.wordbook, args.output)
        print(result["message"])


if __name__ == "__main__":
    main()
