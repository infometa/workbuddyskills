#!/usr/bin/env python3
import argparse, csv, json, math, datetime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topics_json", help="JSON list with topic,difficulty")
    ap.add_argument("--start", required=True)
    ap.add_argument("--exam", required=True)
    ap.add_argument("--out", default="revision_schedule.csv")
    args = ap.parse_args()
    topics = json.load(open(args.topics_json, "r", encoding="utf-8"))
    start = datetime.date.fromisoformat(args.start)
    exam = datetime.date.fromisoformat(args.exam)
    days = max((exam - start).days, 1)
    per = max(days // max(len(topics),1), 1)
    rows = []
    cur = start
    for topic in topics:
        rows.append({"date": cur.isoformat(), "topic": topic.get("topic",""), "phase": "learn"})
        cur += datetime.timedelta(days=per)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","topic","phase"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
