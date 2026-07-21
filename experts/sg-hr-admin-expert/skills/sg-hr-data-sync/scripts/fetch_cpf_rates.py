#!/usr/bin/env python3
"""
CPF 费率爬取脚本
目标：https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay
提取：各年龄段 CPF 雇主/雇员/总费率、OW Ceiling
频率：每年1月检查更新
"""

import json
import re
import sys
import os
from datetime import datetime

def extract_rates_from_text(text):
    """从网页文本中提取CPF费率"""
    rates = {}
    
    # 匹配费率模式: "55 and below ... 17 ... 20 ... 37"
    # 格式: {age_group}: {employer_rate} / {employee_rate} / {total_rate}
    pattern = r"(55 and below|Above 55 to 60|Above 60 to 65|Above 65 to 70|Above 70)[\s\S]*?(\d+(?:\.\d+)?)\s*\n\s*(\d+(?:\.\d+)?)\s*\n\s*(\d+(?:\.\d+)?)"
    matches = re.findall(pattern, text)
    
    for match in matches:
        age_group, emp_rate, empye_rate, total = match
        rates[age_group.strip()] = {
            "employer": float(emp_rate),
            "employee": float(empye_rate),
            "total": float(total)
        }
    
    # 提取OW Ceiling
    ceiling_pattern = r"(?:Ordinary Wage Ceiling|OW Ceiling)[^\d]*\$?(\d[\d,]+)"
    ceiling_match = re.search(ceiling_pattern, text)
    if ceiling_match:
        rates["ow_ceiling"] = int(ceiling_match.group(1).replace(",", ""))
    
    # 检查2027年变更公告
    rates["has_2027_update"] = "from 1 Jan 2027" in text.lower() or "2027" in text
    
    return rates

def main():
    """如果作为独立脚本运行，从WebFetch结果中读取；否则返回模板"""
    # 该脚本由 AI 在执行时调用 WebFetch，然后将结果传入
    # 这里提供数据结构定义供 AI 参照
    schema = {
        "source_url": "https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay",
        "last_fetched": datetime.now().isoformat(),
        "data": {
            "rates_by_age": {
                "55 and below": {"employer": 17.0, "employee": 20.0, "total": 37.0},
                "Above 55 to 60": {"employer": 16.0, "employee": 18.0, "total": 34.0},
                "Above 60 to 65": {"employer": 12.5, "employee": 12.5, "total": 25.0},
                "Above 65 to 70": {"employer": 9.0, "employee": 7.5, "total": 16.5},
                "Above 70": {"employer": 7.5, "employee": 5.0, "total": 12.5}
            },
            "ow_ceiling": 8000,
            "applicable_from": "2026-01-01",
            "next_scheduled_change": "2027-01-01"
        }
    }
    
    if "--schema" in sys.argv:
        print(json.dumps(schema, indent=2))
        return
    
    print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    main()
