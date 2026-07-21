#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor_profile.py — 医生画像管理工具。

用法：
  # 添加/更新医生
  python3 doctor_profile.py add --name "YY" --dept "肿瘤科" --hospital "上海市胸科医院" \
    --field "非小细胞肺癌,EGFR靶向,免疫治疗" --level "kol" --birthday "1963-05-20"

  # 查询医生
  python3 doctor_profile.py get --name "YY"

  # 列出所有医生
  python3 doctor_profile.py list

  # 记录触达
  python3 doctor_profile.py touch --name "YY" --type "research" --topic "ASCO 2026 NSCLC研究"

  # 查看近期建议（哪些医生该触达了）
  python3 doctor_profile.py suggest

  # 生日提醒（7天内）
  python3 doctor_profile.py birthday-check

输出：JSON 到 stdout
存储：~/.workbuddy/med-rep-doctors.json
"""
import argparse, json, os, sys
from datetime import datetime, date, timedelta
from pathlib import Path

DOCTORS_FILE = Path(os.path.expanduser("~/.workbuddy/med-rep-doctors.json"))

def load_doctors():
    if DOCTORS_FILE.exists():
        return json.loads(DOCTORS_FILE.read_text(encoding="utf-8"))
    return {"doctors": []}

def save_doctors(data):
    DOCTORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DOCTORS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def find_doctor(data, name):
    for d in data["doctors"]:
        if d["name"] == name:
            return d
    return None

def cmd_add(args):
    data = load_doctors()
    doc = find_doctor(data, args.name)
    if doc is None:
        doc = {"name": args.name, "contacts": [], "lastTopics": []}
        data["doctors"].append(doc)
    # Update fields if provided
    if args.dept: doc["dept"] = args.dept
    if args.hospital: doc["hospital"] = args.hospital
    if args.field: doc["fields"] = [f.strip() for f in args.field.split(",")]
    if args.level: doc["level"] = args.level  # kol / director / attending / community
    if args.birthday: doc["birthday"] = args.birthday
    if args.notes: doc["notes"] = args.notes
    doc["updatedAt"] = datetime.now().isoformat()
    save_doctors(data)
    print(json.dumps(doc, ensure_ascii=False))

def cmd_get(args):
    data = load_doctors()
    doc = find_doctor(data, args.name)
    if doc:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": f"未找到医生：{args.name}"}, ensure_ascii=False))
        sys.exit(1)

def cmd_list(args):
    data = load_doctors()
    summary = []
    for d in data["doctors"]:
        summary.append({
            "name": d.get("name"),
            "dept": d.get("dept", ""),
            "hospital": d.get("hospital", ""),
            "level": d.get("level", ""),
            "lastContact": d["contacts"][-1]["date"] if d.get("contacts") else "从未触达",
            "contactCount": len(d.get("contacts", []))
        })
    print(json.dumps(summary, ensure_ascii=False, indent=2))

def cmd_touch(args):
    data = load_doctors()
    doc = find_doctor(data, args.name)
    if doc is None:
        doc = {"name": args.name, "contacts": [], "lastTopics": []}
        data["doctors"].append(doc)
    contact = {
        "date": date.today().isoformat(),
        "type": args.type,
        "topic": args.topic or ""
    }
    if "contacts" not in doc:
        doc["contacts"] = []
    doc["contacts"].append(contact)
    # Keep lastTopics (max 10)
    if "lastTopics" not in doc:
        doc["lastTopics"] = []
    if args.topic:
        doc["lastTopics"].append({"date": contact["date"], "type": args.type, "topic": args.topic})
        doc["lastTopics"] = doc["lastTopics"][-10:]
    save_doctors(data)
    print(json.dumps({"status": "ok", "doctor": args.name, "contact": contact}, ensure_ascii=False))

def cmd_suggest(args):
    data = load_doctors()
    today = date.today()
    suggestions = []
    for d in data["doctors"]:
        contacts = d.get("contacts", [])
        if not contacts:
            days_since = 999
            last_date = "从未触达"
        else:
            last = contacts[-1]["date"]
            last_date = last
            days_since = (today - date.fromisoformat(last)).days
        # Suggest if >14 days since last contact
        if days_since >= 14:
            suggestions.append({
                "name": d.get("name"),
                "dept": d.get("dept", ""),
                "daysSinceLastContact": days_since,
                "lastContact": last_date,
                "fields": d.get("fields", []),
                "suggestion": "建议本周触达" if days_since < 30 else "已超30天未触达，建议尽快联系"
            })
    suggestions.sort(key=lambda x: -x["daysSinceLastContact"])
    print(json.dumps(suggestions, ensure_ascii=False, indent=2))

def cmd_birthday_check(args):
    data = load_doctors()
    today = date.today()
    upcoming = []
    for d in data["doctors"]:
        bday = d.get("birthday")
        if not bday:
            continue
        try:
            b = date.fromisoformat(bday)
            # This year's birthday
            this_year_bday = b.replace(year=today.year)
            if this_year_bday < today:
                this_year_bday = b.replace(year=today.year + 1)
            days_until = (this_year_bday - today).days
            if days_until <= 7:
                upcoming.append({
                    "name": d.get("name"),
                    "dept": d.get("dept", ""),
                    "birthday": bday,
                    "daysUntil": days_until,
                    "hint": "今天！" if days_until == 0 else f"{days_until}天后"
                })
        except (ValueError, TypeError):
            continue
    upcoming.sort(key=lambda x: x["daysUntil"])
    print(json.dumps(upcoming, ensure_ascii=False, indent=2))

def main():
    ap = argparse.ArgumentParser(description="医生画像管理")
    sub = ap.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="添加/更新医生")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--dept", default="")
    p_add.add_argument("--hospital", default="")
    p_add.add_argument("--field", default="", help="逗号分隔的关注领域")
    p_add.add_argument("--level", default="", help="kol/director/attending/community")
    p_add.add_argument("--birthday", default="", help="YYYY-MM-DD")
    p_add.add_argument("--notes", default="")

    p_get = sub.add_parser("get", help="查询医生")
    p_get.add_argument("--name", required=True)

    sub.add_parser("list", help="列出所有医生")

    p_touch = sub.add_parser("touch", help="记录触达")
    p_touch.add_argument("--name", required=True)
    p_touch.add_argument("--type", required=True, help="greeting/news/research/education/card")
    p_touch.add_argument("--topic", default="")

    sub.add_parser("suggest", help="触达建议")
    sub.add_parser("birthday-check", help="生日提醒（7天内）")

    args = ap.parse_args()
    if args.command == "add": cmd_add(args)
    elif args.command == "get": cmd_get(args)
    elif args.command == "list": cmd_list(args)
    elif args.command == "touch": cmd_touch(args)
    elif args.command == "suggest": cmd_suggest(args)
    elif args.command == "birthday-check": cmd_birthday_check(args)
    else:
        ap.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
