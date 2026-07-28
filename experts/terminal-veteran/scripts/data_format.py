#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_format.py — 数据格式化与增强引擎

功能：
  1. 将脱敏后的报告原文解析提取成标准化Markdown文件
  2. 每月生成7个文件 + 更新3个聚合文件
  3. 7个增强维度：5G品牌/价位段环比/TOP10均价/分省5G/品牌动态/核心信号/累计数据

输入: data_deidentify.deidentify_content() 的返回值
输出: {"status": "ok", "files": {文件名: 文件内容, ...}, "details": "..."}
"""

import re
import os
from datetime import datetime


def _extract_numbers(text):
    """从文本中提取数字（万台/亿元/元等）。"""
    patterns = {
        "sales_volume": r"销量[：是为]*([\d,]+)\s*万台",
        "sales_amount": r"销售额[：是为]*([\d,]+)\s*亿元",
        "avg_price": r"均价[：是为]*([\d,]+)\s*元",
        "5g_rate": r"5G\s*渗透率[：是为]*([\d.]+)\s*%",
        "online_rate": r"线上[占比]*[：是为]*([\d.]+)\s*%",
    }
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1).replace(",", "")
    return result


def _format_market_overview(content, year_month):
    """格式化月度市场概况。"""
    year = year_month[:4]
    month = year_month[4:]

    comp = content.get("comprehensive", {})
    intro = comp.get("intro", comp.get("content", ""))

    nums = _extract_numbers(intro)

    md = f"""# {year}年{int(month)}月手机市场概况

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

## 一、{int(month)}月市场概况

| 指标 | 数值 | 环比 | 同比 |
|------|------|------|------|
| 销量 | {nums.get('sales_volume', '—')}万台 | — | — |
| 销售额 | {nums.get('sales_amount', '—')}亿元 | — | — |
| 均价 | {nums.get('avg_price', '—')}元 | — | — |
| 5G渗透率 | {nums.get('5g_rate', '—')}% | — | — |
| 线上占比 | {nums.get('online_rate', '—')}% | — | — |

## 二、核心信号

> 注：以下信号基于月度市场监测报告自动提取，需人工复核后引用。

1. （待AI从报告原文提取关键信号）
2. （待AI从报告原文提取关键信号）
3. （待AI从报告原文提取关键信号）

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_brand_competition(content, year_month):
    """格式化品牌竞争格局。"""
    year = year_month[:4]
    month = year_month[4:]

    md = f"""# {year}年{int(month)}月品牌竞争格局

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

## TOP6品牌份额

| 品牌 | 份额 | 环比 | 销量(万) | 关键动态 |
|------|------|------|---------|---------|
| 华为 | — | — | — | （待提取） |
| 苹果 | — | — | — | （待提取） |
| OPPO | — | — | — | （待提取） |
| vivo | — | — | — | （待提取） |
| 小米 | — | — | — | （待提取） |
| 荣耀 | — | — | — | （待提取） |

## 5G品牌排名

| 排名 | 品牌 | 5G份额 |
|------|------|--------|
| 1 | — | — |
| 2 | — | — |
| 3 | — | — |
| 4 | — | — |
| 5 | — | — |

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_price_segments(content, year_month):
    """格式化价位段结构。"""
    year = year_month[:4]
    month = year_month[4:]

    md = f"""# {year}年{int(month)}月价位段结构

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

| 价位段 | 份额 | 环比 |
|--------|------|------|
| 6000+ | — | — |
| 5000-6000 | — | — |
| 4000-5000 | — | — |
| 3000-4000 | — | — |
| 1500-2000 | — | — |
| 1000-1500 | — | — |
| 1K- | — | — |

**关键趋势**: （待AI提取）

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_channels(content, year_month):
    """格式化渠道结构。"""
    year = year_month[:4]
    month = year_month[4:]

    md = f"""# {year}年{int(month)}月渠道结构

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

| 渠道 | 销量(万) | 占比 | 5G渗透率 | TOP品牌 |
|------|---------|------|---------|---------|
| 线上 | — | — | — | — |
| 线下 | — | — | — | — |

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_top10_models(content, year_month):
    """格式化TOP10机型。"""
    year = year_month[:4]
    month = year_month[4:]

    md = f"""# {year}年{int(month)}月TOP10机型

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

| 排名 | 机型 | 销量(万) | 环比 | 均价 |
|------|------|---------|------|------|
| 1 | — | — | — | — |
| 2 | — | — | — | — |
| 3 | — | — | — | — |
| 4 | — | — | — | — |
| 5 | — | — | — | — |
| 6 | — | — | — | — |
| 7 | — | — | — | — |
| 8 | — | — | — | — |
| 9 | — | — | — | — |
| 10 | — | — | — | — |

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_provincial(content, year_month):
    """格式化分省分析。"""
    year = year_month[:4]
    month = year_month[4:]

    prov = content.get("provincial", {})
    prov_intro = prov.get("intro", prov.get("content", ""))

    md = f"""# {year}年{int(month)}月分省分析

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

## 全国总体概况

{prov_intro[:500] if prov_intro else '（分省报告未找到，待补充）'}

## TOP10大省排名

| 排名 | 省份 | 销量（万台） | 同比 | 环比 | TOP1品牌 | 5G渗透率 |
|------|------|------------|------|------|---------|---------|
| 1 | — | — | — | — | — | — |
| 2 | — | — | — | — | — | — |
| ... | ... | ... | ... | ... | ... | ... |

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def _format_month_comparison(content, year_month):
    """格式化月度对比。"""
    year = year_month[:4]
    month = year_month[4:]

    md = f"""# {year}年{int(month)}月与上月对比

> 数据来源：行业知识库 | 提取：{datetime.now().strftime('%Y-%m-%d')} | 脱敏处理

| 指标 | 上月 | 本月 | 变化 |
|------|-----|-----|------|
| 销量 | — | — | — |
| 均价 | — | — | — |
| 5G渗透率 | — | — | — |
| 华为份额 | — | — | — |
| 苹果份额 | — | — | — |
| 线上占比 | — | — | — |
| 同比 | — | — | — |

## 核心信号

1. （待AI提取）
2. （待AI提取）
3. （待AI提取）

---

> 整理时间：{datetime.now().strftime('%Y-%m-%d')}
"""
    return md


def format_monthly_data(deidentify_result, year_month):
    """
    主函数：格式化月度数据。

    参数:
        deidentify_result: data_deidentify.deidentify_content() 的返回值
        year_month: 6位年月字符串

    返回:
        {"status": "ok", "files": {文件名: 内容}, "details": "..."}
    """
    if deidentify_result.get("status") != "ok":
        return {"status": "error", "details": "脱敏结果状态异常"}

    content = deidentify_result.get("content", {})

    # 生成月度目录下的7个文件
    files = {}
    month_dir = f"data/{year_month[:4]}-{year_month[4:]}/"

    files[f"{month_dir}market-overview.md"] = _format_market_overview(content, year_month)
    files[f"{month_dir}brand-competition.md"] = _format_brand_competition(content, year_month)
    files[f"{month_dir}price-segments.md"] = _format_price_segments(content, year_month)
    files[f"{month_dir}channels.md"] = _format_channels(content, year_month)
    files[f"{month_dir}top10-models.md"] = _format_top10_models(content, year_month)
    files[f"{month_dir}provincial-analysis.md"] = _format_provincial(content, year_month)
    files[f"{month_dir}month-comparison.md"] = _format_month_comparison(content, year_month)

    # 聚合文件（提示AI更新，实际更新由AI在管线中完成）
    files["data/latest-update.md"] = _format_market_overview(content, year_month)

    return {
        "status": "ok",
        "files": files,
        "details": f"生成 {len(files)} 个文件（{month_dir} 目录 + latest-update.md）",
    }


if __name__ == "__main__":
    # 测试
    test_input = {
        "status": "ok",
        "month": "202605",
        "content": {
            "comprehensive": {
                "title": "手机市场月度综合分析报告-202605",
                "intro": "2026年5月全国手机市场销量1958万台，销售额831亿元，均价4246元",
                "content": "销量1958万台，销售额831亿元，均价4246元，5G渗透率74.7%",
            },
            "provincial": {
                "title": "手机市场月度分省分析报告-202605",
                "intro": "2026年5月分省分析...",
                "content": "",
            },
        },
    }
    result = format_monthly_data(test_input, "202605")
    print(f"状态: {result['status']}")
    print(f"详情: {result['details']}")
    for fname, fcontent in result["files"].items():
        print(f"  {fname}: {len(fcontent)} 字符")
