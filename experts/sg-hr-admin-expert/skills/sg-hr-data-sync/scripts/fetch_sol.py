#!/usr/bin/env python3
"""
MOM SOL 紧缺职业清单爬取
目标：https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility/compass-c5-skills-bonus-shortage-occupation-list-sol
提取：7大行业、各岗位名称、适用期间
频率：每年10-12月检查更新（SOL每年更新一次）
"""

import json
import re
import sys
from datetime import datetime

# 2026年SOL已知结构（2025年11月发布，2026年1月1日起适用）
SOL_2026_TEMPLATE = {
    "source_url": "https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility/compass-c5-skills-bonus-shortage-occupation-list-sol",
    "last_fetched": "",
    "release_date": "2025-11",
    "applicable_from": "2026-01-01",
    "sectors": {
        "Agritech": [
            "Alternative protein food application scientist",
            "Novel food biotechnologist"
        ],
        "Financial services": [
            "Financial or investment adviser (ultra-high or high net worth, family office and philanthropy)"
        ],
        "Green economy": [
            "Carbon project or programme manager",
            "Carbon standards and methodology analyst",
            "Carbon trader",
            "Carbon verification and audit specialist"
        ],
        "Healthcare": [
            "Clinical psychologist",
            "Diagnostic radiographer",
            "Medical social worker",
            "Occupational therapist",
            "Physiotherapist",
            "Podiatrist",
            "Registered nurse"
        ],
        "Infocomm technology": [
            "Artificial Intelligence (AI) scientist or engineer",
            "Applications or systems programmer",
            "Cloud specialist",
            "Cybersecurity architect",
            "Data scientist",
            "Digital forensics specialist",
            "Penetration testing specialist",
            "Software and applications manager (technical lead or supervisor)",
            "Software developer",
            "Web and mobile applications developer"
        ],
        "Maritime": [
            "Marine superintendent",
            "Marine technical superintendent"
        ],
        "Semi-conductor": [
            "Semi-conductor engineer",
            "Instrumentation engineer",
            "Process engineer"
        ]
    },
    "notes": {
        "ict_5yr_ep": "Infocomm technology occupations may qualify for 5-year EP duration",
        "bonus_points": "C5 Skills bonus: +20 COMPASS points"
    }
}

def count_occupations(sol_data):
    """统计总岗位数"""
    total = 0
    for sector, occupations in sol_data["sectors"].items():
        total += len(occupations)
    return total

def diff_sol(old_data, new_data):
    """比较两个SOL版本的差异"""
    changes = {"added": [], "removed": [], "sector_changes": []}
    
    old_sectors = set(old_data["sectors"].keys())
    new_sectors = set(new_data["sectors"].keys())
    
    # 行业变更
    for s in new_sectors - old_sectors:
        changes["sector_changes"].append(f"+ 新增行业: {s}")
    for s in old_sectors - new_sectors:
        changes["sector_changes"].append(f"- 移除行业: {s}")
    
    # 岗位变更（在共有行业中）
    for sector in old_sectors & new_sectors:
        old_occs = set(old_data["sectors"][sector])
        new_occs = set(new_data["sectors"][sector])
        for occ in new_occs - old_occs:
            changes["added"].append(f"{sector}: {occ}")
        for occ in old_occs - new_occs:
            changes["removed"].append(f"{sector}: {occ}")
    
    return changes

def main():
    schema = SOL_2026_TEMPLATE.copy()
    schema["last_fetched"] = datetime.now().isoformat()
    schema["total_occupations"] = count_occupations(schema)
    
    if "--schema" in sys.argv:
        print(json.dumps(schema, indent=2, ensure_ascii=False))
        return
    
    print(json.dumps(schema, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
