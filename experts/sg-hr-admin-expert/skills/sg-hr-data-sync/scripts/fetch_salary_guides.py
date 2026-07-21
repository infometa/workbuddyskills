#!/usr/bin/env python3
"""
免费薪资指南爬取
检查 Hays / Robert Half / Robert Walters 是否发布新年度薪资指南
频率：每年3月(Hays)、年中(Robert Half)、按需
"""

import json
import re
import sys
from datetime import datetime

SALARY_GUIDE_SOURCES = {
    "hays": {
        "name": "Hays Asia Salary Guide",
        "url": "https://www.hays.com.sg/salary-guide",
        "press_url": "https://www.hays.com.sg/press-release/content/salary-raises-2026-hays-salary-guide",
        "typical_release": "March",
        "latest_known": "2026",
        "latest_known_date": "2026-03-18",
        "key_stats": {
            "dissatisfied_with_pay_pct": 39,
            "movers_over_10pct_raise": 43,
            "planning_career_change_pct": 43,
            "top_motivation": "limited career opportunities (43%)"
        }
    },
    "robert_half": {
        "name": "Robert Half Singapore Salary Guide",
        "url": "https://www.roberthalf.com/sg/en/insights/salary-guide",
        "typical_release": "Mid-year",
        "latest_known": "2026"
    },
    "robert_walters": {
        "name": "Robert Walters Singapore Salary Survey",
        "url": "https://www.robertwalters.com.sg/our-services/salary-survey.html",
        "typical_release": "Annual",
        "latest_known": "2026"
    }
}

def check_new_edition(source_key, web_text):
    """
    从网页文本中检查是否有新年份的薪资指南发布
    返回: {"has_new": bool, "new_year": str or None, "headline": str or None}
    """
    current_known = int(SALARY_GUIDE_SOURCES[source_key]["latest_known"])
    # 搜索年份模式: "2026" "2027" 等
    years_found = set(re.findall(r"(20[2-9]\d)\s+(?:Salary|Asia|Singapore|Guide)", web_text, re.IGNORECASE))
    years_found.update(set(re.findall(r"(?:Salary Guide|Salary Survey)\s*(20[2-9]\d)", web_text, re.IGNORECASE)))
    
    for year_str in years_found:
        year = int(year_str)
        if year > current_known:
            return {"has_new": True, "new_year": str(year), "headline": f"New {year} edition detected"}
    
    return {"has_new": False, "new_year": None, "headline": None}

def main():
    result = {
        "last_checked": datetime.now().isoformat(),
        "sources": {}
    }
    
    for key, info in SALARY_GUIDE_SOURCES.items():
        result["sources"][key] = {
            "name": info["name"],
            "url": info["url"],
            "latest_known_edition": info["latest_known"],
            "typical_release_month": info.get("typical_release", "Unknown"),
            "status": "not_checked"  # 由AI在执行时通过WebFetch填写
        }
    
    if "--schema" in sys.argv:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
