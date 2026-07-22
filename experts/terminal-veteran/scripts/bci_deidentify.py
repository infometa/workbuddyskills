#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_deidentify.py — 数据脱敏处理引擎

功能：
  1. 对IMA报告原文执行来源脱敏
  2. 确保输出文本无内部数据源痕迹
  3. 提供validate校验函数

替换规则：
  BCI数据 → 行业数据显示
  BCI报告 → 月度市场监测报告
  BCI月度 → 月度市场监测
  BCI（其他上下文） → 行业知识库
  bci（路径/文件名） → industry
"""

import re

# 替换规则表（按优先级排序）
REPLACEMENTS = [
    (r"BCI\s*数据", "行业数据显示"),
    (r"BCI\s*报告", "月度市场监测报告"),
    (r"BCI\s*月度", "月度市场监测"),
    (r"BCI\s*知识库", "行业知识库"),
    (r"BCI", "行业知识库"),
    (r"bci-data", "industry-data"),
    (r"bci_fetch", "industry_fetch"),
    (r"bci_pipeline", "industry_pipeline"),
    (r"bci", "industry"),
]


def deidentify_text(text):
    """对文本执行脱敏处理。"""
    if not text:
        return text
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE if "bci" in pattern.lower() else 0)
    return text


def deidentify_content(fetch_result):
    """
    对fetch结果执行脱敏处理。

    参数:
        fetch_result: bci_fetch.fetch_monthly_reports() 的返回值

    返回:
        {
            "status": "ok",
            "month": ...,
            "content": {
                "comprehensive": {"title": ..., "intro": ..., "content": ...},
                "provincial": {"title": ..., "intro": ..., "content": ...},
            },
            "details": "..."
        }
    """
    if fetch_result.get("status") != "ok":
        return {"status": "error", "details": "fetch结果状态异常"}

    comp = fetch_result.get("comprehensive", {})
    prov = fetch_result.get("provincial", {})

    content = {
        "comprehensive": {
            "title": deidentify_text(comp.get("title", "")),
            "intro": deidentify_text(comp.get("intro", "")),
            "content": deidentify_text(comp.get("content", comp.get("intro", ""))),
        },
        "provincial": {
            "title": deidentify_text(prov.get("title", "")),
            "intro": deidentify_text(prov.get("intro", "")),
            "content": deidentify_text(prov.get("content", prov.get("intro", ""))),
        },
    }

    return {
        "status": "ok",
        "month": fetch_result.get("month", ""),
        "content": content,
        "details": "脱敏处理完成",
    }


def validate_content(content):
    """
    验证内容中无内部数据源残留。

    返回:
        {"valid": True/False, "issues": [...]}
    """
    issues = []
    text_parts = []

    for section in ["comprehensive", "provincial"]:
        section_data = content.get(section, {})
        for field in ["title", "intro", "content"]:
            text_parts.append(section_data.get(field, ""))

    full_text = " ".join(text_parts)

    # 检查内部数据源残留
    if "BCI" in full_text:
        # 找出位置
        matches = [(m.start(), full_text[max(0,m.start()-20):m.end()+20]) for m in re.finditer("BCI", full_text)]
        issues.extend([f"位置{pos}: ...{ctx}..." for pos, ctx in matches[:3]])

    if "bci" in full_text.lower():
        matches = [(m.start(), full_text[max(0,m.start()-20):m.end()+20]) for m in re.finditer("bci", full_text, re.IGNORECASE)]
        issues.extend([f"位置{pos}: ...{ctx}..." for pos, ctx in matches[:3] if "BCI" not in ctx])

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


if __name__ == "__main__":
    # 测试
    test_text = "BCI数据显示2026年5月销量1958万台，BCI报告指出均价创年内新高"
    result = deidentify_text(test_text)
    print(f"原文: {test_text}")
    print(f"处理后: {result}")
    print(f"校验: {validate_content({'comprehensive': {'content': result}, 'provincial': {}})}")
