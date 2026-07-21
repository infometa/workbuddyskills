#!/usr/bin/env python3
"""标准报告生成器 - 把 L0 + L1 输出聚合成 HTML 综合报告

输入:
  - L0 JSONL (含资产关联结果): l0_output/*_l0_with_assets.jsonl
  - L1 案例目录 (cases/): 含 {event_id}.md 文件

输出:
  - HTML 综合报告 (含 ECharts 可视化)

报告结构 (8 段):
  1. 概要 KPI (3 卡: 总告警 / 威胁事件 / 受影响资产)
  2. 威胁类型分布 (ECharts 玫瑰图)
  3. 受影响资产清单 (按重要性排序的表格)
  4. 高危事件 Top N (按置信度排序)
  5. 跨产品关联候选 (按 attacker_ip + 时间窗聚合, 供 L2)
  6. IOC 清单 (IP / hostname / user 去重)
  7. 处置建议清单 (按威胁类型分组)
  8. 详细案例 (折叠列表)

用法:
  python3 gen_report.py \
      --l0 l0_output/yujie_l0_with_assets.jsonl l0_output/cwp_l0_full.jsonl \
      --cases l0_output/yujie_cases l0_output/cwp_cases \
      --out l0_output/soc_alert_report.html
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

# SCRIPT_DIR = skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


# ==================== 数据加载 ====================

def load_l0_records(paths: list[Path]) -> list[dict]:
    """加载多个 L0 JSONL 文件, 合并去重"""
    records = []
    seen_ids = set()
    for p in paths:
        if not p.exists():
            print(f"[WARN] L0 文件不存在: {p}", file=sys.stderr)
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # 去重: 用 source_file + row
                key = (rec.get("source_file", ""), rec.get("row", -1))
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                records.append(rec)
    return records


def load_cases(case_dirs: list[Path]) -> dict[str, dict]:
    """加载案例 .md 文件, 解析出关键字段"""
    cases = {}
    for d in case_dirs:
        if not d.exists():
            print(f"[WARN] 案例目录不存在: {d}", file=sys.stderr)
            continue
        for md_path in sorted(d.glob("*.md")):
            try:
                content = md_path.read_text(encoding="utf-8")
            except Exception:
                continue
            case = parse_case_md(content, md_path.stem)
            cases[md_path.stem] = case
    return cases


def parse_case_md(content: str, case_id: str) -> dict:
    """从 .md 文件解析出结构化字段 (用于报告聚合)"""
    case = {
        "id": case_id,
        "content": content,
        "product": "yujie" if case_id.startswith("yujie") else "cwp" if case_id.startswith("cwp") else "unknown",
        "threat_type": None,
        "ttp": None,
        "confidence": 0.0,
        "kill_chain_phase": None,
        "rule_name": None,
        "src_ip": None,
        "dst_ip": None,
        "real_attacker_ip": None,
        "real_victim_ip": None,
        "host_ip": None,
        "hostname": None,
        "user": None,
        "event_time": None,
        "iocs": [],
        "correlation_hints": {},
    }

    # 提取威胁类型
    m = re.search(r"\*\*威胁类型\*\*:\s*(.+)", content)
    if m:
        case["threat_type"] = m.group(1).strip()

    # 提取 TTP
    m = re.search(r"\*\*TTP\*\*:\s*(\S+)", content)
    if m:
        case["ttp"] = m.group(1).strip()

    # 提取置信度
    m = re.search(r"\*\*置信度\*\*:\s*([\d.]+)", content)
    if m:
        try:
            case["confidence"] = float(m.group(1))
        except ValueError:
            pass

    # 提取 kill chain
    m = re.search(r"\*\*Kill Chain 阶段\*\*:\s*(.+)", content)
    if m:
        case["kill_chain_phase"] = m.group(1).strip()

    # 提取 IP (从各种段)
    # 优先从 L1 案例 markdown 的"基础信息"/"网络五元组"段提
    m = re.search(r"\| 源 IP \| ([^|]+) \|", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "-":
            case["src_ip"] = ip

    m = re.search(r"\| 目的 IP:端口 \| ([^:]+):", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "-":
            case["dst_ip"] = ip

    m = re.search(r"\| 主机 \| ([^|]+) \|", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "?" and ip != "-":
            case["host_ip"] = ip

    # 御界: 真实 (NAT 还原)
    m = re.search(r"\*\*真实 \(NAT 还原\)\*\* \| ([^:]+):", content)
    if m:
        parts = m.group(1).strip().split()
        if parts:
            case["real_attacker_ip"] = parts[0]

    # 提取 user
    m = re.search(r"\| 用户 \| ([^|]+) \|", content)
    if m:
        u = m.group(1).strip()
        if u and u != "-":
            case["user"] = u

    # 提取 hostname
    m = re.search(r"\| 主机名 \| ([^|]+) \|", content)
    if m:
        h = m.group(1).strip()
        if h and h != "-":
            case["hostname"] = h

    # 提取时间
    m = re.search(r"\| 事件时间 \| ([^|]+) \|", content)
    if m:
        case["event_time"] = m.group(1).strip()

    # 提取规则名
    m = re.search(r"\| 告警名称 \| ([^|]+) \|", content)
    if not m:
        m = re.search(r"\| 规则 \| ([^(]+)", content)
    if m:
        case["rule_name"] = m.group(1).strip()

    # 收集 IOC
    if case["real_attacker_ip"] and case["real_attacker_ip"] != "-":
        case["iocs"].append(("ip", case["real_attacker_ip"]))
    elif case["src_ip"] and case["src_ip"] != "-":
        case["iocs"].append(("ip", case["src_ip"]))
    if case["dst_ip"] and case["dst_ip"] != "-":
        case["iocs"].append(("ip", case["dst_ip"]))
    if case["user"] and case["user"] != "-":
        case["iocs"].append(("user", case["user"]))

    return case


# ==================== 报告聚合 ====================

def aggregate_stats(records: list[dict], cases: dict[str, dict]) -> dict:
    """聚合统计: 总告警 / 威胁事件 / 受影响资产 / 威胁分布 / IOC"""
    stats = {
        "total_alerts": len(records),
        "total_threats": len(cases),
        "high_confidence_threats": sum(1 for c in cases.values() if c["confidence"] >= 0.7),
        "threat_by_type": Counter(),
        "threat_by_product": Counter(),
        "threat_by_ttp": Counter(),
        "affected_assets": {},   # ip -> asset dict (从 L0)
        "iocs_ips": Counter(),
        "iocs_users": Counter(),
        "iocs_hostnames": Counter(),
        "top_threats": [],       # Top N 高置信度威胁
        "correlation_candidates": defaultdict(list),  # attacker_ip -> [case_id, ...]
        "asset_coverage_appid": {},   # appid -> {alerts, asset_count, status}
        "asset_coverage_vpcid": {},   # vpcid -> {alerts, asset_count, status}
    }

    # 1. 从 L0 收集受影响资产 + appid/vpcid 覆盖
    for rec in records:
        asset_info = rec.get("asset", {}) or {}
        for key in ("src_asset", "victim_asset", "dst_asset"):
            a = asset_info.get(key)
            if a and a.get("ip"):
                stats["affected_assets"][a["ip"]] = a

        # 资产覆盖: appid (主机安全) - 同时记录受害 IP 明细
        parsed = rec.get("parsed", {}) or {}
        appid = parsed.get("appid")
        if appid:
            if appid not in stats["asset_coverage_appid"]:
                stats["asset_coverage_appid"][appid] = {
                    "alerts": 0, "asset_count": 0, "status": "unknown",
                    "victim_ips": {},  # ip -> {"alerts": int, "asset": dict|None}
                }
            stats["asset_coverage_appid"][appid]["alerts"] += 1
            # 从 L0 的 asset 信息里看是否匹配到了
            victim_ip = parsed.get("host_ip") or parsed.get("dst_ip")
            va = asset_info.get("victim_asset")
            if va or asset_info.get("src_asset"):
                stats["asset_coverage_appid"][appid]["asset_count"] = max(
                    stats["asset_coverage_appid"][appid]["asset_count"], 1
                )
            # 累计受害 IP
            if victim_ip:
                slot = stats["asset_coverage_appid"][appid]["victim_ips"]
                if victim_ip not in slot:
                    slot[victim_ip] = {"alerts": 0, "asset": va}
                slot[victim_ip]["alerts"] += 1

        # 资产覆盖: vpcid (御界) - 同时记录受害 IP 明细
        vpcid = parsed.get("vpcid")
        if vpcid:
            key = str(vpcid)
            if key not in stats["asset_coverage_vpcid"]:
                stats["asset_coverage_vpcid"][key] = {
                    "alerts": 0, "asset_count": 0, "status": "unknown",
                    "victim_ips": {},
                }
            stats["asset_coverage_vpcid"][key]["alerts"] += 1
            victim_ip = parsed.get("real_victim_ip") or parsed.get("dst_ip") or parsed.get("asset_ip")
            va = asset_info.get("victim_asset") or asset_info.get("dst_asset") or asset_info.get("src_asset")
            if va:
                stats["asset_coverage_vpcid"][key]["asset_count"] = max(
                    stats["asset_coverage_vpcid"][key]["asset_count"], 1
                )
            if victim_ip:
                slot = stats["asset_coverage_vpcid"][key]["victim_ips"]
                if victim_ip not in slot:
                    slot[victim_ip] = {"alerts": 0, "asset": va}
                slot[victim_ip]["alerts"] += 1

    # 2. 从 cases 收集威胁分布 + IOC
    for case_id, case in cases.items():
        if case["threat_type"]:
            stats["threat_by_type"][case["threat_type"]] += 1
        stats["threat_by_product"][case["product"]] += 1
        if case["ttp"]:
            stats["threat_by_ttp"][case["ttp"]] += 1

        # IOC
        for ioc_type, ioc_val in case["iocs"]:
            if ioc_type == "ip":
                stats["iocs_ips"][ioc_val] += 1
            elif ioc_type == "user":
                stats["iocs_users"][ioc_val] += 1
        if case["hostname"]:
            stats["iocs_hostnames"][case["hostname"]] += 1

        # 跨产品关联候选
        pivot = case["real_attacker_ip"] or case["src_ip"]
        if pivot and pivot != "-":
            stats["correlation_candidates"][pivot].append(case_id)

    # 3. Top N 高置信度威胁
    stats["top_threats"] = sorted(
        cases.values(),
        key=lambda c: c["confidence"],
        reverse=True,
    )[:20]

    # 4. 跨产品关联候选 (只保留 ≥2 个事件的)
    stats["correlation_candidates"] = {
        ip: case_ids for ip, case_ids in stats["correlation_candidates"].items()
        if len(case_ids) >= 2
    }

    # 5. 资产覆盖状态标记
    for appid, info in stats["asset_coverage_appid"].items():
        if info["asset_count"] > 0:
            info["status"] = "covered"
        elif info["alerts"] > 0:
            info["status"] = "missing"
    for vpcid, info in stats["asset_coverage_vpcid"].items():
        if info["asset_count"] > 0:
            info["status"] = "covered"
        elif info["alerts"] > 0:
            info["status"] = "missing"

    return stats


# ==================== HTML 渲染 ====================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>SOC 告警分析报告 - __REPORT_TIME__</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
       background: #f5f7fa; color: #2c3e50; line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }
h1 { color: #1a73e8; margin-bottom: 8px; font-size: 28px; }
.subtitle { color: #5f6368; margin-bottom: 24px; font-size: 14px; }
section { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
section h2 { color: #1a73e8; border-left: 4px solid #1a73e8; padding-left: 12px;
             margin-bottom: 16px; font-size: 18px; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 8px; }
.kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff; padding: 20px; border-radius: 8px; text-align: center; }
.kpi-card.green { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.kpi-card.orange { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.kpi-card.red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
.kpi-value { font-size: 36px; font-weight: bold; }
.kpi-label { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart { height: 360px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f1f3f4; color: #3c4043; padding: 10px 8px; text-align: left;
     border-bottom: 2px solid #dadce0; font-weight: 600; }
td { padding: 8px; border-bottom: 1px solid #e8eaed; }
tr:hover { background: #f8f9fa; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.tag-high { background: #fee2e2; color: #991b1b; }
.tag-medium { background: #fef3c7; color: #92400e; }
.tag-low { background: #d1fae5; color: #065f46; }
.tag-critical { background: #fecaca; color: #7f1d1d; }
.tag-yujie { background: #dbeafe; color: #1e40af; }
.tag-cwp { background: #ede9fe; color: #5b21b6; }
code { font-family: "SF Mono", Monaco, Consolas, monospace; font-size: 0.9em;\n       background: #f1f3f4; color: #1a73e8; padding: 1px 6px; border-radius: 3px;\n       border: 1px solid #e8eaed; word-break: break-all; }\ndetails { background: #f8f9fa; border-radius: 6px; padding: 12px; margin-bottom: 8px; }
summary { cursor: pointer; font-weight: 600; color: #1a73e8; }
.case-content { margin-top: 12px; padding: 12px; background: #fff; border-radius: 4px;
                font-family: "SF Mono", Monaco, monospace; font-size: 12px; white-space: pre-wrap;
                max-height: 500px; overflow-y: auto; border: 1px solid #e8eaed; }
.ioc-list { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.ioc-block h3 { font-size: 14px; color: #5f6368; margin-bottom: 8px; }
.ioc-item { padding: 4px 8px; background: #f1f3f4; border-radius: 4px; margin-bottom: 4px;
            font-family: monospace; font-size: 12px; display: flex; justify-content: space-between; }
/* 段 5 攻击链卡片 */
.chain-card { background: #fff; border: 1px solid #e8eaed; border-radius: 8px;
              padding: 0; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.chain-card > summary { padding: 12px 16px; font-size: 14px; color: #1a73e8;
                        background: linear-gradient(90deg, #f8f9fa 0%, #fff 100%);
                        border-radius: 8px 8px 0 0; list-style: none; }
.chain-card > summary::-webkit-details-marker { display: none; }
.chain-card > summary::before { content: "▶ "; color: #5f6368; font-size: 10px; transition: transform 0.2s; display: inline-block; margin-right: 4px; }
.chain-card[open] > summary::before { transform: rotate(90deg); }
.chain-card[open] > summary { border-bottom: 1px solid #e8eaed; border-radius: 8px 8px 0 0; }
.chain-body { padding: 16px; }
.chain-meta { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
              margin-bottom: 12px; font-size: 12px; }
.chain-meta-item { background: #f8f9fa; padding: 6px 10px; border-radius: 4px; }
.chain-meta-item .label { color: #9aa0a6; font-size: 11px; }
.chain-meta-item .value { color: #2c3e50; font-weight: 600; margin-top: 2px; }
.chain-charts { display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; margin-top: 8px; }
.chain-charts-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 8px; }
.chain-graph { height: 320px; background: #fafbfc; border-radius: 6px; padding: 4px; }
.chain-timeline { height: 320px; background: #fafbfc; border-radius: 6px; padding: 4px; }
.chain-pie { height: 280px; background: #fafbfc; border-radius: 6px; padding: 4px; }
.chain-chart-title { font-size: 12px; color: #5f6368; padding: 4px 8px;
                     font-weight: 600; border-left: 3px solid #1a73e8; margin-bottom: 4px; }
.chain-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 8px; }
.chain-table th { background: #f1f3f4; color: #3c4043; padding: 6px 8px; text-align: left; }
.chain-table td { padding: 4px 8px; border-bottom: 1px solid #e8eaed; }
.footer { text-align: center; color: #9aa0a6; padding: 24px; font-size: 12px; }
</style>
</head>
<body>
<div class="container">

<h1>SOC 告警分析报告</h1>
<div class="subtitle">生成时间: __REPORT_TIME__ | 数据来源: __DATA_SOURCES__ | 由 soc-alert-pipeline 生成</div>

<!-- 段 1: 概要 KPI -->
<section>
<h2>1. 概要</h2>
<div class="kpi-grid">
<div class="kpi-card"><div class="kpi-value">__TOTAL_ALERTS__</div><div class="kpi-label">总告警数</div></div>
<div class="kpi-card red"><div class="kpi-value">__TOTAL_THREATS__</div><div class="kpi-label">威胁事件</div></div>
<div class="kpi-card orange"><div class="kpi-value">__HIGH_CONF_THREATS__</div><div class="kpi-label">高置信度威胁 (≥0.7)</div></div>
<div class="kpi-card green"><div class="kpi-value">__ATTACK_CHAINS__</div><div class="kpi-label">攻击链 (L2)</div></div>
<div class="kpi-card green"><div class="kpi-value">__AFFECTED_ASSETS__</div><div class="kpi-label">受影响资产</div></div>
</div>
</section>

<!-- 段 2: 威胁类型 + 产品分布 -->
<section>
<h2>2. 威胁分布</h2>
<div class="chart-row">
<div id="chart-threat-type" class="chart"></div>
<div id="chart-product" class="chart"></div>
</div>
</section>

<!-- 段 3: 受影响资产 -->
<section>
<h2>3. 受影响资产清单</h2>
<table>
<thead><tr><th>IP</th><th>主机名</th><th>层级</th><th>类型</th><th>重要性</th><th>业务系统</th><th>可用区</th><th>OS</th></tr></thead>
<tbody>__AFFECTED_ASSETS_ROWS__</tbody>
</table>
</section>

<!-- 段 3.5: 资产覆盖情况 -->
<section>
<h2>3.5 资产覆盖情况 (按租户/VPC)</h2>
<p style="color:#5f6368;font-size:13px;margin-bottom:12px;">告警涉及的租户(appid)和 VPC(vpcid) 在资产库的覆盖情况. <span style="color:#dc2626">红色 = 资产库缺数据, 需要补充导出</span></p>
<div class="chart-row">
<div>
<h3 style="font-size:14px;color:#5f6368;margin-bottom:8px;">主机安全 - 按 AppID (租户)</h3>
<table>
<thead><tr><th>AppID</th><th>告警数</th><th>受害机器数</th><th>状态</th></tr></thead>
<tbody>__APPID_COVERAGE_ROWS__</tbody>
</table>
</div>
<div>
<h3 style="font-size:14px;color:#5f6368;margin-bottom:8px;">御界 - 按 VPC ID</h3>
<table>
<thead><tr><th>VPC ID</th><th>告警数</th><th>受害机器数</th><th>状态</th></tr></thead>
<tbody>__VPCID_COVERAGE_ROWS__</tbody>
</table>
</div>
</div>

<!-- 3.5.1 主机安全受害机器明细 -->
<h3 style="font-size:14px;color:#5f6368;margin:20px 0 8px 0;">主机安全 - 受害机器明细 (按 AppID / 租户 分组, 同时展示 VPC 维度)</h3>
__APPID_DETAIL_HTML__

<!-- 3.5.2 御界受害机器明细 -->
<h3 style="font-size:14px;color:#5f6368;margin:20px 0 8px 0;">御界 - 受害机器明细 (按 VPC ID 分组, 每行展示 AppID / 租户)</h3>
__VPCID_DETAIL_HTML__
</section>

<!-- 段 4: 高危事件 Top 20 -->
<section>
<h2>4. 高危事件 Top 20 (按置信度排序)</h2>
<table>
<thead><tr><th>#</th><th>案例 ID</th><th>产品</th><th>威胁类型</th><th>TTP</th><th>置信度</th><th>攻击者 IP</th><th>受害 IP</th><th>用户</th><th>时间</th></tr></thead>
<tbody>__TOP_THREATS_ROWS__</tbody>
</table>
</section>

<!-- 段 5: L2 攻击链汇总 -->
<section>
<h2>5. L2 攻击链汇总</h2>
<p style="color:#5f6368;font-size:13px;margin-bottom:12px;">
  基于同一攻击者/受害 IP 聚合的跨事件关联, 点击每个 chain 卡片展开可视化详情 (关系图 / 时间线 / 威胁类型分布)
</p>
__ATTACK_CHAINS_HTML__
</section>

<!-- 段 6: IOC 清单 -->
<section>
<h2>6. IOC 清单</h2>
<div class="ioc-list">
<div class="ioc-block"><h3>攻击者 IP (__IOC_IPS_COUNT__)</h3>__IOC_IPS_HTML__</div>
<div class="ioc-block"><h3>用户 (__IOC_USERS_COUNT__)</h3>__IOC_USERS_HTML__</div>
<div class="ioc-block"><h3>主机名 (__IOC_HOSTNAMES_COUNT__)</h3>__IOC_HOSTNAMES_HTML__</div>
</div>
</section>

<!-- 段 7: 处置建议 -->
<section>
<h2>7. 处置建议清单 (按威胁类型分组)</h2>
__SUGGESTIONS_HTML__
</section>

<!-- 段 8: 详细案例 -->
<section>
<h2>8. 详细案例 (__TOTAL_CASES__ 个)</h2>
<p style="color:#5f6368;font-size:13px;margin-bottom:12px;">点击案例标题展开详情</p>
__CASES_HTML__
</section>

<div class="footer">由 soc-alert-pipeline + cwp-analyzer + yujie-analyzer 生成 | __REPORT_TIME__</div>

</div>

<script>
// 段 2 通用图表
var chartType = echarts.init(document.getElementById('chart-threat-type'));
chartType.setOption({
    title: { text: '威胁类型分布', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    series: [{
        type: 'pie', radius: ['30%', '65%'],
        data: __THREAT_TYPE_DATA__,
        label: { formatter: '{b}: {c} ({d}%)', fontSize: 11 }
    }]
});

var chartProduct = echarts.init(document.getElementById('chart-product'));
chartProduct.setOption({
    title: { text: '产品来源分布', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    series: [{
        type: 'pie', radius: '60%',
        data: __PRODUCT_DATA__,
        label: { formatter: '{b}: {c} ({d}%)', fontSize: 11 }
    }]
});

// 段 5 攻击链可视化 (每个 chain 3 个图)
var chainData = __CHAINS_DATA_JSON__;
var chainChartInstances = [];   // 缓存所有 chart 实例, 用于 resize

// 威胁类型配色
var THREAT_COLORS = {
    'C2 Beacon': '#ef4444',
    '暴力破解 (Brute Force)': '#f59e0b',
    '反弹 Shell (Reverse Shell)': '#dc2626',
    '数据外传 (Exfiltration)': '#8b5cf6',
    '横向移动 (Lateral Movement)': '#3b82f6',
    '隧道/代理 (Tunnel)': '#06b6d4',
    '权限提升 (Privilege Escalation)': '#ec4899',
    '初始访问 (Initial Access)': '#10b981',
    '_default': '#94a3b8'
};
function threatColor(name) {
    return THREAT_COLORS[name] || THREAT_COLORS['_default'];
}

// 节点 / 边 聚合
function buildGraph(chain) {
    var pivotKey = chain.pivot_key;
    var pivotType = chain.pivot_type;
    var nodeMap = {};   // ip -> {name, value, category, symbolSize}
    var edgeMap = {};   // "a->b" -> {source, target, value, threats:{}}

    // 中心节点 (pivot)
    nodeMap[pivotKey] = {
        name: pivotKey,
        value: chain.case_count,
        category: 0,   // 0=中心
        symbolSize: Math.min(80, 30 + Math.log2(chain.case_count + 1) * 6)
    };

    chain.top_cases.forEach(function(c) {
        var attacker = c.real_attacker_ip || c.src_ip;
        var victim = c.real_victim_ip || c.host_ip || c.dst_ip;
        if (!attacker || !victim) return;
        var otherKey = (pivotType === 'attacker') ? victim : attacker;
        if (!otherKey) return;

        // 对端节点
        if (!nodeMap[otherKey]) {
            nodeMap[otherKey] = {
                name: otherKey,
                value: 0,
                category: 1,   // 1=对端
                symbolSize: 20
            };
        }
        nodeMap[otherKey].value += 1;

        // 边: pivot <-> other
        var edgeKey = pivotKey + '|' + otherKey;
        if (!edgeMap[edgeKey]) {
            edgeMap[edgeKey] = {
                source: pivotKey,
                target: otherKey,
                value: 0,
                threats: {}
            };
        }
        edgeMap[edgeKey].value += 1;
        var t = c.threat_type || '未知';
        edgeMap[edgeKey].threats[t] = (edgeMap[edgeKey].threats[t] || 0) + 1;
    });

    // 调整对端节点 size
    Object.keys(nodeMap).forEach(function(k) {
        if (k === pivotKey) return;
        var n = nodeMap[k];
        n.symbolSize = Math.min(50, 14 + Math.log2(n.value + 1) * 5);
    });

    return {
        nodes: Object.values(nodeMap),
        links: Object.values(edgeMap).map(function(e) {
            return {
                source: e.source,
                target: e.target,
                value: e.value,
                lineStyle: { width: Math.min(8, 1 + Math.log2(e.value + 1) * 1.5),
                             color: '#94a3b8' }
            };
        })
    };
}

function buildTimeline(chain) {
    var pivotKey = chain.pivot_key;
    var pivotType = chain.pivot_type;
    var threatSet = new Set();
    var series = [];

    chain.top_cases.forEach(function(c) {
        var attacker = c.real_attacker_ip || c.src_ip;
        var victim = c.real_victim_ip || c.host_ip || c.dst_ip;
        var peer = (pivotType === 'attacker') ? victim : attacker;
        if (!peer) return;
        var t = c.threat_type || '未知';
        threatSet.add(t);
    });

    var threats = Array.from(threatSet);
    var yCategories = [];   // 纵轴: 对端 IP
    var yMap = {};
    chain.top_cases.forEach(function(c) {
        var attacker = c.real_attacker_ip || c.src_ip;
        var victim = c.real_victim_ip || c.host_ip || c.dst_ip;
        var peer = (pivotType === 'attacker') ? victim : attacker;
        if (peer && yMap[peer] === undefined) {
            yMap[peer] = yCategories.length;
            yCategories.push(peer);
        }
    });

    threats.forEach(function(t) {
        var data = [];
        chain.top_cases.forEach(function(c) {
            if ((c.threat_type || '未知') !== t) return;
            var attacker = c.real_attacker_ip || c.src_ip;
            var victim = c.real_victim_ip || c.host_ip || c.dst_ip;
            var peer = (pivotType === 'attacker') ? victim : attacker;
            if (!peer) return;
            var tStr = c.event_time || '';
            var ts = tStr ? new Date(tStr.replace(' ', 'T')).getTime() : 0;
            if (!ts || isNaN(ts)) return;
            data.push({
                name: c.case_id || '',
                value: [ts, yMap[peer], Math.round((c.confidence || 0) * 100) / 100]
            });
        });
        if (data.length > 0) {
            series.push({
                name: t,
                type: 'scatter',
                data: data,
                symbolSize: function(val) { return 6 + val[2] * 14; },
                itemStyle: { color: threatColor(t) }
            });
        }
    });

    return {
        yCategories: yCategories,
        series: series
    };
}

function buildPie(chain) {
    var data = [];
    Object.keys(chain.threat_types || {}).forEach(function(t) {
        data.push({ name: t, value: chain.threat_types[t], itemStyle: { color: threatColor(t) } });
    });
    return data;
}

// 渲染所有 chain
function renderAllChains() {
    chainData.forEach(function(chain) {
        var idx = chain.idx;
        // 1. 关系图
        var graphEl = document.getElementById('chain-' + idx + '-graph');
        if (graphEl) {
            var g = buildGraph(chain);
            var chart = echarts.init(graphEl);
            chart.setOption({
                tooltip: {
                    trigger: 'item',
                    formatter: function(p) {
                        if (p.dataType === 'edge') {
                            return p.data.source + ' → ' + p.data.target + '<br/>事件数: ' + p.data.value;
                        }
                        return p.data.name + '<br/>事件数: ' + (p.data.value || 0);
                    }
                },
                legend: [{ data: ['中心节点', '对端节点'], top: 4, textStyle: { fontSize: 10 } }],
                series: [{
                    type: 'graph',
                    layout: 'force',
                    roam: true,
                    draggable: true,
                    categories: [{ name: '中心节点', itemStyle: { color: '#ef4444' } },
                                 { name: '对端节点', itemStyle: { color: '#3b82f6' } }],
                    force: { repulsion: 200, edgeLength: 80, gravity: 0.1 },
                    label: { show: true, position: 'right', fontSize: 10 },
                    edgeSymbol: ['none', 'none'],
                    data: g.nodes,
                    links: g.links,
                    lineStyle: { opacity: 0.7 }
                }]
            });
            chainChartInstances.push(chart);
        }

        // 2. 时间线
        var tlEl = document.getElementById('chain-' + idx + '-timeline');
        if (tlEl) {
            var tl = buildTimeline(chain);
            var chart2 = echarts.init(tlEl);
            chart2.setOption({
                tooltip: {
                    trigger: 'item',
                    formatter: function(p) {
                        var d = p.value;
                        var date = new Date(d[0]).toISOString().replace('T', ' ').substring(0, 19);
                        return p.seriesName + '<br/>' + date + '<br/>对端: ' + tl.yCategories[d[1]] + '<br/>置信度: ' + d[2];
                    }
                },
                legend: { data: tl.series.map(function(s) { return s.name; }), top: 4, textStyle: { fontSize: 10 } },
                grid: { left: 100, right: 20, top: 36, bottom: 30 },
                xAxis: { type: 'time', name: '时间', nameLocation: 'middle', nameGap: 25 },
                yAxis: { type: 'category', data: tl.yCategories, name: '对端 IP', nameLocation: 'middle', nameGap: 60, axisLabel: { fontSize: 10 } },
                series: tl.series
            });
            chainChartInstances.push(chart2);
        }

        // 3. 威胁类型饼图
        var pieEl = document.getElementById('chain-' + idx + '-pie');
        if (pieEl) {
            var pieData = buildPie(chain);
            var chart3 = echarts.init(pieEl);
            chart3.setOption({
                tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
                series: [{
                    type: 'pie',
                    radius: ['35%', '65%'],
                    avoidLabelOverlap: true,
                    data: pieData,
                    label: { formatter: '{b}: {d}%', fontSize: 11 }
                }]
            });
            chainChartInstances.push(chart3);
        }
    });
}

// 延迟渲染, 等待 details 默认 collapsed 状态计算完容器尺寸
setTimeout(function() {
    // 只对 [open] 的 details 渲染 (性能优化, 避免一次性渲染上百个图)
    // 监听 details toggle 事件, 用户点开才渲染
    document.querySelectorAll('details.chain-card').forEach(function(det) {
        det.addEventListener('toggle', function() {
            if (det.open) {
                var idx = parseInt(det.getAttribute('data-idx'));
                var chain = chainData[idx];
                if (!chain) return;
                renderOneChain(chain, idx);
            }
        });
    });
    // 如果有 [open] 状态的, 立即渲染
    document.querySelectorAll('details.chain-card[open]').forEach(function(det) {
        var idx = parseInt(det.getAttribute('data-idx'));
        var chain = chainData[idx];
        if (chain) renderOneChain(chain, idx);
    });
}, 100);

function renderOneChain(chain, idx) {
    if (chain._rendered) return;
    chain._rendered = true;
    var g = buildGraph(chain);
    var graphEl = document.getElementById('chain-' + idx + '-graph');
    if (graphEl) {
        var chart = echarts.init(graphEl);
        chart.setOption({
            tooltip: { trigger: 'item' },
            legend: [{ data: ['中心节点', '对端节点'], top: 4, textStyle: { fontSize: 10 } }],
            series: [{
                type: 'graph', layout: 'force', roam: true, draggable: true,
                categories: [{ name: '中心节点', itemStyle: { color: '#ef4444' } },
                             { name: '对端节点', itemStyle: { color: '#3b82f6' } }],
                force: { repulsion: 200, edgeLength: 80, gravity: 0.1 },
                label: { show: true, position: 'right', fontSize: 10 },
                edgeSymbol: ['none', 'none'],
                data: g.nodes, links: g.links, lineStyle: { opacity: 0.7 }
            }]
        });
        chainChartInstances.push(chart);
    }
    var tlEl = document.getElementById('chain-' + idx + '-timeline');
    if (tlEl) {
        var tl = buildTimeline(chain);
        var chart2 = echarts.init(tlEl);
        chart2.setOption({
            tooltip: { trigger: 'item' },
            legend: { data: tl.series.map(function(s) { return s.name; }), top: 4, textStyle: { fontSize: 10 } },
            grid: { left: 100, right: 20, top: 36, bottom: 30 },
            xAxis: { type: 'time', name: '时间', nameLocation: 'middle', nameGap: 25 },
            yAxis: { type: 'category', data: tl.yCategories, name: '对端 IP', nameLocation: 'middle', nameGap: 60, axisLabel: { fontSize: 10 } },
            series: tl.series
        });
        chainChartInstances.push(chart2);
    }
    var pieEl = document.getElementById('chain-' + idx + '-pie');
    if (pieEl) {
        var chart3 = echarts.init(pieEl);
        chart3.setOption({
            tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
            series: [{
                type: 'pie', radius: ['35%', '65%'], avoidLabelOverlap: true,
                data: buildPie(chain),
                label: { formatter: '{b}: {d}%', fontSize: 11 }
            }]
        });
        chainChartInstances.push(chart3);
    }
}

window.addEventListener('resize', function() {
    chartType.resize();
    chartProduct.resize();
    chainChartInstances.forEach(function(c) { try { c.resize(); } catch(e) {} });
});
</script>
</body>
</html>
"""


def render_html(stats: dict, cases: dict, data_sources: str) -> str:
    """渲染 HTML 报告"""
    html = HTML_TEMPLATE

    # 段 1: KPI
    html = html.replace("__TOTAL_ALERTS__", str(stats["total_alerts"]))
    html = html.replace("__TOTAL_THREATS__", str(stats["total_threats"]))
    html = html.replace("__HIGH_CONF_THREATS__", str(stats["high_confidence_threats"]))
    html = html.replace("__ATTACK_CHAINS__", str(len(stats.get("attack_chains", []))))
    html = html.replace("__AFFECTED_ASSETS__", str(len(stats["affected_assets"])))

    # 段 2: ECharts data
    threat_type_data = json.dumps(
        [{"name": k, "value": v} for k, v in stats["threat_by_type"].most_common()],
        ensure_ascii=False,
    )
    product_data = json.dumps(
        [{"name": k, "value": v} for k, v in stats["threat_by_product"].most_common()],
        ensure_ascii=False,
    )
    html = html.replace("__THREAT_TYPE_DATA__", threat_type_data)
    html = html.replace("__PRODUCT_DATA__", product_data)

    # 段 3: 受影响资产表格
    asset_rows = []
    # 按重要性排序
    importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    sorted_assets = sorted(
        stats["affected_assets"].values(),
        key=lambda a: importance_order.get(a.get("importance", "unknown"), 99),
    )
    for a in sorted_assets:
        imp = a.get("importance", "unknown")
        imp_class = f"tag-{imp}" if imp in ("critical", "high", "medium", "low") else "tag-low"
        layer_class = "tag-yujie" if a.get("layer") == "platform" else "tag-cwp"
        asset_rows.append(
            f"<tr>"
            f"<td><code>{escape(a.get('ip', ''))}</code></td>"
            f"<td>{escape(a.get('hostname', ''))}</td>"
            f"<td><span class='tag {layer_class}'>{escape(a.get('layer', ''))}</span></td>"
            f"<td>{escape(a.get('asset_type', ''))}</td>"
            f"<td><span class='tag {imp_class}'>{escape(imp)}</span></td>"
            f"<td>{escape(a.get('business_system', ''))}</td>"
            f"<td>{escape(a.get('zone', ''))}</td>"
            f"<td>{escape(a.get('os', '')[:40])}</td>"
            f"</tr>"
        )
    html = html.replace("__AFFECTED_ASSETS_ROWS__", "".join(asset_rows) or "<tr><td colspan='8' style='text-align:center;color:#9aa0a6'>无匹配资产 (资产库可能不全, 见下方资产覆盖情况)</td></tr>")

    # 段 3.5: 资产覆盖情况 (顶部概览)
    appid_rows = []
    for appid, info in sorted(stats["asset_coverage_appid"].items(), key=lambda x: -x[1]["alerts"]):
        status = info["status"]
        if status == "covered":
            status_html = f"<span class='tag tag-low'>✓ 已覆盖</span>"
        else:
            status_html = f"<span class='tag tag-high'>✗ 缺资产</span>"
        victim_count = len(info.get("victim_ips", {}))
        appid_rows.append(
            f"<tr><td><code>{escape(appid)}</code></td><td>{info['alerts']}</td>"
            f"<td>{victim_count}</td><td>{status_html}</td></tr>"
        )
    html = html.replace("__APPID_COVERAGE_ROWS__", "".join(appid_rows) or "<tr><td colspan='4' style='text-align:center;color:#9aa0a6'>无 AppID 数据 (非主机安全告警)</td></tr>")

    vpcid_rows = []
    for vpcid, info in sorted(stats["asset_coverage_vpcid"].items(), key=lambda x: -x[1]["alerts"]):
        status = info["status"]
        if status == "covered":
            status_html = f"<span class='tag tag-low'>✓ 已覆盖</span>"
        else:
            status_html = f"<span class='tag tag-high'>✗ 缺资产</span>"
        victim_count = len(info.get("victim_ips", {}))
        vpcid_rows.append(
            f"<tr><td><code>{escape(vpcid)}</code></td><td>{info['alerts']}</td>"
            f"<td>{victim_count}</td><td>{status_html}</td></tr>"
        )
    html = html.replace("__VPCID_COVERAGE_ROWS__", "".join(vpcid_rows) or "<tr><td colspan='4' style='text-align:center;color:#9aa0a6'>无 VPC ID 数据 (非御界告警)</td></tr>")

    # 段 3.5.1: 主机安全受害机器明细 (按 AppID 分组展开)
    def _render_ip_detail_table(victim_ips: dict, *, show_appid: bool = True, show_vpcid: bool = False) -> str:
        """渲染一个 AppID/VPCID 下的受害机器明细表

        Args:
            victim_ips: {ip: {"alerts": int, "asset": dict|None}}
            show_appid: 是否展示 AppID 列 (租户标识)
            show_vpcid: 是否展示 VPC ID 列 (网络维度)
        """
        if not victim_ips:
            return "<p style='color:#9aa0a6;font-size:13px;'>无受害 IP 数据</p>"
        rows = []
        for ip, info in sorted(victim_ips.items(), key=lambda x: -x[1]["alerts"]):
            a = info.get("asset") or {}
            alerts = info["alerts"]
            if a:
                hostname = escape(a.get("hostname") or "")
                atype = escape(a.get("asset_type") or "")
                biz = escape(a.get("business_system") or "")
                imp = escape(a.get("importance") or "")
                zone = escape(a.get("zone") or "")
                os_name = escape((a.get("os") or "")[:30])
                appid_cell = f"<code>{escape(a.get('appid') or '-')}</code>"
                vpcid_cell = f"<code>{escape(str(a.get('vpcid') or '-'))}</code>" if a.get('vpcid') else "-"
                vpc_name = a.get('vpc_name') or ''
                if vpc_name and a.get('vpcid'):
                    vpcid_cell = f"<code>{a.get('vpcid')}</code> ({escape(vpc_name)})"
                status = "<span class='tag tag-low'>✓ 资产已匹配</span>"
            else:
                hostname = atype = biz = imp = zone = os_name = ""  # 查不到就滞空
                appid_cell = "-"
                vpcid_cell = "-"
                status = "<span class='tag tag-high'>✗ 资产库无数据</span>"
            row = [f"<code>{escape(ip)}</code>"]
            if show_appid:
                row.append(appid_cell)
            if show_vpcid:
                row.append(vpcid_cell)
            row.extend([hostname, atype, biz, imp, zone, os_name, str(alerts), status])
            rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
        # 表头
        header = ["<th>受害 IP</th>"]
        if show_appid:
            header.append("<th>AppID (租户)</th>")
        if show_vpcid:
            header.append("<th>VPC ID</th>")
        header.extend(["<th>主机名</th>", "<th>类型</th>", "<th>业务系统</th>",
                       "<th>重要性</th>", "<th>可用区</th>", "<th>OS</th>",
                       "<th>告警数</th>", "<th>资产状态</th>"])
        return (
            "<table>"
            f"<thead><tr>{''.join(header)}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    appid_detail_parts = []
    for appid, info in sorted(stats["asset_coverage_appid"].items(), key=lambda x: -x[1]["alerts"]):
        ips = info.get("victim_ips", {})
        covered = sum(1 for v in ips.values() if v.get("asset"))
        missing = len(ips) - covered
        summary = f"<span class='tag tag-low'>{covered} 台已覆盖</span>" if covered else ""
        if missing:
            summary += f" <span class='tag tag-high'>{missing} 台缺资产</span>"
        # 汇总该 AppID 涉及的 vpcid (从受害资产的 vpcid 字段收集)
        vpcids_in_appid = sorted(set(
            str(v.get("asset", {}).get("vpcid"))
            for v in ips.values()
            if v.get("asset") and v.get("asset", {}).get("vpcid")
        ))
        vpc_hint = ""
        if vpcids_in_appid:
            vpc_hint = f" &nbsp;·&nbsp; 涉及 VPC: {', '.join(f'<code>{escape(v)}</code>' for v in vpcids_in_appid)}"
        appid_detail_parts.append(
            f"<details open style='margin:8px 0 16px 0;'>"
            f"<summary style='cursor:pointer;font-weight:600;'>"
            f"租户 <code>{escape(appid)}</code> &nbsp;·&nbsp; 受害机器 {len(ips)} 台 &nbsp;·&nbsp; "
            f"告警 {info['alerts']} 条 &nbsp; {summary}{vpc_hint}"
            f"</summary>"
            f"{_render_ip_detail_table(ips, show_appid=True, show_vpcid=True)}"
            f"</details>"
        )
    html = html.replace("__APPID_DETAIL_HTML__", "".join(appid_detail_parts) or "<p style='color:#9aa0a6;font-size:13px;'>无 AppID 明细</p>")

    # 段 3.5.2: 御界受害机器明细 (按 VPC ID 分组展开, 但每行展示 AppID 让租户维度可见)
    vpc_detail_parts = []
    for vpcid, info in sorted(stats["asset_coverage_vpcid"].items(), key=lambda x: -x[1]["alerts"]):
        ips = info.get("victim_ips", {})
        covered = sum(1 for v in ips.values() if v.get("asset"))
        missing = len(ips) - covered
        summary = f"<span class='tag tag-low'>{covered} 台已覆盖</span>" if covered else ""
        if missing:
            summary += f" <span class='tag tag-high'>{missing} 台缺资产</span>"
        # 汇总该 VPC 涉及的 AppID (从受害资产的 appid 字段收集)
        appids_in_vpc = sorted(set(
            str(v.get("asset", {}).get("appid"))
            for v in ips.values()
            if v.get("asset") and v.get("asset", {}).get("appid")
        ))
        appid_hint = ""
        if appids_in_vpc:
            appid_hint = f" &nbsp;·&nbsp; 租户 AppID: {', '.join(f'<code>{escape(a)}</code>' for a in appids_in_vpc)}"
        vpc_detail_parts.append(
            f"<details open style='margin:8px 0 16px 0;'>"
            f"<summary style='cursor:pointer;font-weight:600;'>"
            f"VPC <code>{escape(vpcid)}</code> &nbsp;·&nbsp; 受害机器 {len(ips)} 台 &nbsp;·&nbsp; "
            f"告警 {info['alerts']} 条 &nbsp; {summary}{appid_hint}"
            f"</summary>"
            f"{_render_ip_detail_table(ips, show_appid=True, show_vpcid=True)}"
            f"</details>"
        )
    html = html.replace("__VPCID_DETAIL_HTML__", "".join(vpc_detail_parts) or "<p style='color:#9aa0a6;font-size:13px;'>无 VPC ID 明细</p>")

    # 段 4: 高危事件 Top 20
    top_rows = []
    for i, case in enumerate(stats["top_threats"], 1):
        conf = case["confidence"]
        conf_class = "tag-high" if conf >= 0.7 else "tag-medium" if conf >= 0.5 else "tag-low"
        prod_class = "tag-yujie" if case["product"] == "yujie" else "tag-cwp"
        attacker = case["real_attacker_ip"] or case["src_ip"] or "-"
        victim = case["real_victim_ip"] or case["dst_ip"] or case["host_ip"] or "-"
        top_rows.append(
            f"<tr>"
            f"<td>{i}</td>"
            f"<td><code>{escape(case['id'])}</code></td>"
            f"<td><span class='tag {prod_class}'>{escape(case['product'])}</span></td>"
            f"<td>{escape(case['threat_type'] or '-')}</td>"
            f"<td><code>{escape(case['ttp'] or '-')}</code></td>"
            f"<td><span class='tag {conf_class}'>{conf:.2f}</span></td>"
            f"<td><code>{escape(attacker)}</code></td>"
            f"<td><code>{escape(victim)}</code></td>"
            f"<td>{escape(case['user'] or '-')}</td>"
            f"<td>{escape(case['event_time'] or '-')}</td>"
            f"</tr>"
        )
    html = html.replace("__TOP_THREATS_ROWS__", "".join(top_rows) or "<tr><td colspan='10' style='text-align:center;color:#9aa0a6'>无威胁事件</td></tr>")

    # 段 5: L2 攻击链汇总
    chains = stats.get("attack_chains", [])
    chains_html = []
    chain_data_json_list = []   # 给 JS 端消费: 每个 chain 序列化数据
    if not chains:
        chains_html.append("<p style='color:#9aa0a6'>无 L2 攻击链数据 (未运行 l2_correlate.py 或无关联结果)</p>")
    else:
        # 5.1 攻击链总览表
        chains_html.append("<h3 style='font-size:14px;color:#5f6368;margin-bottom:8px'>5.1 攻击链总览 (按事件数降序)</h3>")
        chains_html.append("<table>")
        chains_html.append("<thead><tr><th>#</th><th>视角</th><th>关联键</th><th>事件数</th><th>跨产品</th><th>涉及产品</th><th>Kill Chain 阶段</th><th>时间范围</th></tr></thead>")
        chains_html.append("<tbody>")
        for i, chain in enumerate(chains, 1):
            pivot = "攻击者" if chain.get("pivot_type") == "attacker" else "受害者"
            cross = "✅" if chain.get("is_cross_product") else "❌"
            products = ", ".join(f"{p}({n})" for p, n in chain.get("products", {}).items())
            phases = " → ".join(chain.get("kill_chain_phases", [])[:3]) or "-"
            t_range = chain.get("time_range", [None, None])
            t_str = ""
            if t_range and t_range[0]:
                t_str = f"{t_range[0][:16]} ~ {t_range[1][:16]}" if t_range[1] else t_range[0][:16]
            chains_html.append(
                f"<tr><td>{i}</td><td>{pivot}</td><td><code>{escape(chain.get('pivot_key', ''))}</code></td>"
                f"<td>{chain.get('case_count', 0)}</td><td style='text-align:center'>{cross}</td>"
                f"<td>{escape(products)}</td><td>{escape(phases)}</td><td><small>{escape(t_str)}</small></td></tr>"
            )
        chains_html.append("</tbody></table>")
        chains_html.append("")

        # 5.2 每个 chain 一个可折叠卡片 (内含 3 个 ECharts 图)
        chains_html.append("<h3 style='font-size:14px;color:#5f6368;margin:16px 0 8px'>5.2 攻击链详情 (点击展开可视化)</h3>")

        for idx, chain in enumerate(chains):
            pivot = "攻击者" if chain.get("pivot_type") == "attacker" else "受害者"
            cross_tag = "<span class='tag tag-high'>跨产品</span>" if chain.get("is_cross_product") else ""
            products = ", ".join(f"{p}({n})" for p, n in chain.get("products", {}).items())
            ttps = ", ".join(chain.get("ttps", [])[:3]) or "-"
            phases = " → ".join(chain.get("kill_chain_phases", [])[:4]) or "-"
            t_range = chain.get("time_range", [None, None])
            t_str = ""
            if t_range and t_range[0]:
                t_str = f"{t_range[0][:19]} ~ {t_range[1][:19]}" if t_range[1] else t_range[0][:19]
            threat_types_str = ", ".join(f"{t}({n})" for t, n in chain.get("threat_types", {}).items()) or "-"

            title = (
                f"#{idx+1} <span class='tag tag-cwp'>{pivot}</span> "
                f"<code>{escape(chain.get('pivot_key', ''))}</code> "
                f"<span class='tag tag-medium'>{chain.get('case_count', 0)} 事件</span> "
                f"{cross_tag}"
            )
            chains_html.append(f"<details class='chain-card' data-idx='{idx}'>")
            chains_html.append(f"<summary>{title}</summary>")
            chains_html.append("<div class='chain-body'>")

            # 概要 meta
            chains_html.append("<div class='chain-meta'>")
            chains_html.append(f"<div class='chain-meta-item'><div class='label'>威胁类型</div><div class='value'>{escape(threat_types_str)}</div></div>")
            chains_html.append(f"<div class='chain-meta-item'><div class='label'>ATT&CK TTP</div><div class='value'><code>{escape(ttps)}</code></div></div>")
            chains_html.append(f"<div class='chain-meta-item'><div class='label'>Kill Chain</div><div class='value'>{escape(phases)}</div></div>")
            chains_html.append(f"<div class='chain-meta-item'><div class='label'>时间范围</div><div class='value' style='font-size:11px'>{escape(t_str)}</div></div>")
            chains_html.append("</div>")

            # 3 个图 (3 列)
            chains_html.append("<div class='chain-charts-3'>")
            chains_html.append(f"<div><div class='chain-chart-title'>🕸️ 关系图 (攻击者/受害者 → 对端IP)</div><div id='chain-{idx}-graph' class='chain-graph'></div></div>")
            chains_html.append(f"<div><div class='chain-chart-title'>⏱️ 时间线 (按威胁类型着色)</div><div id='chain-{idx}-timeline' class='chain-timeline'></div></div>")
            chains_html.append(f"<div><div class='chain-chart-title'>🥧 威胁类型分布</div><div id='chain-{idx}-pie' class='chain-pie'></div></div>")
            chains_html.append("</div>")

            # 折叠的 top cases 表
            top_cases = chain.get("top_cases", [])
            if top_cases:
                chains_html.append("<details style='margin-top:12px;background:#f8f9fa;padding:8px'><summary style='font-size:12px;color:#5f6368'>📋 涉及案例时间线 (前 15 条, 共 {} 条)</summary>".format(len(top_cases)))
                chains_html.append("<table class='chain-table'>")
                chains_html.append("<thead><tr><th>时间</th><th>产品</th><th>威胁类型</th><th>TTP</th><th>置信度</th><th>攻击者</th><th>受害者</th></tr></thead>")
                chains_html.append("<tbody>")
                for c in top_cases[:15]:
                    attacker = c.get("real_attacker_ip") or c.get("src_ip") or "-"
                    victim = c.get("real_victim_ip") or c.get("host_ip") or c.get("dst_ip") or "-"
                    conf = c.get("confidence", 0)
                    conf_class = "tag-high" if conf >= 0.7 else "tag-medium" if conf >= 0.5 else "tag-low"
                    prod_class = "tag-yujie" if c.get("product") == "yujie" else "tag-cwp"
                    chains_html.append(
                        f"<tr><td><small>{escape(str(c.get('event_time', '-'))[:19])}</small></td>"
                        f"<td><span class='tag {prod_class}'>{escape(c.get('product', '-'))}</span></td>"
                        f"<td>{escape(c.get('threat_type') or '-')}</td>"
                        f"<td><code>{escape(c.get('ttp') or '-')}</code></td>"
                        f"<td><span class='tag {conf_class}'>{conf:.2f}</span></td>"
                        f"<td><code>{escape(attacker)}</code></td>"
                        f"<td><code>{escape(victim)}</code></td></tr>"
                    )
                chains_html.append("</tbody></table>")
                if len(top_cases) > 15:
                    chains_html.append(f"<p style='color:#9aa0a6;font-size:11px'>(仅显示前 15 条, 共 {len(top_cases)} 条)</p>")
                chains_html.append("</details>")

            chains_html.append("</div>")   # /.chain-body
            chains_html.append("</details>")

            # 序列化数据 (供 JS ECharts 消费)
            chain_data_json_list.append({
                "idx": idx,
                "pivot_type": chain.get("pivot_type"),
                "pivot_key": chain.get("pivot_key", ""),
                "case_count": chain.get("case_count", 0),
                "is_cross_product": chain.get("is_cross_product", False),
                "threat_types": chain.get("threat_types", {}),
                "kill_chain_phases": chain.get("kill_chain_phases", []),
                "time_range": chain.get("time_range", [None, None]),
                "top_cases": top_cases,
            })

    chains_data_json = json.dumps(chain_data_json_list, ensure_ascii=False)
    html = html.replace("__ATTACK_CHAINS_HTML__", "".join(chains_html))
    html = html.replace("__CHAINS_DATA_JSON__", chains_data_json)

    # 段 6: IOC 清单
    def render_ioc_list(counter: Counter, max_items: int = 50) -> str:
        if not counter:
            return "<p style='color:#9aa0a6'>无</p>"
        items = []
        for val, cnt in counter.most_common(max_items):
            items.append(f"<div class='ioc-item'><span><code>{escape(val)}</code></span><span style='color:#9aa0a6'>×{cnt}</span></div>")
        return "".join(items)

    html = html.replace("__IOC_IPS_COUNT__", str(len(stats["iocs_ips"])))
    html = html.replace("__IOC_IPS_HTML__", render_ioc_list(stats["iocs_ips"]))
    html = html.replace("__IOC_USERS_COUNT__", str(len(stats["iocs_users"])))
    html = html.replace("__IOC_USERS_HTML__", render_ioc_list(stats["iocs_users"]))
    html = html.replace("__IOC_HOSTNAMES_COUNT__", str(len(stats["iocs_hostnames"])))
    html = html.replace("__IOC_HOSTNAMES_HTML__", render_ioc_list(stats["iocs_hostnames"]))

    # 段 7: 处置建议 (按威胁类型分组)
    sugg_html = []
    if not cases:
        sugg_html.append("<p style='color:#9aa0a6'>无威胁事件, 无处置建议</p>")
    else:
        by_type = defaultdict(list)
        for case in cases.values():
            if case["threat_type"]:
                by_type[case["threat_type"]].append(case)
        for t_type, type_cases in sorted(by_type.items(), key=lambda x: -len(x[1])):
            sugg_html.append(f"<details open><summary>{escape(t_type)} ({len(type_cases)} 个事件)</summary>")
            sugg_html.append("<div style='padding:12px'>")
            # 取该类型的处置建议 (从第一个 case 提取)
            first = type_cases[0]
            # 从 markdown 提取处置建议段
            content = first["content"]
            m = re.search(r"## \d+\. 处置建议\s*\n(.*?)(?=## \d+\.|$)", content, re.DOTALL)
            if m:
                sugg_text = m.group(1).strip()
                # 转成 HTML
                for line in sugg_text.split("\n"):
                    line = line.strip()
                    if line.startswith("- [ ]"):
                        sugg_html.append(f"<div style='padding:4px 0'>☐ {escape(line[5:])}</div>")
                    elif line.startswith("- "):
                        sugg_html.append(f"<div style='padding:4px 0;color:#5f6368'>{escape(line)}</div>")
                    elif line:
                        sugg_html.append(f"<div style='padding:4px 0'>{escape(line)}</div>")
            sugg_html.append("</div></details>")
    html = html.replace("__SUGGESTIONS_HTML__", "".join(sugg_html))

    # 段 8: 详细案例 (折叠)
    cases_html = []
    sorted_cases = sorted(cases.values(), key=lambda c: c["confidence"], reverse=True)
    for case in sorted_cases[:100]:  # 最多 100 个, 避免报告过大
        conf = case["confidence"]
        conf_class = "tag-high" if conf >= 0.7 else "tag-medium" if conf >= 0.5 else "tag-low"
        prod_class = "tag-yujie" if case["product"] == "yujie" else "tag-cwp"
        title = (
            f"<span class='tag {prod_class}'>{escape(case['product'])}</span> "
            f"<span class='tag {conf_class}'>conf={conf:.2f}</span> "
            f"<code>{escape(case['id'])}</code> "
            f"- {escape(case['threat_type'] or '无威胁')}"
        )
        cases_html.append(f"<details><summary>{title}</summary>")
        cases_html.append(f"<div class='case-content'>{escape(case['content'])}</div></details>")
    if len(sorted_cases) > 100:
        cases_html.append(f"<p style='color:#9aa0a6;padding:12px'>(仅显示前 100 个案例, 共 {len(sorted_cases)} 个)</p>")
    html = html.replace("__TOTAL_CASES__", str(len(cases)))
    html = html.replace("__CASES_HTML__", "".join(cases_html) or "<p style='color:#9aa0a6'>无案例</p>")

    # 元数据
    html = html.replace("__REPORT_TIME__", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html = html.replace("__DATA_SOURCES__", escape(data_sources))

    return html


def main():
    ap = argparse.ArgumentParser(
        description="SOC 告警分析标准报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--l0", nargs="+", type=Path, required=True,
                    help="L0 JSONL 文件 (可多个, 含资产关联结果)")
    ap.add_argument("--cases", nargs="+", type=Path, required=True,
                    help="L1 案例目录 (可多个)")
    ap.add_argument("--attack-chains", type=Path, default=None,
                    help="L2 攻击链 JSONL 文件 (attack_chains.jsonl, 可选)")
    ap.add_argument("--out", type=Path, required=True,
                    help="输出 HTML 文件路径")
    args = ap.parse_args()

    # 1. 加载数据
    print("[INFO] 加载 L0 数据...", file=sys.stderr)
    records = load_l0_records(args.l0)
    print(f"[INFO] L0 记录数: {len(records)}", file=sys.stderr)

    print("[INFO] 加载 L1 案例...", file=sys.stderr)
    cases = load_cases(args.cases)
    print(f"[INFO] 案例数: {len(cases)}", file=sys.stderr)

    # 加载 L2 攻击链 (可选)
    attack_chains = []
    if args.attack_chains and args.attack_chains.exists():
        print("[INFO] 加载 L2 攻击链...", file=sys.stderr)
        with open(args.attack_chains, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    attack_chains.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        print(f"[INFO] 攻击链数: {len(attack_chains)}", file=sys.stderr)
    elif args.attack_chains:
        print(f"[WARN] L2 攻击链文件不存在: {args.attack_chains}", file=sys.stderr)

    # 2. 聚合统计
    print("[INFO] 聚合统计...", file=sys.stderr)
    stats = aggregate_stats(records, cases)
    stats["attack_chains"] = attack_chains
    print(f"[INFO] 受影响资产: {len(stats['affected_assets'])}", file=sys.stderr)
    print(f"[INFO] 威胁类型分布: {dict(stats['threat_by_type'])}", file=sys.stderr)
    if attack_chains:
        print(f"[INFO] 攻击链: {len(attack_chains)} (跨产品: {sum(1 for c in attack_chains if c.get('is_cross_product'))})",
              file=sys.stderr)

    # 3. 渲染 HTML
    print("[INFO] 渲染 HTML...", file=sys.stderr)
    data_sources = ", ".join(p.name for p in args.l0 + args.cases)
    html = render_html(stats, cases, data_sources)

    # 4. 写出
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"[OK] 报告已生成: {args.out}", file=sys.stderr)
    print(f"[OK] 文件大小: {args.out.stat().st_size // 1024} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
