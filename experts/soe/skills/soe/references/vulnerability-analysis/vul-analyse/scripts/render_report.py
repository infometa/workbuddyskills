#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_report.py —— 根据 4 个产物 JSON 渲染最终漏洞分析报告

为什么需要它：
  把统计计算放到代码里，避免 LLM 自己算错数字、漏章节、虚假打勾。
  支持 Provider 未启用时优雅降级渲染。

【发布版幂等性保证（v1.1）】
  同一份输入 JSON，配合 --freeze-time，跑 N 次输出文件**逐字节相同**：
    1. 所有"集合 → 列表"位置都用稳定排序键
    2. 高危/紧急按 (CVE+漏洞名) 聚合，IP/端口/资产去重合并
    3. 低危/信息表按 (漏洞名+CVE) 去重，展示影响主机数
    4. 字段值统一用 _fmt() 兜底（list→join, None/""→"-"）
    5. 输出文件名按 漏洞分析报告_<日期>_<厂商>.md 规范命名

输入（位于 --workdir）:
  - vulnerabilities.json   （必需，extract_vulns.py 产出）
  - unique_cves.json       （可选，dedupe_cves.py 产出）
  - knot_results.json      （可选，知识库 Provider 产出）
  - xti_results.json       （可选，威胁情报 Provider 产出）

输出:
  - 漏洞分析报告_YYYY-MM-DD_<来源>.md
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


SEVERITY_ORDER = ["紧急", "高危", "中危", "低危", "信息"]
SEVERITY_ALIASES = {
    "critical": "紧急", "严重": "紧急", "紧急": "紧急", "emergency": "紧急",
    "high": "高危", "高": "高危", "高危": "高危",
    "medium": "中危", "中": "中危", "中危": "中危",
    "low": "低危", "低": "低危", "低危": "低危",
    "info": "信息", "信息": "信息", "提示": "信息", "safe": "信息",
}
SEVERITY_EMOJI = {"紧急": "🔴", "高危": "🟠", "中危": "🟡", "低危": "🟢", "信息": "⚪"}

# 威胁等级排序权重（数字越小越严重，用于第四章稳定排序）
INTEL_SEVERITY_RANK = {
    "critical": 0, "紧急": 0,
    "high": 1, "高": 1, "高危": 1,
    "medium": 2, "中": 2, "中危": 2,
    "low": 3, "低": 3, "低危": 3,
    "none": 4,
    "unknown": 5,
}

# 解析器名称前缀 → 厂商中文标签映射（用于自动推断 --source-label）
PARSER_VENDOR_MAP = {
    "lv_meng": "绿盟RSAS",
    "nsfocus": "绿盟RSAS",
    "sxf": "深信服",
    "sangfor": "深信服",
    "xuanjing": "悬镜",
    "mingjian": "明鉴",
    "dengbao": "等保",
    "qianxin": "奇安信",
    "qax": "奇安信",
    "venustech": "启明星辰",
    "huayunan": "华云安",
    "chaitin": "长亭",
    "xray": "长亭xray",
    "dongjian": "长亭洞鉴",
    "nessus": "Nessus",
    "openvas": "OpenVAS",
    "trivy": "Trivy",
    "grype": "Grype",
    "snyk": "Snyk",
    "generic": "通用格式",
}

# 厂商标签的合法字符集（用于文件名 slug，避免空格 / 斜杠 / 特殊符号）
_VENDOR_SLUG_RE = re.compile(r"[^\w\u4e00-\u9fff]+")


# ────────────────────────── 通用工具 ──────────────────────────

def _fmt(val: Any, sep: str = "；", placeholder: str = "-") -> str:
    """统一字段渲染：

    - None / "" / [] / "无" → 占位符
    - list / tuple → 用 sep 拼接（去除空元素）
    - 字符串形式的 Python list 字面量（如 "['a', 'b']"）→ 解析后拼接
    - 其它 → str()
    """
    if val is None:
        return placeholder
    if isinstance(val, (list, tuple)):
        items = [str(x).strip() for x in val if x not in (None, "")]
        return sep.join(items) if items else placeholder
    s = str(val).strip()
    if not s or s in ("无", "None", "nan", "NaN"):
        return placeholder
    # 上游解析器有时会把 list 用 str() 直接序列化，得到形如 "['a', 'b']" 的字符串
    # 这里安全还原（仅当首尾为方括号时）
    if len(s) >= 2 and s[0] == "[" and s[-1] == "]":
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple)):
                items = [str(x).strip() for x in parsed if x not in (None, "")]
                return sep.join(items) if items else placeholder
        except (ValueError, SyntaxError):
            pass
    return s


def _join_unique(items: Iterable[str], sep: str = ";") -> str:
    """对字符串集合稳定去重并以分隔符拼接（保留首次出现顺序）。"""
    out: list[str] = []
    seen: set[str] = set()
    for raw in items:
        if raw is None:
            continue
        # 兼容 "10.0.17.6;10.0.17.136" 这种已聚合的字段
        for piece in re.split(r"[;,；，\s]+", str(raw)):
            p = piece.strip()
            if p and p not in seen:
                seen.add(p)
                out.append(p)
    return sep.join(out) if out else "-"


def _stable_vuln_key(v: dict) -> tuple:
    """漏洞稳定排序键：CVE > 漏洞名 > IP > 端口。"""
    return (
        v.get("CVE编号") or "ZZZ",
        v.get("漏洞名称") or "",
        v.get("风险域名/IP") or "",
        str(v.get("风险端口") or ""),
    )


def _stable_intel_key(r: dict) -> tuple:
    """情报记录稳定排序：威胁等级 → CVSS（高→低）→ CVE。"""
    level = (r.get("threat_level") or r.get("威胁等级") or "unknown")
    try:
        cvss = -float(r.get("cvss_score") or r.get("CVSS评分") or 0)
    except (TypeError, ValueError):
        cvss = 0.0
    return (
        INTEL_SEVERITY_RANK.get(str(level).lower(), 9),
        cvss,
        str(r.get("cve_id") or "ZZZ"),
    )


def _slug_vendor(label: str) -> str:
    """厂商标签 → 文件名 slug：保留中文/英文/数字，其余字符替换为下划线。"""
    if not label:
        return "未知来源"
    s = _VENDOR_SLUG_RE.sub("_", label.strip())
    return s.strip("_") or "未知来源"


def infer_source_label(vulns_data: dict) -> str:
    """从 vulnerabilities.json 的 parser / sub_parsers 字段自动推断来源厂商标签。

    优先级：sub_parsers（取出现频率最高的前缀）> parser 本身。
    当 --source-label 未传入时自动调用。
    """
    if not isinstance(vulns_data, dict):
        return ""

    parser_names: list[str] = []
    sub_parsers = vulns_data.get("sub_parsers", [])
    if isinstance(sub_parsers, list) and sub_parsers:
        parser_names.extend(sub_parsers)
    else:
        main_parser = vulns_data.get("parser", "")
        if main_parser and main_parser != "zip_aggregator":
            parser_names.append(main_parser)

    if not parser_names:
        return ""

    prefix_counts: Counter = Counter()
    for name in parser_names:
        for prefix in PARSER_VENDOR_MAP:
            if name.startswith(prefix) or prefix in name:
                prefix_counts[prefix] += 1
                break

    if not prefix_counts:
        return ""

    # most_common 在并列时按插入顺序，PARSER_VENDOR_MAP 是有序 dict → 稳定
    top_prefix = prefix_counts.most_common(1)[0][0]
    return PARSER_VENDOR_MAP[top_prefix]


def normalize_severity(raw: str) -> str:
    if not raw:
        return "信息"
    key = str(raw).strip().lower()
    return SEVERITY_ALIASES.get(key, "信息")


def safe_load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️  读取 {path} 失败: {e}", file=sys.stderr)
        return None


# ────────────────────────── 聚合逻辑 ──────────────────────────

def merge_vulns_by_cve(items: list[dict]) -> list[dict]:
    """按 (CVE编号 or 漏洞名称) 聚合漏洞记录：

    - 多个 IP/端口/资产 → 用 ; 拼接去重
    - 其它字段（描述/CVSS/类型/发现时间）取首条
    - 返回顺序：按 _stable_vuln_key 稳定排序
    """
    if not items:
        return []

    buckets: dict[str, list[dict]] = {}
    for v in items:
        cve = (v.get("CVE编号") or "").strip()
        name = (v.get("漏洞名称") or "").strip()
        # 同 CVE 必合并；无 CVE 时按漏洞名称合并
        key = cve if cve else f"__no_cve__::{name}"
        buckets.setdefault(key, []).append(v)

    merged: list[dict] = []
    for group in buckets.values():
        # 组内按稳定键排序，确保首条选择稳定
        group_sorted = sorted(group, key=_stable_vuln_key)
        base = dict(group_sorted[0])
        for fld in ("风险域名/IP", "风险端口", "影响资产"):
            base[fld] = _join_unique((g.get(fld) for g in group_sorted))
        merged.append(base)

    merged.sort(key=_stable_vuln_key)
    return merged


def aggregate_low_table(items: list[dict]) -> list[tuple[str, str, int]]:
    """低危/信息表按 (漏洞名称, CVE) 聚合，返回 (name, cve, host_count)。

    排序：影响主机数降序 → 漏洞名升序 → CVE 升序（稳定）
    """
    agg: dict[tuple[str, str], set[str]] = {}
    for v in items:
        name = (v.get("漏洞名称") or "-").strip() or "-"
        cve = (v.get("CVE编号") or "-").strip() or "-"
        host = (v.get("风险域名/IP") or "").strip()
        agg.setdefault((name, cve), set())
        if host:
            agg[(name, cve)].add(host)

    rows = [(name, cve, len(hosts)) for (name, cve), hosts in agg.items()]
    rows.sort(key=lambda x: (-x[2], x[0], x[1]))
    return rows


# ────────────────────────── 章节渲染 ──────────────────────────

def build_severity_distribution(vulns: list[dict]) -> tuple[Counter, int]:
    counter: Counter = Counter()
    for v in vulns:
        sev = normalize_severity(v.get("风险等级", ""))
        counter[sev] += 1
    return counter, sum(counter.values())


def render_severity_chart(counter: Counter, total: int) -> str:
    lines = []
    for sev in SEVERITY_ORDER:
        cnt = counter.get(sev, 0)
        ratio = (cnt / total * 100) if total else 0
        bar_len = int(ratio / 3)  # 每 3% = 1 格
        bar = "█" * max(bar_len, 1 if cnt else 0)
        lines.append(f"{sev:<3s} {bar:<35s} {cnt:>5d} ({ratio:>5.1f}%)")
    return "```\n" + "\n".join(lines) + "\n```"


def render_provider_section(
    results: Optional[dict],
    enabled: bool,
    intro: str,
    table_header: str,
    row_renderer,
    sort_key=None,
) -> str:
    """渲染一个 Provider 章节，未启用时显示提示。"""
    if not enabled or not results or results.get("provider_disabled"):
        return f"{intro}\n\n> ⏭️ **本章节未启用**：Provider 未在 `providers.yaml` 中启用，跳过查询。\n"

    rows = list(results.get("results", []))
    if sort_key is not None:
        rows.sort(key=sort_key)

    queried = results.get("queried_count", 0)
    hit = results.get("hit_count", 0)
    rate_raw = results.get("hit_rate")
    if isinstance(rate_raw, (int, float)):
        rate = rate_raw
    else:
        rate = (hit / queried) if queried else 0.0

    body = [intro, "", f"**查询统计**：共查询 {queried} 个 CVE，命中 {hit} 个，命中率 {rate * 100:.1f}%。", ""]
    if rows:
        body.append(table_header)
        for r in rows:
            body.append(row_renderer(r))
    else:
        body.append("> （Provider 已启用但本次未查询到任何记录）")
    return "\n".join(body)


def kb_row(r: dict) -> str:
    cve = _fmt(r.get("cve_id"))
    name = _fmt(r.get("漏洞名称") or r.get("vuln_name"))
    status = _fmt(r.get("fix_status") or r.get("修复状态")
                  or ("已找到" if r.get("found") else "未找到"))
    links = r.get("ticket_links") or r.get("关联单据") or []
    if isinstance(links, list):
        link_str = "<br>".join(str(x) for x in links if x) or "-"
    else:
        link_str = str(links) or "-"
    return f"| {name} | {cve} | {status} | {link_str} |"


def intel_row(r: dict) -> str:
    cve = _fmt(r.get("cve_id"))
    name = _fmt(r.get("漏洞名称") or r.get("vuln_name"))
    cvss = _fmt(r.get("cvss_score") or r.get("CVSS评分"))
    has_exploit = r.get("has_public_exploit")
    exploit_str = "✅ 有" if has_exploit else ("❌ 无" if has_exploit is False else "-")
    level = _fmt(r.get("threat_level") or r.get("威胁等级"))
    return f"| {name} | {cve} | {cvss} | {exploit_str} | {level} |"


def render_per_vuln_analysis(vulns: list[dict],
                             kb_results: Optional[dict],
                             intel_results: Optional[dict]) -> str:
    """渲染第五章：逐条漏洞分析。"""
    kb_by_cve = {r.get("cve_id"): r
                 for r in (kb_results or {}).get("results", []) if r.get("cve_id")}
    intel_by_cve = {r.get("cve_id"): r
                    for r in (intel_results or {}).get("results", []) if r.get("cve_id")}

    grouped: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for v in vulns:
        sev = normalize_severity(v.get("风险等级", ""))
        grouped[sev].append(v)

    sections = []

    # 紧急 / 高危：按 CVE 聚合后逐条详细
    for sev in ("紧急", "高危"):
        items = merge_vulns_by_cve(grouped[sev])
        if not items:
            continue
        sections.append(f"### 5.{SEVERITY_ORDER.index(sev) + 1} {sev}漏洞（共 {len(items)} 条）\n")
        for v in items:
            cve = (v.get("CVE编号") or "").strip()
            kb_info = kb_by_cve.get(cve, {}) if cve else {}
            intel_info = intel_by_cve.get(cve, {}) if cve else {}
            sections.append(f"#### {_fmt(v.get('漏洞名称'), placeholder='未知漏洞')}\n")
            sections.append("| 属性 | 信息 |")
            sections.append("|------|------|")
            sections.append(f"| CVE 编号 | {_fmt(cve)} |")
            sections.append(f"| 风险等级 | {SEVERITY_EMOJI.get(sev, '')} {sev} |")
            sections.append(f"| CVSS 评分 | {_fmt(v.get('CVSS评分'))} |")
            sections.append(f"| 漏洞类型 | {_fmt(v.get('漏洞类型'))} |")
            sections.append(f"| 影响资产 | {_fmt(v.get('影响资产'))} |")
            sections.append(f"| 风险IP/域名 | {_fmt(v.get('风险域名/IP'))} |")
            sections.append(f"| 风险端口 | {_fmt(v.get('风险端口'))} |")
            sections.append(f"| 发现时间 | {_fmt(v.get('发现时间'))} |")
            sections.append("")
            sections.append(f"**漏洞描述**: {_fmt(v.get('漏洞描述'), sep=' ')}\n")
            sections.append(
                f"**知识库历史修复情况**: "
                f"{_fmt(kb_info.get('fix_status'), placeholder='未查询/未命中') if kb_info else '未启用'}\n"
            )
            sections.append(
                f"**威胁情报**: "
                f"{_fmt(intel_info.get('fix_advice'), placeholder='未查询/未命中') if intel_info else '未启用'}\n"
            )
            sections.append(f"**修复建议**: {_fmt(v.get('修复建议'), sep=' ')}\n")
            sections.append("---\n")

    # 中危：表格简要（按稳定键排序）
    if grouped["中危"]:
        med_items = sorted(grouped["中危"], key=_stable_vuln_key)
        sections.append(f"### 5.3 中危漏洞（共 {len(med_items)} 条）\n")
        sections.append("| 漏洞名称 | CVE 编号 | 影响资产 | 风险IP | 修复建议（节选） |")
        sections.append("|---------|---------|---------|--------|----------------|")
        for v in med_items:
            advice = _fmt(v.get("修复建议"), sep=" ")
            advice = advice[:50] if advice != "-" else "-"
            sections.append(
                f"| {_fmt(v.get('漏洞名称'))} | {_fmt(v.get('CVE编号'))} "
                f"| {_fmt(v.get('影响资产'))} | {_fmt(v.get('风险域名/IP'))} | {advice} |"
            )
        sections.append("")

    # 低危/信息：按 (漏洞名+CVE) 聚合 + 主机数列
    low_items = grouped["低危"] + grouped["信息"]
    if low_items:
        agg_rows = aggregate_low_table(low_items)
        total_unique = len(agg_rows)
        sections.append(
            f"### 5.4 低危/信息漏洞（原始 {len(low_items)} 条 → "
            f"按漏洞类型聚合 {total_unique} 类）\n"
        )
        sections.append("| 漏洞名称 | CVE 编号 | 影响主机数 |")
        sections.append("|---------|---------|----------|")
        max_rows = 50
        for name, cve, host_count in agg_rows[:max_rows]:
            sections.append(f"| {name} | {cve} | {host_count} |")
        if total_unique > max_rows:
            sections.append(
                f"| ...（共 {total_unique} 类，仅展示前 {max_rows} 类，按主机数降序） | | |"
            )
        sections.append("")

    return "\n".join(sections) if sections else "（无漏洞数据）"


def render_priority(vulns: list[dict]) -> str:
    """渲染第六章：修复优先级。同 CVE 多 IP 已聚合。"""
    grouped: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for v in vulns:
        grouped[normalize_severity(v.get("风险等级", ""))].append(v)

    # 紧急/高危聚合后展示；中危/低危用原始数量统计
    crit_merged = merge_vulns_by_cve(grouped["紧急"])
    high_merged = merge_vulns_by_cve(grouped["高危"])
    med_count = len(grouped["中危"])
    low_count = len(grouped["低危"]) + len(grouped["信息"])

    out = []
    out.append(f"### 紧急修复（建议 24 小时内，共 {len(crit_merged)} 条）")
    for v in crit_merged[:20]:
        out.append(
            f"- [{_fmt(v.get('CVE编号'))}] {_fmt(v.get('漏洞名称'))} "
            f"@ {_fmt(v.get('风险域名/IP'))}"
        )
    out.append(f"\n### 高优先级（建议 7 天内，共 {len(high_merged)} 条）")
    for v in high_merged[:20]:
        out.append(
            f"- [{_fmt(v.get('CVE编号'))}] {_fmt(v.get('漏洞名称'))} "
            f"@ {_fmt(v.get('风险域名/IP'))}"
        )
    out.append(f"\n### 中优先级（建议 30 天内，共 {med_count} 条）")
    out.append(f"\n### 低优先级（常规迭代修复，共 {low_count} 条）")
    return "\n".join(out)


def render_summary(counter: Counter, total: int,
                   kb_enabled: bool, intel_enabled: bool,
                   crit_merged: int, high_merged: int) -> str:
    if total == 0:
        return "本次扫描未发现有效漏洞条目，建议复核扫描器配置和扫描范围。"
    parts = [f"本次共发现 **{total}** 条漏洞。"]
    if crit_merged:
        parts.append(f"其中 **{crit_merged} 类紧急/严重风险**亟需 24h 内处置。")
    if high_merged:
        parts.append(f"另有 **{high_merged} 类高危**应在 7 天内排期修复。")
    if not (kb_enabled or intel_enabled):
        parts.append("⚠️ 本次未启用知识库与威胁情报 Provider，建议配置后重新分析以获取修复历史与公开 PoC 信息。")
    elif not kb_enabled:
        parts.append("⚠️ 知识库 Provider 未启用，无法判断历史修复状态。")
    elif not intel_enabled:
        parts.append("⚠️ 威胁情报 Provider 未启用，无法判断公开利用情况。")
    parts.append("详细修复建议详见第六章。")
    return " ".join(parts)


# ────────────────────────── 主渲染函数 ──────────────────────────

def render(workdir: Path, output: Path,
           source_label: str = "",
           freeze_time: Optional[str] = None) -> dict:
    vulns_data = safe_load_json(workdir / "vulnerabilities.json")
    if not vulns_data:
        print("❌ 必需文件 vulnerabilities.json 不存在或解析失败", file=sys.stderr)
        sys.exit(1)
    vulns = vulns_data.get("vulnerabilities", []) if isinstance(vulns_data, dict) else []
    source = vulns_data.get("source", "") if isinstance(vulns_data, dict) else ""

    # 自动推断来源标签
    if not source_label:
        source_label = infer_source_label(vulns_data)
        if source_label:
            print(f"📌 自动推断来源: {source_label}（从 parser/sub_parsers 字段）")

    unique_data = safe_load_json(workdir / "unique_cves.json") or {}
    kb_data = safe_load_json(workdir / "knot_results.json")
    intel_data = safe_load_json(workdir / "xti_results.json")

    kb_enabled = bool(kb_data and not kb_data.get("provider_disabled"))
    intel_enabled = bool(intel_data and not intel_data.get("provider_disabled"))

    # 一、概览统计
    counter, total = build_severity_distribution(vulns)
    cve_count = unique_data.get("unique_cves", 0)
    asset_count = len({v.get("风险域名/IP", "") for v in vulns if v.get("风险域名/IP")})

    # 计算合并后的高危/紧急数（用于总结）
    grouped_for_summary: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for v in vulns:
        grouped_for_summary[normalize_severity(v.get("风险等级", ""))].append(v)
    crit_merged_count = len(merge_vulns_by_cve(grouped_for_summary["紧急"]))
    high_merged_count = len(merge_vulns_by_cve(grouped_for_summary["高危"]))

    # 渲染各章节
    chart = render_severity_chart(counter, total)

    kb_section = render_provider_section(
        results=kb_data,
        enabled=kb_enabled,
        intro="> 以下信息来源于配置的知识库 Provider 查询结果。",
        table_header=("| 漏洞名称 | CVE 编号 | 历史修复状态 | 相关需求/缺陷单链接 |\n"
                      "|---------|---------|-------------|-------------------|"),
        row_renderer=kb_row,
        sort_key=lambda r: (str(r.get("cve_id") or "ZZZ"),
                            str(r.get("漏洞名称") or "")),
    )

    intel_section = render_provider_section(
        results=intel_data,
        enabled=intel_enabled,
        intro="> 以下信息来源于配置的威胁情报 Provider，仅针对知识库未命中的漏洞。",
        table_header=("| 漏洞名称 | CVE 编号 | CVSS | 是否有公开利用 | 威胁等级 |\n"
                      "|---------|---------|------|--------------|---------|"),
        row_renderer=intel_row,
        sort_key=_stable_intel_key,
    )

    per_vuln = render_per_vuln_analysis(vulns, kb_data, intel_data)
    priority = render_priority(vulns)
    summary = render_summary(counter, total, kb_enabled, intel_enabled,
                             crit_merged_count, high_merged_count)

    gen_time = freeze_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 拼装最终报告
    report = f"""# 漏洞分析报告

---

**报告生成时间**: {gen_time}
**分析来源**: {source_label or Path(source).name or "（未知）"}
**生成工具**: vul-analyse Skill v1.1.0

---

## 一、概览统计

| 统计项 | 数值 |
|--------|------|
| 漏洞总数 | {total} |
| 紧急/严重 | {counter.get('紧急', 0)} |
| 高危 | {counter.get('高危', 0)} |
| 中危 | {counter.get('中危', 0)} |
| 低危 | {counter.get('低危', 0)} |
| 信息 | {counter.get('信息', 0)} |
| 涉及 CVE 编号数 | {cve_count} |
| 涉及资产/IP 数 | {asset_count} |
| 知识库 Provider | {"✅ 已启用" if kb_enabled else "⏭️ 未启用"} |
| 情报 Provider | {"✅ 已启用" if intel_enabled else "⏭️ 未启用"} |

> 说明：高危/紧急逐条分析按 (CVE 编号 + 漏洞名称) 聚合展示，同一漏洞在多 IP 出现时合并为一行（IP/端口/资产用 `;` 拼接）。

## 二、风险等级分布

{chart}

## 三、知识库历史修复情况

{kb_section}

## 四、威胁情报信息

{intel_section}

## 五、逐条漏洞分析

{per_vuln}

## 六、修复优先级建议

{priority}

## 七、总结

{summary}

---

*本报告由 vul-analyse Skill 自动生成，统计数字均由代码计算。请结合业务实际情况评估修复优先级。*
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "report_path": str(output),
        "total_vulns": total,
        "report_chars": len(report),
        "kb_enabled": kb_enabled,
        "intel_enabled": intel_enabled,
        "vendor": source_label,
    }


def resolve_output_path(args) -> tuple[Path, str]:
    """根据 CLI 参数计算最终输出路径，返回 (path, vendor_label)。

    强制规范：仅支持 --output-dir，文件名按 漏洞分析报告_<日期>_<厂商>.md 自动生成。
    （v1.1 起移除 --output，避免自由命名破坏一致性。）
    """
    if not args.output_dir:
        raise SystemExit(
            "❌ 必须指定 --output-dir <目录>。"
            "v1.1 起移除 --output 自由命名，文件名强制为 漏洞分析报告_<日期>_<厂商>.md"
        )

    # 推断厂商
    vulns_data = safe_load_json(args.workdir / "vulnerabilities.json") or {}
    vendor = args.source_label or infer_source_label(vulns_data) or "未知来源"
    vendor_slug = _slug_vendor(vendor)

    date_str = (args.freeze_time or datetime.now().strftime("%Y-%m-%d"))[:10]
    fname = f"漏洞分析报告_{date_str}_{vendor_slug}.md"
    return args.output_dir / fname, vendor


def main() -> int:
    # allow_abbrev=False：禁用前缀匹配，避免 --output 被错误识别为 --output-dir
    # 这样 AI 若误写 --output 会立即报错，而不是悄悄当成 --output-dir 跑过
    p = argparse.ArgumentParser(
        description="渲染漏洞分析报告（v1.1 发布版）",
        allow_abbrev=False,
    )
    p.add_argument("--workdir", type=Path, required=True, help="包含 4 个 JSON 产物的目录")
    p.add_argument("--output-dir", type=Path, required=True,
                   help="输出目录，文件名按规范自动生成：漏洞分析报告_<日期>_<厂商>.md")
    p.add_argument("--source-label", type=str, default="",
                   help="报告中显示的来源标签（不传则从 parser 自动推断）")
    p.add_argument("--freeze-time", type=str, default=None,
                   help="冻结生成时间（格式 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD），用于幂等性回归测试")
    p.add_argument("--template", type=Path, default=None,
                   help="模板文件（保留参数，当前用内置模板）")
    args = p.parse_args()

    output_path, _ = resolve_output_path(args)

    result = render(args.workdir, output_path, args.source_label, args.freeze_time)
    print(f"✅ 报告已生成: {result['report_path']}")
    print(f"   漏洞总数: {result['total_vulns']}")
    print(f"   字数: {result['report_chars']}")
    print(f"   来源厂商: {result['vendor'] or '（未推断）'}")
    print(f"   知识库 Provider: {'启用' if result['kb_enabled'] else '未启用'}")
    print(f"   情报 Provider:   {'启用' if result['intel_enabled'] else '未启用'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
