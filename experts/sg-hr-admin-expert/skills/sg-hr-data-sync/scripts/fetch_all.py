#!/usr/bin/env python3
"""
综合数据爬取批处理入口
依次调用各 fetch 脚本，汇总差异报告
"""

import json
import sys
import os
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REFS_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR), "references")
LAST_KNOWN_PATH = os.path.join(REFS_DIR, "last_known.json")

def load_last_known():
    """加载上次缓存数据"""
    if os.path.exists(LAST_KNOWN_PATH):
        with open(LAST_KNOWN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_known(data):
    """保存本次缓存数据"""
    os.makedirs(REFS_DIR, exist_ok=True)
    data["_updated_at"] = datetime.now().isoformat()
    with open(LAST_KNOWN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compare_data(old, new):
    """递归比较两个数据结构"""
    if type(old) != type(new):
        return {"type": "changed", "old": old, "new": new}
    
    if isinstance(old, dict):
        diffs = {}
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            if key.startswith("_"):
                continue
            if key not in old:
                diffs[key] = {"type": "added", "new": new[key]}
            elif key not in new:
                diffs[key] = {"type": "removed", "old": old[key]}
            else:
                result = compare_data(old[key], new[key])
                if result:
                    diffs[key] = result
        return diffs if diffs else None
    
    if isinstance(old, list):
        if old != new:
            return {"type": "changed", "old": old, "new": new}
        return None
    
    if old != new:
        return {"type": "changed", "old": old, "new": new}
    return None

def generate_report(diffs):
    """生成人类可读的差异报告"""
    if not diffs:
        return "【数据同步报告】无变化，所有数据均为最新。"
    
    lines = [f"【数据同步报告】{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    for category, diff in diffs.items():
        lines.append(f"## {category}")
        if isinstance(diff, dict):
            for item, change in diff.items():
                if isinstance(change, dict) and change.get("type"):
                    lines.append(f"- **{item}**: {change['type']}")
                    if "old" in change and "new" in change:
                        lines.append(f"  旧值: {change['old']}")
                        lines.append(f"  新值: {change['new']}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python fetch_all.py [--check] [--update]")
        print("  --check   仅检查变更，不更新缓存")
        print("  --update  检查变更并更新缓存（默认仅检查）")
        return
    
    # 这是批处理入口，实际执行时由AI逐项调用WebFetch
    print(json.dumps({
        "status": "ready",
        "scripts": [
            "fetch_cpf_rates.py",
            "fetch_sol.py", 
            "fetch_compass.py",
            "fetch_salary_guides.py",
            "fetch_labour_market.py"
        ],
        "instructions": "Run each script with --schema to get data template, then use WebFetch to populate, then call compare_data() to detect changes."
    }, indent=2))

if __name__ == "__main__":
    main()
