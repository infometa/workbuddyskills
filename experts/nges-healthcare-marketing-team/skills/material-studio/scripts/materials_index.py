#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
materials_index.py — 物料资产库管理工具。

用法：
  # 索引一份新物料
  python3 materials_index.py add --type "research" --recipient YY教授" \
    --dept "肿瘤科" --headline "ASCO 2026 NSCLC研究" --filepath "/path/to/file.html"

  # 查询某医生的历史物料
  python3 materials_index.py query --recipient "YY"

  # 列出所有物料（最近20条）
  python3 materials_index.py list [--limit 20]

  # 检查某医生是否最近收过类似主题
  python3 materials_index.py check-dup --recipient "YY" --type "research" --topic "EGFR"

输出：JSON 到 stdout
存储：~/.workbuddy/med-rep-materials-index.json
"""
import argparse, json, os, sys
from datetime import date
from pathlib import Path

INDEX_FILE = Path(os.path.expanduser("~/.workbuddy/med-rep-materials-index.json"))

def load_index():
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {"materials": []}

def save_index(data):
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def cmd_add(args):
    data = load_index()
    entry = {
        "id": len(data["materials"]) + 1,
        "date": args.date or date.today().isoformat(),
        "type": args.type,
        "recipient": args.recipient or "",
        "dept": args.dept or "",
        "headline": args.headline or "",
        "topics": [t.strip() for t in args.topics.split(",")] if args.topics else [],
        "filepath": args.filepath or "",
    }
    data["materials"].append(entry)
    save_index(data)
    print(json.dumps(entry, ensure_ascii=False))

def cmd_query(args):
    data = load_index()
    results = [m for m in data["materials"] if args.recipient in m.get("recipient", "")]
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    if args.limit:
        results = results[:args.limit]
    print(json.dumps(results, ensure_ascii=False, indent=2))

def cmd_list(args):
    data = load_index()
    results = sorted(data["materials"], key=lambda x: x.get("date", ""), reverse=True)
    limit = args.limit or 20
    print(json.dumps(results[:limit], ensure_ascii=False, indent=2))

def cmd_check_dup(args):
    data = load_index()
    today = date.today()
    recent = []
    for m in data["materials"]:
        if args.recipient and args.recipient not in m.get("recipient", ""):
            continue
        if args.type and m.get("type") != args.type:
            continue
        # Check within 14 days
        try:
            m_date = date.fromisoformat(m.get("date", "2000-01-01"))
            if (today - m_date).days <= 14:
                # Check topic overlap
                if args.topic:
                    headline = m.get("headline", "")
                    topics = m.get("topics", [])
                    if args.topic.lower() in headline.lower() or any(args.topic.lower() in t.lower() for t in topics):
                        recent.append(m)
                else:
                    recent.append(m)
        except (ValueError, TypeError):
            continue
    is_dup = len(recent) > 0
    print(json.dumps({
        "isDuplicate": is_dup,
        "recentSimilar": recent,
        "suggestion": f"14天内已发过类似内容（{len(recent)}条），建议换个角度或等几天再发" if is_dup else "无重复，可以发送"
    }, ensure_ascii=False, indent=2))

def main():
    ap = argparse.ArgumentParser(description="物料资产库管理")
    sub = ap.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="索引新物料")
    p_add.add_argument("--type", required=True, help="greeting/news/research/education/card")
    p_add.add_argument("--recipient", default="")
    p_add.add_argument("--dept", default="")
    p_add.add_argument("--headline", default="")
    p_add.add_argument("--topics", default="", help="逗号分隔的关键词")
    p_add.add_argument("--filepath", default="")
    p_add.add_argument("--date", default="")

    p_query = sub.add_parser("query", help="查询某医生的物料")
    p_query.add_argument("--recipient", required=True)
    p_query.add_argument("--limit", type=int, default=10)

    p_list = sub.add_parser("list", help="列出所有物料")
    p_list.add_argument("--limit", type=int, default=20)

    p_dup = sub.add_parser("check-dup", help="检查重复")
    p_dup.add_argument("--recipient", default="")
    p_dup.add_argument("--type", default="")
    p_dup.add_argument("--topic", default="")

    args = ap.parse_args()
    if args.command == "add": cmd_add(args)
    elif args.command == "query": cmd_query(args)
    elif args.command == "list": cmd_list(args)
    elif args.command == "check-dup": cmd_check_dup(args)
    else:
        ap.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
