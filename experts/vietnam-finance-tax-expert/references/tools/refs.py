# -*- coding: utf-8 -*-
"""
合规与ODI速查 v1.0
  python refs.py calendar    # 越南申报合规日历
  python refs.py odi         # 中资企业赴越 ODI 出境流程
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")


def _load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)


def show_calendar():
    d = _load("compliance_calendar.json")
    print("【越南申报合规日历】" + d["meta"]["note"])
    print("-" * 70)
    for o in d["obligations"]:
        print(f"[{o['frequency']:<4}] {o['name_zh']}")
        print(f"   截止：{o['deadline_rule']}  | 依据：{o['legal_basis']}")
        print(f"   提示：{o['note']}")
    print("-" * 70)


def show_odi():
    d = _load("odi_checklist.json")
    print("【中资企业赴越 ODI 出境投资流程】" + d["meta"]["note"])
    print("-" * 70)
    for s in d["stages"]:
        print(f"第{s['step']}步  {s['name_zh']}（{s['authority']}）")
        print(f"   触发：{s['trigger']}")
        print(f"   周期：{s['typical_duration']}")
        print(f"   关键材料：{'; '.join(s['key_materials'])}")
        print(f"   说明：{s['note']}")
    ts = d["timeline_summary"]
    print("-" * 70)
    print(f"时间线：{ts['parallelizable']}")
    print(f"  快速通道：{ts['fast_track_days']}；完整通道：{ts['full_track_days']}")
    print(f"常见坑：{'; '.join(ts['common_pitfalls'])}")


def main():
    p = argparse.ArgumentParser(description="合规日历与ODI速查")
    p.add_argument("what", choices=["calendar", "odi"], help="calendar=越南合规日历 / odi=赴越ODI流程")
    args = p.parse_args()
    if args.what == "calendar":
        show_calendar()
    else:
        show_odi()


if __name__ == "__main__":
    main()
