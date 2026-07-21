#!/usr/bin/env python3
"""L1 CFW (云防火墙) 入侵防御告警日志分析 CLI

输入: L0 输出的 JSONL (soc-alert-pipeline/l0_parse.py --product cfw 生成)
输出:
  - CFW 告警分析报告 (Markdown)
  - per-attacker case .md 文件 (供 L2 l2_correlate.py 消费)

与 tianmu 的 L1 类似 (自包含, 无独立 analyzer.py):
  - CFW eventLog 是逐条告警 (非聚合统计)
  - 分析维度: 概览 / 风险等级 / 攻击规则 Top / 源IP Top / 目标IP Top /
              方向分析(入站/出站) / 处置动作(阻断率/可疑绕过) / 攻击者画像
  - case 按攻击源IP聚合 (不逐条输出, 避免文件爆炸)

CFW 独有维度:
  - direction (0=出站/1=入站): 出站告警可能是失陷主机外连
  - strategy (阻断/观察/放行): 观察+放行的高危告警 = 可疑绕过
  - level (严重/高危/中危/低危) → severity 归一

用法:
  python3 l1_cfw_analyze.py <l0_jsonl_path> --out report/ --emit-cases cases/
  python3 l1_cfw_analyze.py <l0_jsonl_path> --top 20 --out report.md
  python3 l1_cfw_analyze.py <l0_jsonl_path> --emit-cases cases/ --min-count 3 --max-cases 50
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# ==================== L0 加载 ====================

def load_records(jsonl_path: Path) -> list[dict]:
    """加载 L0 JSONL, 只保留 cfw eventLog 记录 (ok/partial)

    过滤掉非 eventLog 日志 (operateLog/natFlowLog 等), 它们不是入侵防御告警,
    混入分析会污染动作/方向统计. eventLog 判定依据 parsed.log_type 含 "eventlog".
    """
    records = []
    skipped_non_event = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("product") != "cfw":
                continue
            if rec.get("parse_status") not in ("ok", "partial"):
                continue
            # 只保留 eventLog (入侵防御告警), 过滤 operateLog/natFlowLog 等
            parsed = rec.get("parsed", {})
            log_type = (parsed.get("log_type") or "").lower()
            if "eventlog" not in log_type:
                skipped_non_event += 1
                continue
            records.append(rec)
    if skipped_non_event:
        print(f"[INFO] 跳过非 eventLog 记录: {skipped_non_event} 条", file=sys.stderr)
    return records


# ==================== Kill Chain 阶段映射 ====================

def kill_chain_phase(rule_name: str) -> str:
    """根据 CFW 规则名映射 Kill Chain 阶段"""
    t = (rule_name or "").lower()

    # 侦察阶段
    if any(k in t for k in ("扫描", "探测", "端口扫描", "信息收集", "recon", "scan")):
        return "Reconnaissance"

    # 利用阶段 (注入/溢出/文件包含/WebShell)
    if any(k in t for k in ("注入", "inject", "xss", "溢出", "overflow", "文件包含",
                            "路径穿越", "webshell", "rce", "命令执行", "反序列化")):
        return "Exploitation"

    # C2 阶段 (隧道/外连/C2)
    if any(k in t for k in ("隧道", "tunnel", "c2", "beacon", "外连", "反弹", "reverse")):
        return "Command and Control"

    # 横向移动
    if any(k in t for k in ("横向", "lateral", "爆破", "暴力", "brute")):
        return "Lateral Movement"

    # 凭证获取
    if any(k in t for k in ("弱口令", "凭证", "credential", "密码")):
        return "Credential Access"

    # 默认: 初始访问
    return "Initial Access"


# ==================== 聚合分析 ====================

def aggregate_analysis(records: list[dict]) -> dict:
    """批量聚合分析

    Returns:
        分析结果 dict, 包含概览 + TOP 统计 + 方向/动作分布
    """
    total = len(records)

    # 概览统计
    severity_counter: Counter = Counter()
    action_counter: Counter = Counter()
    direction_counter: Counter = Counter()
    appids: set = set()
    all_times: list = []

    # 规则统计
    rule_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "src_ips": set(), "dst_ips": set(),
        "severities": Counter(), "actions": Counter(),
        "first_time": None, "last_time": None,
    })

    # 源IP统计
    src_ip_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "rules": set(), "dst_ips": set(),
        "severities": Counter(), "actions": Counter(),
        "directions": Counter(), "first_time": None, "last_time": None,
    })

    # 目标IP统计
    dst_ip_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "src_ips": set(), "rules": set(),
        "severities": Counter(),
    })

    for rec in records:
        p = rec.get("parsed", {})

        severity = p.get("severity", "info")
        action = p.get("action", "unknown")
        direction = p.get("direction", "unknown")
        rule_name = p.get("rule_name") or p.get("rule_id") or "未知"
        src_ip = p.get("src_ip") or "未知"
        dst_ip = p.get("dst_ip") or "未知"
        appid = p.get("appid")
        event_time = p.get("event_time")

        severity_counter[severity] += 1
        action_counter[action] += 1
        direction_counter[direction] += 1
        if appid:
            appids.add(appid)
        if event_time:
            all_times.append(event_time)

        # 规则统计
        rs = rule_stats[rule_name]
        rs["count"] += 1
        rs["src_ips"].add(src_ip)
        rs["dst_ips"].add(dst_ip)
        rs["severities"][severity] += 1
        rs["actions"][action] += 1
        if event_time:
            if rs["first_time"] is None or event_time < rs["first_time"]:
                rs["first_time"] = event_time
            if rs["last_time"] is None or event_time > rs["last_time"]:
                rs["last_time"] = event_time

        # 源IP统计
        ss = src_ip_stats[src_ip]
        ss["count"] += 1
        ss["rules"].add(rule_name)
        ss["dst_ips"].add(dst_ip)
        ss["severities"][severity] += 1
        ss["actions"][action] += 1
        ss["directions"][direction] += 1
        if event_time:
            if ss["first_time"] is None or event_time < ss["first_time"]:
                ss["first_time"] = event_time
            if ss["last_time"] is None or event_time > ss["last_time"]:
                ss["last_time"] = event_time

        # 目标IP统计
        ds = dst_ip_stats[dst_ip]
        ds["count"] += 1
        ds["src_ips"].add(src_ip)
        ds["rules"].add(rule_name)
        ds["severities"][severity] += 1

    # 排序
    top_rules = sorted(rule_stats.items(), key=lambda x: -x[1]["count"])
    top_src_ips = sorted(src_ip_stats.items(), key=lambda x: -x[1]["count"])
    top_dst_ips = sorted(dst_ip_stats.items(), key=lambda x: -x[1]["count"])

    # 多规则命中源IP (≥3 条规则 = 多向量攻击)
    multi_rule_srcs = [
        (ip, s) for ip, s in src_ip_stats.items() if len(s["rules"]) >= 3
    ]
    multi_rule_srcs.sort(key=lambda x: -len(x[1]["rules"]))

    # 可疑绕过: 高危 + (观察/放行)
    suspicious_bypass = []
    for rec in records:
        p = rec.get("parsed", {})
        sev = p.get("severity", "")
        act = p.get("action", "")
        if sev in ("critical", "high") and act in ("observe", "allow"):
            suspicious_bypass.append(rec)

    # 出站高危告警 (可能失陷主机外连)
    outbound_high = []
    for rec in records:
        p = rec.get("parsed", {})
        if p.get("direction") == "outbound" and p.get("severity") in ("critical", "high"):
            outbound_high.append(rec)

    # 时间范围
    time_range = None
    if all_times:
        all_times.sort()
        time_range = (all_times[0], all_times[-1])

    return {
        "overview": {
            "total": total,
            "unique_rules": len(rule_stats),
            "unique_src_ips": len(src_ip_stats),
            "unique_dst_ips": len(dst_ip_stats),
            "unique_appids": len(appids),
            "time_range": time_range,
            "severity_breakdown": dict(severity_counter),
            "action_breakdown": dict(action_counter),
            "direction_breakdown": dict(direction_counter),
        },
        "top_rules": top_rules,
        "top_src_ips": top_src_ips,
        "top_dst_ips": top_dst_ips,
        "multi_rule_srcs": multi_rule_srcs,
        "suspicious_bypass": suspicious_bypass,
        "outbound_high": outbound_high,
    }


# ==================== 报告渲染 ====================

def render_report(analysis: dict, source_file: str, top_n: int) -> str:
    """渲染 CFW 告警分析报告 (Markdown)"""
    ov = analysis["overview"]
    lines = []

    lines.append("# CFW 云防火墙 - 入侵防御告警分析报告")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 数据来源: {source_file}")
    lines.append("")

    # 1. 告警概览
    lines.append("## 1. 告警概览")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 告警总数 | **{ov['total']:,}** |")
    lines.append(f"| 命中规则数 | {ov['unique_rules']} |")
    lines.append(f"| 攻击源IP数 | {ov['unique_src_ips']} |")
    lines.append(f"| 被攻击目标IP数 | {ov['unique_dst_ips']} |")
    lines.append(f"| AppId 数 | {ov['unique_appids']} |")
    if ov["time_range"]:
        lines.append(f"| 时间范围 | {ov['time_range'][0]} ~ {ov['time_range'][1]} |")
    lines.append("")

    # 2. 风险等级分布
    sev_map = {"critical": "严重", "high": "高危", "medium": "中危", "low": "低危", "info": "信息"}
    lines.append("## 2. 风险等级分布")
    lines.append("")
    lines.append("| 等级 | 条数 | 占比 |")
    lines.append("|---|---|---|")
    for sev in ("critical", "high", "medium", "low", "info"):
        cnt = ov["severity_breakdown"].get(sev, 0)
        pct = f"{cnt * 100 / max(ov['total'], 1):.1f}%"
        lines.append(f"| {sev_map.get(sev, sev)} | {cnt:,} | {pct} |")
    lines.append("")

    # 3. 方向分布
    dir_map = {"inbound": "入站", "outbound": "出站", "unknown": "未知"}
    lines.append("## 3. 方向分布")
    lines.append("")
    lines.append("| 方向 | 条数 | 占比 |")
    lines.append("|---|---|---|")
    for d in ("inbound", "outbound", "unknown"):
        cnt = ov["direction_breakdown"].get(d, 0)
        pct = f"{cnt * 100 / max(ov['total'], 1):.1f}%"
        lines.append(f"| {dir_map.get(d, d)} | {cnt:,} | {pct} |")
    lines.append("")
    outbound_cnt = ov["direction_breakdown"].get("outbound", 0)
    if outbound_cnt > 0:
        lines.append(f"> ⚠️ **出站告警 {outbound_cnt} 条**: 可能是内部失陷主机外连 C2 / 数据外泄, 需结合主机安全 (CWP) 关联确认")
        lines.append("")

    # 4. 处置动作分布
    act_map = {"block": "阻断", "observe": "观察", "allow": "放行", "unknown": "未知"}
    lines.append("## 4. 处置动作分布")
    lines.append("")
    lines.append("| 动作 | 条数 | 占比 |")
    lines.append("|---|---|---|")
    for a in ("block", "observe", "allow", "unknown"):
        cnt = ov["action_breakdown"].get(a, 0)
        pct = f"{cnt * 100 / max(ov['total'], 1):.1f}%"
        lines.append(f"| {act_map.get(a, a)} | {cnt:,} | {pct} |")
    lines.append("")
    block_cnt = ov["action_breakdown"].get("block", 0)
    block_rate = f"{block_cnt * 100 / max(ov['total'], 1):.1f}%"
    lines.append(f"> 阻断率: **{block_rate}** ({block_cnt:,}/{ov['total']:,})")
    lines.append("")

    # 可疑绕过
    bypass = analysis["suspicious_bypass"]
    if bypass:
        lines.append(f"> ⚠️ **可疑绕过 {len(bypass)} 条**: 高危告警但动作为观察/放行, 可能 CFW 规则盲区")
        lines.append("")

    # 5. TOP 攻击规则
    lines.append(f"## 5. TOP {min(top_n, len(analysis['top_rules']))} 攻击规则")
    lines.append("")
    lines.append("| 规则名 | 告警数 | 源IP数 | 目标IP数 | 最高等级 | 阻断数 | Kill Chain |")
    lines.append("|---|---|---|---|---|---|---|")
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    for rule_name, rs in analysis["top_rules"][:top_n]:
        top_sev = min(rs["severities"].keys(), key=lambda s: sev_rank.get(s, 9)) if rs["severities"] else "-"
        blocked = rs["actions"].get("block", 0)
        kc = kill_chain_phase(rule_name)
        lines.append(
            f"| {rule_name} | {rs['count']:,} | {len(rs['src_ips'])} | "
            f"{len(rs['dst_ips'])} | {sev_map.get(top_sev, top_sev)} | {blocked} | {kc} |"
        )
    lines.append("")

    # 6. TOP 攻击源IP
    lines.append(f"## 6. TOP {min(top_n, len(analysis['top_src_ips']))} 攻击源IP")
    lines.append("")
    lines.append("| 源IP | 告警数 | 规则数 | 目标数 | 主要方向 | 最高等级 | 阻断率 | 首次 | 最新 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for ip, ss in analysis["top_src_ips"][:top_n]:
        top_sev = min(ss["severities"].keys(), key=lambda s: sev_rank.get(s, 9)) if ss["severities"] else "-"
        top_dir = max(ss["directions"].items(), key=lambda x: x[1])[0] if ss["directions"] else "-"
        total = ss["count"]
        blocked = ss["actions"].get("block", 0)
        br = f"{blocked * 100 / max(total, 1):.0f}%"
        first_t = (ss["first_time"] or "")[:19]
        last_t = (ss["last_time"] or "")[:19]
        lines.append(
            f"| `{ip}` | {total:,} | {len(ss['rules'])} | {len(ss['dst_ips'])} | "
            f"{dir_map.get(top_dir, top_dir)} | {sev_map.get(top_sev, top_sev)} | {br} | "
            f"{first_t} | {last_t} |"
        )
    lines.append("")

    # 7. TOP 被攻击目标IP
    lines.append(f"## 7. TOP {min(top_n, len(analysis['top_dst_ips']))} 被攻击目标IP")
    lines.append("")
    lines.append("| 目标IP | 被攻击数 | 攻击源IP数 | 命中规则数 | 最高等级 |")
    lines.append("|---|---|---|---|---|")
    for ip, ds in analysis["top_dst_ips"][:top_n]:
        top_sev = min(ds["severities"].keys(), key=lambda s: sev_rank.get(s, 9)) if ds["severities"] else "-"
        lines.append(
            f"| `{ip}` | {ds['count']:,} | {len(ds['src_ips'])} | "
            f"{len(ds['rules'])} | {sev_map.get(top_sev, top_sev)} |"
        )
    lines.append("")

    # 8. 多向量攻击源IP
    if analysis["multi_rule_srcs"]:
        lines.append("## 8. 多向量攻击源IP (命中 ≥ 3 条规则)")
        lines.append("")
        lines.append("| 源IP | 命中规则数 | 告警数 | 规则列表 |")
        lines.append("|---|---|---|---|")
        for ip, ss in analysis["multi_rule_srcs"][:20]:
            rules_str = ", ".join(sorted(ss["rules"]))
            if len(rules_str) > 80:
                rules_str = rules_str[:77] + "..."
            lines.append(f"| `{ip}` | {len(ss['rules'])} | {ss['count']:,} | {rules_str} |")
        lines.append("")

    # 9. 出站高危告警 (可能失陷主机)
    if analysis["outbound_high"]:
        lines.append(f"## 9. 出站高危告警 ({len(analysis['outbound_high'])} 条, 可能失陷主机外连)")
        lines.append("")
        lines.append("> ⚠️ 出站方向的高危告警, 内部主机可能已失陷并外连 C2 / 外泄数据")
        lines.append("")
        lines.append("| 源IP(内部) | 目标IP(外部) | 规则 | 等级 | 动作 | 时间 |")
        lines.append("|---|---|---|---|---|---|")
        seen_ips = set()
        for rec in analysis["outbound_high"][:top_n]:
            p = rec.get("parsed", {})
            src = p.get("src_ip", "?")
            if src in seen_ips:
                continue
            seen_ips.add(src)
            lines.append(
                f"| `{src}` | `{p.get('dst_ip', '?')}` | {p.get('rule_name', '?')} | "
                f"{sev_map.get(p.get('severity', ''), '?')} | "
                f"{act_map.get(p.get('action', ''), '?')} | "
                f"{(p.get('event_time') or '')[:19]} |"
            )
        lines.append("")

    # 10. 处置建议
    lines.append("## 10. 处置建议")
    lines.append("")

    # 高频攻击源IP
    top_src = analysis["top_src_ips"][:5]
    if top_src:
        lines.append("### 10.1 高频攻击源IP (建议加黑)")
        lines.append("")
        for ip, ss in top_src:
            lines.append(
                f"- [ ] **`{ip}`**: {ss['count']:,} 次告警, "
                f"命中 {len(ss['rules'])} 条规则, "
                f"攻击 {len(ss['dst_ips'])} 个目标 → 建议在 CFW/安全组 永久加黑"
            )
        lines.append("")

    # 出站高危
    if analysis["outbound_high"]:
        lines.append("### 10.2 出站高危告警 (可能失陷主机, 最高优先级)")
        lines.append("")
        outbound_ips = set()
        for rec in analysis["outbound_high"]:
            p = rec.get("parsed", {})
            outbound_ips.add(p.get("src_ip"))
        for ip in sorted(outbound_ips)[:10]:
            if ip:
                lines.append(
                    f"- [ ] ⚠️ **`{ip}`**: 出站高危告警, 可能已失陷 → "
                    f"立即隔离主机 + 取证 (进程/网络/文件) + 查主机安全 (CWP) 告警"
                )
        lines.append("")

    # 可疑绕过
    if bypass:
        lines.append(f"### 10.3 可疑绕过 ({len(bypass)} 条高危观察/放行)")
        lines.append("")
        lines.append("- [ ] 检查 CFW 规则配置, 高危告警不应设为观察/放行")
        lines.append("- [ ] 确认是否为业务误报导致手动放行")
        lines.append("")

    # 多向量攻击
    multi_rule = analysis["multi_rule_srcs"][:5]
    if multi_rule:
        lines.append("### 10.4 多向量攻击源IP (建议重点排查)")
        lines.append("")
        for ip, ss in multi_rule:
            lines.append(
                f"- [ ] **`{ip}`**: 命中 {len(ss['rules'])} 条规则 (多向量攻击) → "
                f"建议拉取御界/天幕/主机安全关联告警, 确认是否已突破边界"
            )
        lines.append("")

    # 11. L2 关联建议
    lines.append("## 11. L2 关联建议")
    lines.append("")
    lines.append("```yaml")
    lines.append("correlation:")
    lines.append("  product: cfw")
    lines.append("  pivot_keys:")
    for ip, _ in top_src[:3]:
        lines.append(f"    - ip: \"{ip}\"")
    lines.append("  time_window_min: 60")
    lines.append('  rationale: "CFW阻断的源IP, 在御界/天幕/主机安全/WAF是否有对应检测告警"')
    lines.append("  cross_product:")
    lines.append("    - yujie: 查 src_ip 是否有流量层检测告警 (C2/隧道/扫描)")
    lines.append("    - tianmu: 查 src_ip 是否有网络层阻断 (双重防护验证)")
    lines.append("    - waf: 查 src_ip 是否有应用层攻击 (SQL注入/XSS)")
    lines.append("    - cwp: 查 dst_ip 是否有主机入侵告警 (攻击是否已突破边界)")
    if analysis["outbound_high"]:
        lines.append("  special:")
        lines.append('    - "出站高危告警: 查 src_ip(内部) 在 cwp 是否有失陷告警"')
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ==================== Case 渲染 (对齐 L2 parse_case_md) ====================

def aggregate_by_attacker(records: list[dict]) -> list[dict]:
    """按攻击源IP聚合记录, 返回每个攻击者的聚合 case"""
    by_ip: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        p = rec.get("parsed", {})
        ip = p.get("src_ip") or p.get("real_attacker_ip")
        if ip:
            by_ip[ip].append(rec)

    cases = []
    for ip, recs in by_ip.items():
        rule_names = Counter()
        dst_ips = set()
        actions = Counter()
        severities = Counter()
        directions = Counter()
        appids = set()
        times = []

        for rec in recs:
            p = rec.get("parsed", {})
            rn = p.get("rule_name") or p.get("rule_id") or "未知"
            rule_names[rn] += 1
            if p.get("dst_ip"):
                dst_ips.add(p["dst_ip"])
            actions[p.get("action", "")] += 1
            severities[p.get("severity", "")] += 1
            directions[p.get("direction", "")] += 1
            if p.get("appid"):
                appids.add(p["appid"])
            if p.get("event_time"):
                times.append(p["event_time"])

        top_rule = rule_names.most_common(1)[0][0] if rule_names else "未知"
        times.sort()
        first_time = times[0] if times else None
        last_time = times[-1] if times else None

        cases.append({
            "attacker_ip": ip,
            "records": recs,
            "total_count": len(recs),
            "rule_names": rule_names,
            "top_rule": top_rule,
            "dst_ips": dst_ips,
            "actions": actions,
            "severities": severities,
            "directions": directions,
            "appids": appids,
            "first_time": first_time,
            "last_time": last_time,
        })

    cases.sort(key=lambda c: c["total_count"], reverse=True)
    return cases


def render_case_md(case: dict) -> str:
    """渲染单个攻击者 case .md (供 L2 l2_correlate.py 消费)

    格式对齐 L2 的 parse_case_md 解析逻辑:
      - case_id 以 cfw_ 开头 → product=cfw
      - 包含 **威胁类型** / **置信度** / **Kill Chain 阶段**
      - 包含 | 源 IP | / | 目的 IP:端口 | / | 事件时间 | / | 告警名称 |

    安全约束: 不输出 payload 原文
    """
    ip = case["attacker_ip"]
    top_rule = case["top_rule"]
    kc_phase = kill_chain_phase(top_rule)
    total = case["total_count"]

    # 威胁类型 + 置信度
    blocked = case["actions"].get("block", 0)
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    top_sev = min(case["severities"].keys(), key=lambda s: sev_rank.get(s, 9)) if case["severities"] else "info"
    sev_map = {"critical": "严重", "high": "高危", "medium": "中危", "low": "低危", "info": "信息"}

    # 出站告警提高优先级
    outbound_cnt = case["directions"].get("outbound", 0)
    is_outbound = outbound_cnt > 0

    if is_outbound:
        threat_type = f"CFW出站告警 (可能失陷主机外连, {total}次)"
        confidence = 0.95
    elif blocked == total:
        threat_type = f"CFW入侵防御告警 (已阻断, {total}次)"
        confidence = 1.0
    elif blocked > 0:
        threat_type = f"CFW入侵防御告警 (部分阻断, {blocked}/{total}次)"
        confidence = 0.9
    else:
        threat_type = f"CFW入侵防御告警 (观察/放行, {total}次)"
        confidence = 0.7

    # case_id
    safe_ip = ip.replace(".", "_").replace(":", "_")
    case_id = f"cfw_r{hash(ip) % 100000:05d}_{safe_ip}"

    lines = []
    lines.append(f"# CFW 入侵防御告警事件 - {case_id}")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 来源: CFW eventLog (按攻击源IP聚合)")
    lines.append("")

    # 1. 基础信息 (格式对齐 L2 parse_case_md)
    lines.append("## 1. 基础信息")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 事件时间 | {case['last_time'] or '?'} |")
    lines.append(f"| 告警名称 | {top_rule} (CFW IPS规则) |")
    lines.append(f"| 源 IP | {ip} |")
    # 取第一条有 dst_ip 的记录
    first_dst = next((r["parsed"].get("dst_ip") for r in case["records"] if r.get("parsed", {}).get("dst_ip")), "-")
    first_dport = next((r["parsed"].get("dst_port") for r in case["records"] if r.get("parsed", {}).get("dst_port")), "-")
    lines.append(f"| 目的 IP:端口 | {first_dst}:{first_dport} |")
    lines.append(f"| 告警次数 | {total} |")
    lines.append(f"| 阻断次数 | {blocked} |")
    lines.append(f"| 最高等级 | {sev_map.get(top_sev, top_sev)} |")
    dir_map = {"inbound": "入站", "outbound": "出站"}
    main_dir = max(case["directions"].items(), key=lambda x: x[1])[0] if case["directions"] else "unknown"
    lines.append(f"| 主要方向 | {dir_map.get(main_dir, main_dir)} |")
    if case["appids"]:
        lines.append(f"| AppId | {', '.join(sorted(case['appids'])[:3])} |")
    lines.append("")

    # 2. 威胁判定 (对齐 L2 解析格式)
    lines.append("## 2. 威胁判定")
    lines.append("")
    lines.append(f"- **威胁类型**: {threat_type}")
    lines.append(f"- **TTP**: -")
    lines.append(f"- **置信度**: {confidence}")
    lines.append(f"- **Kill Chain 阶段**: {kc_phase}")
    lines.append("")

    # 判定依据
    lines.append("**判定依据**:")
    lines.append(f"- 攻击源IP `{ip}` 共触发 {total} 次 CFW 告警")
    lines.append(f"- 主要规则: {top_rule}")
    lines.append(f"- 涉及 {len(case['dst_ips'])} 个目标IP")
    lines.append(f"- 动作分布: {', '.join(f'{k}:{v}' for k, v in case['actions'].most_common())}")
    if is_outbound:
        lines.append(f"- ⚠️ 含 {outbound_cnt} 次出站告警, 可能是失陷主机外连")
    lines.append("")

    # 3. 规则分布
    lines.append("## 3. 命中规则分布")
    lines.append("")
    lines.append("| 规则 | 次数 | Kill Chain 阶段 |")
    lines.append("|---|---|---|")
    for rn, cnt in case["rule_names"].most_common(10):
        lines.append(f"| {rn} | {cnt} | {kill_chain_phase(rn)} |")
    lines.append("")

    # 4. 处置建议
    lines.append("## 4. 处置建议")
    lines.append("")
    if is_outbound:
        lines.append(f"- [ ] ⚠️ **立即隔离主机** `{ip}`: 出站告警可能已失陷, 立即隔离 + 取证")
        lines.append(f"- [ ] 拉取 `{ip}` 在主机安全 (CWP) 的告警, 确认是否已失陷")
    else:
        lines.append(f"- [ ] **阻断攻击者 IP**: CFW/安全组 阻断 `{ip}` 的所有入站流量")
    lines.append(f"- [ ] **拉取历史**: 在 SOC/御界/主机安全/WAF 中搜索 `{ip}` 的全部历史告警")
    lines.append(f"- [ ] **威胁情报查询**: 查 `{ip}` 是否在已知 IOC 库")
    lines.append("")

    # 5. 关联建议 (L2 消费)
    lines.append("## 5. 关联建议 (供 L2 消费)")
    lines.append("")
    lines.append("```yaml")
    lines.append("threat:")
    lines.append(f'  threat_type: "{threat_type}"')
    lines.append(f"  confidence: {confidence}")
    lines.append(f'  kill_chain_phase: "{kc_phase}"')
    lines.append("  iocs:")
    lines.append(f'    ips: ["{ip}"]')
    if first_dst and first_dst != "-":
        lines.append(f'    dst_ips: ["{first_dst}"]')
    lines.append("  correlation_hints:")
    lines.append(f'    pivot_keys: ["{ip}"]')
    lines.append("    time_window_min: 60")
    lines.append('    rationale: "CFW阻断的源IP, 在御界/天幕/主机安全/WAF是否有对应检测告警"')
    lines.append("  cross_product:")
    lines.append("    - yujie: 查 src_ip 是否有流量层检测告警 (C2/隧道/扫描)")
    lines.append("    - tianmu: 查 src_ip 是否有网络层阻断 (双重防护验证)")
    lines.append("    - waf: 查 src_ip 是否有应用层攻击 (SQL注入/XSS)")
    lines.append("    - cwp: 查 dst_ip 是否有主机入侵告警 (攻击是否已突破边界)")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def emit_cases(cases: list[dict], out_dir: Path) -> int:
    """输出 per-attacker case .md 文件 (供 L2 消费)"""
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for case in cases:
        ip = case["attacker_ip"]
        safe_ip = ip.replace(".", "_").replace(":", "_")
        case_id = f"cfw_r{hash(ip) % 100000:05d}_{safe_ip}"
        md = render_case_md(case)
        (out_dir / f"{case_id}.md").write_text(md, encoding="utf-8")
        n += 1
    return n


# ==================== 主入口 ====================

def main():
    ap = argparse.ArgumentParser(
        description="L1 CFW 入侵防御告警分析 (消费 L0 JSONL → 分析报告 + case)",
    )
    ap.add_argument("l0_jsonl", type=Path, help="L0 输出的 JSONL 文件")
    ap.add_argument("--out", type=Path, default=None,
                    help="输出报告目录 (默认 stdout)")
    ap.add_argument("--top", type=int, default=20,
                    help="TOP N 显示数量 (默认 20)")
    ap.add_argument("--emit-cases", type=Path, default=None,
                    help="输出 per-attacker case .md 目录 (供 L2 l2_correlate.py 消费)")
    ap.add_argument("--min-count", type=int, default=1,
                    help="case 输出的最小告警次数阈值 (默认 1)")
    ap.add_argument("--max-cases", type=int, default=None,
                    help="case 输出的最大数量 (默认无限制)")
    args = ap.parse_args()

    if not args.l0_jsonl.exists():
        print(f"[ERR] L0 JSONL 不存在: {args.l0_jsonl}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 加载: {args.l0_jsonl}", file=sys.stderr)
    records = load_records(args.l0_jsonl)
    print(f"[INFO] CFW 记录: {len(records)} 条", file=sys.stderr)

    if not records:
        print("[ERR] 无 CFW 记录 (product=cfw)", file=sys.stderr)
        sys.exit(2)

    # 1. 聚合分析
    print("[INFO] 聚合分析中...", file=sys.stderr)
    analysis = aggregate_analysis(records)

    ov = analysis["overview"]
    print(f"[STATS] 总告警={ov['total']:,}  "
          f"规则={ov['unique_rules']}  "
          f"源IP={ov['unique_src_ips']}  "
          f"目标IP={ov['unique_dst_ips']}", file=sys.stderr)
    print(f"[STATS] 等级分布={ov['severity_breakdown']}", file=sys.stderr)
    print(f"[STATS] 动作分布={ov['action_breakdown']}", file=sys.stderr)
    print(f"[STATS] 方向分布={ov['direction_breakdown']}", file=sys.stderr)
    if analysis["suspicious_bypass"]:
        print(f"[WARN] 可疑绕过: {len(analysis['suspicious_bypass'])} 条 (高危+观察/放行)", file=sys.stderr)
    if analysis["outbound_high"]:
        print(f"[WARN] 出站高危: {len(analysis['outbound_high'])} 条 (可能失陷主机外连)", file=sys.stderr)

    # 2. 渲染报告
    report = render_report(analysis, args.l0_jsonl.name, args.top)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        md_path = args.out / "report.md"
        md_path.write_text(report, encoding="utf-8")
        print(f"[OK] 报告写出: {md_path}", file=sys.stderr)
    else:
        print(report)

    # 3. 可选: 输出 per-attacker case 文件 (供 L2 消费)
    if args.emit_cases:
        print("[INFO] 按攻击源IP聚合生成 case...", file=sys.stderr)
        cases = aggregate_by_attacker(records)
        cases = [c for c in cases if c["total_count"] >= args.min_count]
        if args.max_cases:
            cases = cases[:args.max_cases]
        n_cases = emit_cases(cases, args.emit_cases)
        print(f"[OK] case 文件写出: {n_cases} 个 → {args.emit_cases}", file=sys.stderr)
        print(f"[STATS] 攻击IP总数: {len(aggregate_by_attacker(records))}, "
              f"输出case数: {n_cases} (min_count={args.min_count})", file=sys.stderr)


if __name__ == "__main__":
    main()
