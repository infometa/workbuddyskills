#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedupe_cves.py —— 基于 CVE ID 对漏洞记录去重，为 MCP 查询生成最小工作集

为什么需要去重：
  同一个 CVE 往往出现在多台主机、多份子报告中，如果不去重直接调 MCP，会：
    - 浪费 MCP 配额（成本高）
    - 响应慢（1857 条漏洞 vs 几十个唯一 CVE）
    - 引入幻觉风险（Agent 为了节省时间而降级）
  所以本脚本把 vulnerabilities.json 展开 → 抽 CVE 编号 → 去重 → 产出查询清单。

输入: vulnerabilities.json （extract_vulns.py 的产出）
输出: unique_cves.json

产出结构:
{
  "total_vulns": 1857,
  "with_cve": 320,
  "without_cve": 1537,
  "unique_cves": 87,
  "cve_list": [
    {
      "cve_id": "CVE-2025-8194",
      "漏洞名称": "CPython 安全漏洞",
      "风险等级": "high",
      "CVSS评分": "7.5",
      "affected_records": [0, 15, 203, ...],   // 持有此 CVE 的漏洞在原数组中的索引
      "affected_count": 3
    },
    ...
  ],
  "vulns_without_cve": [                        // 无 CVE 的漏洞，按漏洞名称聚合
    {
      "漏洞名称": "可通过HTTP(S)获取远端WWW服务信息",
      "风险等级": "low",
      "affected_records": [1, 2, 3, ...],
      "affected_count": 637,
      "search_keyword": "可通过HTTP(S)获取远端WWW服务信息"   // 供 MCP 名称查询使用
    },
    ...
  ]
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# CVE 编号规范化正则（匹配大小写、空格、全角破折号）
CVE_PATTERN = re.compile(r"CVE[-–—\s]?(\d{4})[-–—\s]?(\d+)", re.IGNORECASE)


def normalize_cve(raw: str) -> str | None:
    """把各种格式的 CVE 字符串归一化为 CVE-YYYY-NNNN。"""
    if not raw or not isinstance(raw, str):
        return None
    m = CVE_PATTERN.search(raw.strip())
    if not m:
        return None
    return f"CVE-{m.group(1)}-{m.group(2)}"


def extract_cves(cve_field: Any) -> list[str]:
    """从漏洞记录的 CVE 字段提取一个或多个规范化 CVE ID。

    兼容场景：
      - 字符串 "CVE-2021-44228"
      - 字符串 "CVE-2021-44228; CVE-2021-45046"
      - 列表 ["CVE-2021-44228", ...]
      - 空 / None / "无" / "-"
    """
    if not cve_field:
        return []
    if isinstance(cve_field, list):
        raw_parts = cve_field
    else:
        # 字符串：按常见分隔符拆分
        raw_parts = re.split(r"[;,；，\s]+", str(cve_field))
    out: list[str] = []
    for part in raw_parts:
        norm = normalize_cve(str(part))
        if norm:
            out.append(norm)
    return out


def severity_rank(sev: str) -> int:
    """风险等级排序权重（数字越小越严重，用于稳定排序）。"""
    m = {
        "critical": 0, "紧急": 0, "严重": 0,
        "high": 1, "高危": 1, "高": 1,
        "medium": 2, "中危": 2, "中": 2,
        "low": 3, "低危": 3, "低": 3,
        "info": 4, "信息": 4, "提示": 4,
    }
    return m.get(str(sev).lower().strip(), 5)


def build_search_keyword(name: str) -> str:
    """为无 CVE 漏洞构造 MCP 查询关键词，去除版本号、协议前缀等噪声。"""
    if not name:
        return ""
    kw = name.strip()
    # 去掉常见括号补充说明
    kw = re.sub(r"[\(（].*?[\)）]", "", kw)
    # 去掉版本号（如 1.2.3, v2.0, Apache 2.4.1）
    kw = re.sub(r"\b[vV]?\d+(\.\d+){1,3}\b", "", kw)
    # 去掉【原理扫描】等方括号标注
    kw = re.sub(r"[\[【].*?[\]】]", "", kw)
    # 压缩多余空格
    kw = re.sub(r"\s+", " ", kw).strip()
    return kw or name


def dedupe(vulns: list[dict]) -> dict:
    cve_buckets: dict[str, dict] = {}
    no_cve_buckets: dict[str, dict] = defaultdict(lambda: {
        "affected_records": [],
        "风险等级": "",
        "风险等级_rank": 99,
    })

    with_cve_count = 0
    without_cve_count = 0

    for idx, v in enumerate(vulns):
        cve_raw = v.get("CVE编号") or v.get("cve_id") or v.get("cve") or ""
        cves = extract_cves(cve_raw)
        name = str(v.get("漏洞名称") or v.get("name") or v.get("vuln_name") or "未知漏洞").strip()
        sev = str(v.get("风险等级") or v.get("severity") or "").strip()
        cvss = str(v.get("CVSS评分") or v.get("cvss") or "").strip()

        if cves:
            with_cve_count += 1
            for cve in cves:
                bucket = cve_buckets.setdefault(cve, {
                    "cve_id": cve,
                    "漏洞名称": name,
                    "风险等级": sev,
                    "CVSS评分": cvss,
                    "affected_records": [],
                })
                bucket["affected_records"].append(idx)
                # 取最严重等级作为代表
                if severity_rank(sev) < severity_rank(bucket["风险等级"]):
                    bucket["风险等级"] = sev
                    bucket["漏洞名称"] = name
                # 取最高 CVSS
                try:
                    if cvss and float(cvss) > float(bucket["CVSS评分"] or 0):
                        bucket["CVSS评分"] = cvss
                except ValueError:
                    pass
        else:
            without_cve_count += 1
            key = name  # 按漏洞名称聚合
            bucket = no_cve_buckets[key]
            bucket["affected_records"].append(idx)
            if severity_rank(sev) < bucket["风险等级_rank"]:
                bucket["风险等级"] = sev
                bucket["风险等级_rank"] = severity_rank(sev)

    # 整理 CVE 列表（按严重度排序）
    cve_list = []
    for cve_id, bucket in cve_buckets.items():
        bucket["affected_count"] = len(bucket["affected_records"])
        cve_list.append(bucket)
    cve_list.sort(key=lambda b: (severity_rank(b["风险等级"]), -b["affected_count"]))

    # 整理无 CVE 列表
    no_cve_list = []
    for name, bucket in no_cve_buckets.items():
        no_cve_list.append({
            "漏洞名称": name,
            "风险等级": bucket["风险等级"],
            "affected_records": bucket["affected_records"],
            "affected_count": len(bucket["affected_records"]),
            "search_keyword": build_search_keyword(name),
        })
    no_cve_list.sort(key=lambda b: (severity_rank(b["风险等级"]), -b["affected_count"]))

    return {
        "total_vulns": len(vulns),
        "with_cve": with_cve_count,
        "without_cve": without_cve_count,
        "unique_cves": len(cve_list),
        "unique_names_without_cve": len(no_cve_list),
        "cve_list": cve_list,
        "vulns_without_cve": no_cve_list,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="对漏洞记录按 CVE ID 去重")
    parser.add_argument("input", type=Path, help="vulnerabilities.json 路径")
    parser.add_argument("-o", "--output", type=Path, required=True, help="输出 unique_cves.json 路径")
    parser.add_argument("--top", type=int, default=0, help="仅输出前 N 个 CVE（0 表示全部）")
    parser.add_argument("--severity", choices=["critical", "high", "medium", "low", "all"],
                        default="all", help="仅保留指定等级及以上的 CVE")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ 输入文件不存在: {args.input}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ JSON 解析失败: {e}", file=sys.stderr)
        return 1

    vulns = data.get("vulnerabilities") if isinstance(data, dict) else data
    if not isinstance(vulns, list):
        print("❌ 输入不是预期的漏洞数组结构", file=sys.stderr)
        return 1

    result = dedupe(vulns)

    # 按严重度过滤
    if args.severity != "all":
        threshold = {"critical": 0, "high": 1, "medium": 2, "low": 3}[args.severity]
        result["cve_list"] = [c for c in result["cve_list"] if severity_rank(c["风险等级"]) <= threshold]

    # Top N 截断
    if args.top > 0:
        result["cve_list"] = result["cve_list"][: args.top]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印人类可读摘要
    print("=" * 60)
    print("CVE 去重结果")
    print("=" * 60)
    print(f"总漏洞数:       {result['total_vulns']}")
    print(f"有 CVE 编号的:   {result['with_cve']}")
    print(f"无 CVE 编号的:   {result['without_cve']}")
    print(f"唯一 CVE 数:     {result['unique_cves']}")
    print(f"无 CVE 唯一名称: {result['unique_names_without_cve']}")
    print(f"\n输出文件: {args.output}")
    print(f"\n示例：前 5 个唯一 CVE（按严重度排序）:")
    for c in result["cve_list"][:5]:
        print(f"  - {c['cve_id']:20s} [{c['风险等级']:6s}] "
              f"影响 {c['affected_count']:3d} 条 | {c['漏洞名称'][:40]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
