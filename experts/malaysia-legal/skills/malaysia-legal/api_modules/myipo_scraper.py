#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyIPO Web-Scrape 辅助模块
通过定向网络搜索提取马来西亚企业知识产权信息

用法（作为 Risa Agent 内部调用参考，非独立运行脚本）：
  - 在 Phase DD-3 中，若目标企业属于科技/制造/品牌行业，
    自动触发知识产权搜索
  - 本文件定义搜索策略模板和输出格式，Agent 在执行时参考
"""

# MyIPO Web-Scrape 搜索模板

SEARCH_TEMPLATES = {
    "patent": [
        '"{company_name}" patent MyIPO',
        '"{company_name}" "patent application" Malaysia',
        '"{company_name}" patent site:myipo.gov.my',
        '"{company_name}" patent site:iponline.myipo.gov.my',
        '"{company_name}" "intellectual property" Malaysia patent',
    ],
    "trademark": [
        '"{company_name}" trademark Malaysia MyIPO',
        '"{company_name}" "trademark registration" Malaysia',
        '"{company_name}" trademark site:myipo.gov.my',
        '"{company_name}" brand registration Malaysia',
    ],
    "industrial_design": [
        '"{company_name}" "industrial design" Malaysia MyIPO',
        '"{company_name}" "design registration" Malaysia',
    ],
    "asean_ip": [
        'site:aseanipregister.gov.my "{company_name}"',
    ],
}

# 输出格式
REPORT_TEMPLATE = """
## 📋 知识产权资产

| 类型 | 检索结果 | 详情 | 来源 |
|------|---------|------|------|
| 专利 (Patent) | {patent_count} | {patent_details} | MyIPO / ASEAN IP Register |
| 商标 (Trademark) | {trademark_count} | {trademark_details} | MyIPO |
| 工业设计 (Industrial Design) | {design_count} | {design_details} | MyIPO |

**可信度**: B（公开搜索，MyIPO 未提供免费 API）
**检索日期**: {search_date}
"""
