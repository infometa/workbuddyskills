#!/usr/bin/env python3
"""L1 天幕 (安全治理) 阻断日志分析 CLI

输入: L0 输出的 JSONL (soc-alert-pipeline/l0_parse.py --product tianmu 生成)
输出: 阻断分析报告 (Markdown)

与 cwp/yujie 的 L1 不同:
  - 天幕数据是聚合统计 (每行 = 规则+源IP+目标IP 的累计阻断)
  - 分析逻辑是批量聚合, 不是逐条 TTP 检测
  - 输出是单个报告, 不是 per-event 案例文件

分析维度:
  1. 阻断概览 (总阻断次数 / 规则数 / 源IP数 / 目标IP数)
  2. TOP 阻断规则 (哪些规则命中最多)
  3. 攻击者画像 (TOP 源IP / 多规则命中 / 多目标攻击)
  4. 被攻击目标 (TOP 目标IP)
  5. 误报识别 (黑名单阻断 vs 规则阻断)
  6. 处置建议 (加黑 / 放行 / 调规则)

用法:
  python3 l1_tianmu_analyze.py <l0_jsonl_path> --out report.md
  python3 l1_tianmu_analyze.py <l0_jsonl_path> --top 20 --out report.md
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load_records(jsonl_path: Path) -> list[dict]:
    """加载 L0 JSONL, 只保留 tianmu 记录"""
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("product") != "tianmu":
                continue
            if rec.get("parse_status") not in ("ok", "partial"):
                continue
            records.append(rec)
    return records


def aggregate_analysis(records: list[dict]) -> dict:
    """批量聚合分析

    Returns:
        分析结果 dict, 包含概览 + TOP 统计
    """
    total_block_count = 0
    rule_stats: dict[str, dict] = defaultdict(lambda: {
        "block_count": 0, "src_ips": set(), "dst_ips": set(),
        "first_time": None, "last_time": None, "sources": set(),
    })
    src_ip_stats: dict[str, dict] = defaultdict(lambda: {
        "block_count": 0, "rules": set(), "dst_ips": set(),
        "first_time": None, "last_time": None,
    })
    dst_ip_stats: dict[str, dict] = defaultdict(lambda: {
        "block_count": 0, "src_ips": set(), "rules": set(),
    })
    source_stats: dict[str, int] = defaultdict(int)  # 告警来源 → block_count
    all_times = []

    for rec in records:
        p = rec.get("parsed", {})
        bc = p.get("block_count", 0) or 0
        total_block_count += bc

        rule_id = p.get("rule_id", "未知")
        src_ip = p.get("src_ip", "未知")
        dst_ip = p.get("dst_ip", "未知")
        alert_source = p.get("alert_source", "未知")
        first_t = p.get("first_alert_time")
        last_t = p.get("last_alert_time") or p.get("event_time")

        # 规则统计
        rs = rule_stats[rule_id]
        rs["block_count"] += bc
        rs["src_ips"].add(src_ip)
        rs["dst_ips"].add(dst_ip)
        rs["sources"].add(alert_source)
        if first_t and (rs["first_time"] is None or first_t < rs["first_time"]):
            rs["first_time"] = first_t
        if last_t and (rs["last_time"] is None or last_t > rs["last_time"]):
            rs["last_time"] = last_t

        # 源IP统计
        ss = src_ip_stats[src_ip]
        ss["block_count"] += bc
        ss["rules"].add(rule_id)
        ss["dst_ips"].add(dst_ip)
        if first_t and (ss["first_time"] is None or first_t < ss["first_time"]):
            ss["first_time"] = first_t
        if last_t and (ss["last_time"] is None or last_t > ss["last_time"]):
            ss["last_time"] = last_t

        # 目标IP统计
        ds = dst_ip_stats[dst_ip]
        ds["block_count"] += bc
        ds["src_ips"].add(src_ip)
        ds["rules"].add(rule_id)

        # 告警来源
        source_stats[alert_source] += bc

        if last_t:
            all_times.append(last_t)

    # 排序
    top_rules = sorted(rule_stats.items(), key=lambda x: -x[1]["block_count"])
    top_src_ips = sorted(src_ip_stats.items(), key=lambda x: -x[1]["block_count"])
    top_dst_ips = sorted(dst_ip_stats.items(), key=lambda x: -x[1]["block_count"])

    # 多规则命中源IP (一个IP命中 >= 3 条规则 = 多向量攻击)
    multi_rule_srcs = [
        (ip, s) for ip, s in src_ip_stats.items()
        if len(s["rules"]) >= 3
    ]
    multi_rule_srcs.sort(key=lambda x: -len(x[1]["rules"]))

    # 多目标攻击源IP (一个IP攻击 >= 3 个目标)
    multi_dst_srcs = [
        (ip, s) for ip, s in src_ip_stats.items()
        if len(s["dst_ips"]) >= 3
    ]
    multi_dst_srcs.sort(key=lambda x: -len(x[1]["dst_ips"]))

    time_range = None
    if all_times:
        time_range = (min(all_times), max(all_times))

    return {
        "overview": {
            "total_records": len(records),
            "total_block_count": total_block_count,
            "unique_rules": len(rule_stats),
            "unique_src_ips": len(src_ip_stats),
            "unique_dst_ips": len(dst_ip_stats),
            "time_range": time_range,
            "source_breakdown": dict(source_stats),
        },
        "top_rules": top_rules,
        "top_src_ips": top_src_ips,
        "top_dst_ips": top_dst_ips,
        "multi_rule_srcs": multi_rule_srcs,
        "multi_dst_srcs": multi_dst_srcs,
    }


def assess_false_positive(rule_id: str, alert_source: str, block_count: int) -> dict:
    """误报识别: 评估阻断是否合理

    天幕规则分类:
      - GB0xxxx: 黑名单类 (已知恶意IP, 阻断合理)
      - GB1xxxx: 规则类 (特征匹配, 需评估)
      - GB2xxxx: 行为类 (频率/异常行为, 需评估)
    """
    fp_risk = "low"
    reason = ""

    if alert_source == "黑名单":
        fp_risk = "low"
        reason = "黑名单阻断, 已知恶意IP, 阻断合理"
    elif rule_id.startswith("GB0") or rule_id.startswith("PB0"):
        fp_risk = "low"
        reason = "黑名单类规则 (GB0xxx/PB0xxx), 通常为已知恶意源"
    elif rule_id.startswith("GB1") or rule_id.startswith("PB1"):
        fp_risk = "medium"
        reason = "特征匹配类规则 (GB1xxx/PB1xxx), 需确认是否误报"
    elif rule_id.startswith("GB2") or rule_id.startswith("PB2"):
        fp_risk = "medium"
        reason = "行为类规则 (GB2xxx/PB2xxx), 需确认攻击行为是否真实"
    elif rule_id.startswith("GB3"):
        fp_risk = "medium"
        reason = "扩展规则类 (GB3xxx), 需人工确认"
    else:
        fp_risk = "unknown"
        reason = "未知规则类型, 需人工确认"

    return {"fp_risk": fp_risk, "reason": reason}


def render_report(analysis: dict, source_file: str, top_n: int) -> str:
    """渲染阻断分析报告 (Markdown)"""
    ov = analysis["overview"]
    lines = []

    lines.append("# 天幕安全治理 - 阻断日志分析报告")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 数据来源: {source_file}")
    lines.append("")

    # 1. 阻断概览
    lines.append("## 1. 阻断概览")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 告警记录数 | {ov['total_records']} |")
    lines.append(f"| 总阻断次数 | **{ov['total_block_count']:,}** |")
    lines.append(f"| 命中规则数 | {ov['unique_rules']} |")
    lines.append(f"| 攻击源IP数 | {ov['unique_src_ips']} |")
    lines.append(f"| 被攻击目标IP数 | {ov['unique_dst_ips']} |")
    if ov["time_range"]:
        lines.append(f"| 时间范围 | {ov['time_range'][0]} ~ {ov['time_range'][1]} |")
    lines.append("")

    if ov["source_breakdown"]:
        lines.append("**告警来源分布**:")
        lines.append("")
        lines.append("| 来源 | 阻断次数 |")
        lines.append("|---|---|")
        for src, cnt in sorted(ov["source_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"| {src} | {cnt:,} |")
        lines.append("")

    # 2. TOP 阻断规则
    lines.append(f"## 2. TOP {min(top_n, len(analysis['top_rules']))} 阻断规则")
    lines.append("")
    lines.append("| 规则ID | 阻断次数 | 源IP数 | 目标IP数 | 来源 | 首次 | 最新 | 误报风险 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for rule_id, rs in analysis["top_rules"][:top_n]:
        fp = assess_false_positive(rule_id, ",".join(rs["sources"]), rs["block_count"])
        first_t = (rs["first_time"] or "")[:19]
        last_t = (rs["last_time"] or "")[:19]
        lines.append(
            f"| {rule_id} | {rs['block_count']:,} | {len(rs['src_ips'])} | "
            f"{len(rs['dst_ips'])} | {','.join(rs['sources'])} | "
            f"{first_t} | {last_t} | {fp['fp_risk']} |"
        )
    lines.append("")

    # 3. 攻击者画像 - TOP 源IP
    lines.append(f"## 3. TOP {min(top_n, len(analysis['top_src_ips']))} 攻击源IP")
    lines.append("")
    lines.append("| 源IP | 阻断次数 | 命中规则数 | 攻击目标数 | 首次 | 最新 |")
    lines.append("|---|---|---|---|---|---|")
    for ip, ss in analysis["top_src_ips"][:top_n]:
        first_t = (ss["first_time"] or "")[:19]
        last_t = (ss["last_time"] or "")[:19]
        lines.append(
            f"| `{ip}` | {ss['block_count']:,} | {len(ss['rules'])} | "
            f"{len(ss['dst_ips'])} | {first_t} | {last_t} |"
        )
    lines.append("")

    # 4. 多规则命中源IP (多向量攻击)
    if analysis["multi_rule_srcs"]:
        lines.append("## 4. 多向量攻击源IP (命中 >= 3 条规则)")
        lines.append("")
        lines.append("| 源IP | 命中规则数 | 阻断次数 | 规则列表 |")
        lines.append("|---|---|---|---|")
        for ip, ss in analysis["multi_rule_srcs"][:20]:
            rules_str = ", ".join(sorted(ss["rules"]))
            if len(rules_str) > 80:
                rules_str = rules_str[:77] + "..."
            lines.append(
                f"| `{ip}` | {len(ss['rules'])} | {ss['block_count']:,} | {rules_str} |"
            )
        lines.append("")

    # 5. 多目标攻击源IP
    if analysis["multi_dst_srcs"]:
        lines.append("## 5. 多目标攻击源IP (攻击 >= 3 个目标)")
        lines.append("")
        lines.append("| 源IP | 攻击目标数 | 阻断次数 | 目标列表 |")
        lines.append("|---|---|---|---|")
        for ip, ss in analysis["multi_dst_srcs"][:20]:
            dsts_str = ", ".join(sorted(ss["dst_ips"]))
            if len(dsts_str) > 80:
                dsts_str = dsts_str[:77] + "..."
            lines.append(
                f"| `{ip}` | {len(ss['dst_ips'])} | {ss['block_count']:,} | {dsts_str} |"
            )
        lines.append("")

    # 6. 被攻击目标
    lines.append(f"## 6. TOP {min(top_n, len(analysis['top_dst_ips']))} 被攻击目标IP")
    lines.append("")
    lines.append("| 目标IP | 被阻断次数 | 攻击源IP数 | 命中规则数 |")
    lines.append("|---|---|---|---|")
    for ip, ds in analysis["top_dst_ips"][:top_n]:
        lines.append(
            f"| `{ip}` | {ds['block_count']:,} | {len(ds['src_ips'])} | {len(ds['rules'])} |"
        )
    lines.append("")

    # 7. 处置建议
    lines.append("## 7. 处置建议")
    lines.append("")
    top_src = analysis["top_src_ips"][:5] if analysis["top_src_ips"] else []
    if top_src:
        lines.append("### 7.1 高频攻击源IP (建议加黑)")
        lines.append("")
        for ip, ss in top_src:
            lines.append(f"- [ ] **`{ip}`**: 阻断 {ss['block_count']:,} 次, "
                         f"命中 {len(ss['rules'])} 条规则, "
                         f"攻击 {len(ss['dst_ips'])} 个目标 → 建议在安全组/WAF 永久加黑")
        lines.append("")

    medium_fp_rules = [
        (rid, rs) for rid, rs in analysis["top_rules"]
        if assess_false_positive(rid, ",".join(rs["sources"]), rs["block_count"])["fp_risk"] == "medium"
    ]
    if medium_fp_rules:
        lines.append("### 7.2 需人工确认的规则 (可能误报)")
        lines.append("")
        for rid, rs in medium_fp_rules[:10]:
            fp = assess_false_positive(rid, ",".join(rs["sources"]), rs["block_count"])
            lines.append(f"- [ ] **{rid}**: {fp['reason']} "
                         f"(阻断 {rs['block_count']:,} 次, 涉及 {len(rs['src_ips'])} 个源IP)")
        lines.append("")

    multi_rule = analysis["multi_rule_srcs"][:5]
    if multi_rule:
        lines.append("### 7.3 多向量攻击源IP (建议重点排查)")
        lines.append("")
        for ip, ss in multi_rule:
            lines.append(f"- [ ] **`{ip}`**: 命中 {len(ss['rules'])} 条规则 "
                         f"(多向量攻击), 阻断 {ss['block_count']:,} 次 → "
                         f"建议拉取御界/主机安全关联告警, 确认是否已突破边界")
        lines.append("")

    lines.append("### 7.4 L2 关联建议")
    lines.append("")
    lines.append("```yaml")
    lines.append("correlation:")
    lines.append("  product: tianmu")
    lines.append("  pivot_keys:")
    for ip, _ in top_src[:3]:
        lines.append(f"    - ip: \"{ip}\"")
    lines.append("  time_window_min: 60")
    lines.append("  rationale: \"天幕阻断的源IP, 在御界/主机安全是否有对应检测告警\"")
    lines.append("  cross_product:")
    lines.append("    - yujie: 查 src_ip 是否有流量检测告警 (C2/扫描/注入)")
    lines.append("    - cwp: 查 src_ip 是否有主机入侵告警 (如已突破边界)")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def render_case_md(record: dict) -> str:
    """渲染单条天幕记录为 case .md (供 L2 l2_correlate.py 消费)

    格式对齐 L2 的 parse_case_md 解析逻辑:
      - case_id 以 tianmu_ 开头 → product=tianmu
      - 包含 **威胁类型** / **置信度** / **Kill Chain 阶段**
      - 包含 | 源 IP | / | 目的 IP:端口 | / | 事件时间 | / | 告警名称 |
    """
    p = record.get("parsed", {})
    row = record.get("row", 0)
    event_id = f"tianmu_r{row:05d}_{p.get('rule_id', 'unknown')}"

    lines = []
    lines.append(f"# 天幕阻断事件 - {event_id}")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 来源: {record.get('source_file', '?')} row={row}")
    lines.append("")

    # 1. 基础信息 (格式对齐 L2 parse_case_md)
    lines.append("## 1. 基础信息")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 事件时间 | {p.get('event_time', '?')} |")
    lines.append(f"| 告警名称 | {p.get('rule_id', '?')} (天幕阻断规则) |")
    lines.append(f"| 源 IP | {p.get('src_ip', '-')} |")
    lines.append(f"| 目的 IP:端口 | {p.get('dst_ip', '-')}:{p.get('dst_port', '-')} |")
    lines.append(f"| 协议 | {p.get('protocol', '?')} |")
    lines.append(f"| 阻断次数 | {p.get('block_count', 0):,} |")
    lines.append(f"| 告警来源 | {p.get('alert_source', '-')} |")
    lines.append(f"| 状态 | {p.get('status', '-')} |")
    lines.append("")

    # 2. 威胁判定 (对齐 L2 解析格式)
    lines.append("## 2. 威胁判定")
    lines.append("")
    lines.append(f"- **威胁类型**: 网络阻断 (天幕已拦截)")
    lines.append(f"- **TTP**: -")
    lines.append(f"- **置信度**: 1.0")
    lines.append(f"- **Kill Chain 阶段**: Initial Access")
    lines.append("")
    lines.append("**判定依据**:")
    lines.append(f"- 天幕规则 {p.get('rule_id', '?')} 命中并已阻断")
    lines.append(f"- 累计阻断 {p.get('block_count', 0):,} 次")
    lines.append(f"- 告警来源: {p.get('alert_source', '未知')}")
    lines.append("")

    # 3. 处置建议
    lines.append("## 3. 处置建议")
    lines.append("")
    fp = assess_false_positive(p.get("rule_id", ""), p.get("alert_source", ""), p.get("block_count", 0))
    lines.append(f"- 误报风险: **{fp['fp_risk']}** ({fp['reason']})")
    if p.get("src_ip"):
        lines.append(f"- [ ] 在安全组/WAF 加黑源IP `{p['src_ip']}`")
    lines.append(f"- [ ] 确认规则 {p.get('rule_id', '?')} 的阻断效果")
    lines.append("")

    # 4. 关联建议 (L2 消费)
    lines.append("## 4. 关联建议 (供 L2 消费)")
    lines.append("")
    lines.append("```yaml")
    lines.append("threat:")
    lines.append('  threat_type: "网络阻断"')
    lines.append("  confidence: 1.0")
    lines.append('  kill_chain_phase: "Initial Access"')
    lines.append("  iocs:")
    if p.get("src_ip"):
        lines.append(f'    ips: ["{p["src_ip"]}"]')
    if p.get("dst_ip"):
        lines.append(f'    dst_ips: ["{p["dst_ip"]}"]')
    lines.append("  correlation_hints:")
    lines.append(f'    pivot_keys: ["{p.get("src_ip", "")}"]')
    lines.append("    time_window_min: 60")
    lines.append('    rationale: "天幕阻断的源IP, 在御界/主机安全是否有对应检测告警"')
    lines.append("```")
    lines.append("")

    # 5. 附录
    lines.append("## 5. 附录: 原始数据")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({"l0_parsed": p}, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def emit_cases(records: list[dict], out_dir: Path) -> int:
    """输出 per-record case .md 文件 (供 L2 消费)

    Returns:
        写出的 case 文件数
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for rec in records:
        md = render_case_md(rec)
        p = rec.get("parsed", {})
        row = rec.get("row", 0)
        case_id = f"tianmu_r{row:05d}_{p.get('rule_id', 'unknown')}"
        (out_dir / f"{case_id}.md").write_text(md, encoding="utf-8")
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(
        description="L1 天幕阻断日志分析 (消费 L0 JSONL → 阻断分析报告)",
    )
    ap.add_argument("l0_jsonl", type=Path, help="L0 输出的 JSONL 文件")
    ap.add_argument("--out", type=Path, default=None,
                    help="输出报告文件路径 (默认 stdout)")
    ap.add_argument("--top", type=int, default=20,
                    help="TOP N 显示数量 (默认 20)")
    ap.add_argument("--emit-cases", type=Path, default=None,
                    help="输出 per-record case .md 目录 (供 L2 l2_correlate.py 消费)")
    args = ap.parse_args()

    if not args.l0_jsonl.exists():
        print(f"[ERR] L0 JSONL 不存在: {args.l0_jsonl}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 加载: {args.l0_jsonl}", file=sys.stderr)
    records = load_records(args.l0_jsonl)
    print(f"[INFO] 天幕记录: {len(records)} 条", file=sys.stderr)

    if not records:
        print("[ERR] 无天幕记录 (product=tianmu)", file=sys.stderr)
        sys.exit(2)

    print("[INFO] 聚合分析中...", file=sys.stderr)
    analysis = aggregate_analysis(records)

    ov = analysis["overview"]
    print(f"[STATS] 总阻断={ov['total_block_count']:,}  "
          f"规则={ov['unique_rules']}  "
          f"源IP={ov['unique_src_ips']}  "
          f"目标IP={ov['unique_dst_ips']}", file=sys.stderr)

    report = render_report(analysis, args.l0_jsonl.name, args.top)

    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"[OK] 报告写出: {args.out}", file=sys.stderr)
    else:
        print(report)

    # 可选: 输出 per-record case 文件 (供 L2 消费)
    if args.emit_cases:
        n_cases = emit_cases(records, args.emit_cases)
        print(f"[OK] case 文件写出: {n_cases} 个 → {args.emit_cases}", file=sys.stderr)


if __name__ == "__main__":
    main()
