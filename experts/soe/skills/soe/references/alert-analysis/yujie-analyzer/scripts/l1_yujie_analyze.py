#!/usr/bin/env python3
"""L1 御界分析 CLI

输入: L0 输出的 JSONL (soc-alert-pipeline/l0_parse.py 生成)
输出: cases/{event_id}.md 案例文档

用法:
  python3 l1_yujie_analyze.py <l0_jsonl_path> --out cases/
  python3 l1_yujie_analyze.py <l0_jsonl_path> --limit 5 --pretty
"""
from __future__ import annotations
import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# 允许独立运行
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ttp_detectors import (
    detect_c2_beacon,
    detect_tunnel,
    detect_lateral_movement,
    detect_exfiltration,
)
from nat_resolve import resolve_nat_chain


def analyze_event(record: dict) -> dict | None:
    """分析单条 L0 输出, 返回威胁判定

    Args:
        record: L0 输出的 dict (含 parsed / ocsf / row / product)

    Returns:
        包含 nat_resolution + primary threat + all detections 的 dict
    """
    parsed = record.get("parsed", {})
    if not parsed:
        return None

    # 1. NAT 还原
    nat = resolve_nat_chain(parsed)

    # 2. 4 个 detector
    nat_bonus = nat.get("nat_suspicion_bonus", 0.0)

    detectors = [
        ("c2_beacon", detect_c2_beacon, (parsed, nat_bonus)),
        ("tunnel", detect_tunnel, (parsed, nat_bonus)),
        ("lateral_movement", detect_lateral_movement, (parsed, nat_bonus)),
        ("exfiltration", detect_exfiltration, (parsed, nat_bonus)),
    ]

    results = []
    for name, detector, args in detectors:
        try:
            r = detector(*args)
            if r:
                r["detector"] = name
                results.append(r)
        except Exception as e:
            results.append({
                "detector": name,
                "error": f"{type(e).__name__}: {e}",
            })

    valid = [r for r in results if r.get("confidence", 0) >= 0.5]
    if not valid:
        return {
            "nat_resolution": nat,
            "primary": None,
            "all_detections": results,
        }

    best = max(valid, key=lambda r: r.get("confidence", 0))
    return {
        "nat_resolution": nat,
        "primary": best,
        "all_detections": results,
    }


def make_event_id(record: dict) -> str:
    row = record.get("row", 0)
    return f"yujie_r{row:05d}_{uuid.uuid4().hex[:8]}"


def render_case_md(event_id: str, record: dict, analysis: dict) -> str:
    """渲染案例文档"""
    parsed = record.get("parsed", {})
    ocsf = record.get("ocsf", {})
    nat = analysis.get("nat_resolution", {})
    primary = analysis.get("primary", {})

    lines = []
    lines.append(f"# 御界事件分析 - {event_id}")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 来源: {record.get('source_file', '?')} row={record.get('row', '?')}")
    lines.append("")

    # 1. 事件元数据
    lines.append("## 1. 事件元数据")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 规则 | {parsed.get('rule_name', '?')} (ID: {parsed.get('rule_id', '?')}) |")
    lines.append(f"| 严重度 (OCSF) | {ocsf.get('severity', '-')} |")
    lines.append(f"| 置信度 (OCSF) | {ocsf.get('confidence', '-')} |")
    lines.append(f"| 御界 score | {parsed.get('score', '-')} |")
    lines.append(f"| DPI 协议 | {parsed.get('app_proto', '-')} |")
    lines.append(f"| 事件时间 | {parsed.get('event_timestamp', '-')} |")
    lines.append("")

    # 2. 网络五元组 (OCSF vs NAT 还原)
    lines.append("## 2. 网络五元组 (OCSF vs NAT 还原)")
    lines.append("")
    lines.append("| 视角 | 源 | 目的 |")
    lines.append("|---|---|---|")
    lines.append(f"| **OCSF 透出** | {parsed.get('src_ip', '-')}:{parsed.get('src_port', '-')} | {parsed.get('dst_ip', '-')}:{parsed.get('dst_port', '-')} |")
    lines.append(f"| **真实 (NAT 还原)** | {nat.get('real_attacker_ip', '-')}:{parsed.get('src_port', '-')} | {nat.get('real_victim_ip', '-')}:{parsed.get('dst_port', '-')} |")
    lines.append("")
    if nat.get("ip_discrepancy"):
        lines.append(f"> ⚠️ **IP 不一致**: 攻击者/受害者隐藏在 NAT 后. 性质可能从'内网违规'升级为'**外部入侵**'")
        lines.append("")

    # 2.5 受害资产信息 (从 L0 asset.victim_asset 提取, 由 asset_resolver 关联)
    asset = record.get("asset", {}) or {}
    victim_asset = asset.get("victim_asset") or asset.get("dst_asset") or asset.get("src_asset") or {}
    if victim_asset:
        match_method = asset.get("match_method", "unknown")
        method_label = {
            "ip_vpcid": "精确匹配 (IP + VPCID)",
            "ip_appid": "精确匹配 (IP + AppID)",
            "ip_only": "仅 IP 匹配 (跨租户风险)",
            "hostname": "主机名匹配",
            "vpcid_only": "⚠️ 占位匹配 (VPC 反查, IP 未命中)",
        }.get(match_method, match_method)
        lines.append("## 2.5 受害资产 / 租户归属 (核心: AppID)")
        lines.append("")
        lines.append(f"> 匹配方式: **{method_label}**")
        lines.append("")

        # 1) 租户维度 (AppID 优先) - 区分谁家的资产
        lines.append("### 🏢 租户归属")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|---|---|")
        lines.append(f"| **AppID (租户)** | **`{victim_asset.get('appid', '-')}`** |")
        lines.append(f"| 业务系统 | {victim_asset.get('business_system', '-')} |")
        lines.append(f"| 资产类型 | {victim_asset.get('asset_type', '-')} |")
        lines.append(f"| 重要性 | {victim_asset.get('importance', '-')} |")
        lines.append(f"| 负责人 | {victim_asset.get('owner', '-')} |")
        lines.append("")

        # 2) 网络维度 (VPC) - 区分哪个 VPC
        lines.append("### 🌐 网络位置 (VPC)")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|---|---|")
        lines.append(f"| 受害 IP (NAT还原) | {nat.get('real_victim_ip', '-')} |")
        vpcid = victim_asset.get('vpcid', '-')
        vpc_name = victim_asset.get('vpc_name', '')
        vpc_display = f"`{vpcid}` ({vpc_name})" if vpc_name and vpc_name != '-' else f"`{vpcid}`"
        lines.append(f"| **VPC ID** | **{vpc_display}** |")
        lines.append(f"| 可用区 | {victim_asset.get('zone', '-')} |")
        lines.append("")

        # 3) 主机信息
        lines.append("### 🖥️ 主机信息")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|---|---|")
        lines.append(f"| 主机名 | {victim_asset.get('hostname', '-')} |")
        lines.append(f"| 操作系统 | {victim_asset.get('os', '-')} |")
        lines.append(f"| 实例 ID | {victim_asset.get('instance_id', '-')} |")
        lines.append("")

    # 3. NAT 链分析
    lines.append("## 3. NAT 链分析")
    lines.append("")
    lines.append(f"- **封装链**: {' → '.join(nat.get('nat_chain', [])) or '(无)'}")
    lines.append(f"- **攻击者 IP 性质**: {nat.get('attacker_class', '?')} ({nat.get('real_attacker_ip', '-')})")
    lines.append(f"- **受害 IP 性质**: {nat.get('victim_class', '?')} ({nat.get('real_victim_ip', '-')})")
    lines.append(f"- **还原可信度**: {nat.get('trust_level', '?')}")
    lines.append(f"- **分析**: {nat.get('rationale', '-')}")
    if nat.get("nat_suspicion_reasons"):
        lines.append("- **异常信号**:")
        for r in nat["nat_suspicion_reasons"]:
            lines.append(f"  - {r}")
    lines.append("")

    # 4. 协议 + 包解析
    if parsed.get("packet_header") or parsed.get("flow_stats"):
        lines.append("## 4. 协议与流量特征")
        lines.append("")
        pkt = parsed.get("packet_header", {})
        if pkt:
            lines.append("**包结构**:")
            lines.append("```json")
            lines.append(json.dumps(pkt, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
        flow = parsed.get("flow_stats", {})
        if flow:
            lines.append("**流统计**:")
            lines.append("```json")
            lines.append(json.dumps(flow, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

    # 5. 威胁判定
    lines.append("## 5. 威胁判定")
    lines.append("")
    if primary:
        lines.append(f"- **威胁类型**: {primary.get('threat_type')}")
        lines.append(f"- **TTP**: {primary.get('ttp')} ({primary.get('ttp_name')})")
        lines.append(f"- **置信度**: {primary.get('confidence')}")
        lines.append(f"- **Kill Chain 阶段**: {primary.get('kill_chain_phase')}")
        lines.append(f"- **检测器**: {primary.get('detector')}")
        lines.append("")
        lines.append("**判定依据**:")
        for reason in primary.get("reasons", []):
            lines.append(f"- {reason}")
        lines.append("")
    else:
        lines.append("- 未命中已知威胁场景 (但已执行全部 detector)")
        lines.append("")

    # 所有检测器结果
    all_dets = analysis.get("all_detections", [])
    if len(all_dets) > 1:
        lines.append("**所有检测器结果**:")
        lines.append("")
        for d in all_dets:
            det = d.get("detector", "?")
            if "error" in d:
                lines.append(f"- `{det}`: ERROR - {d['error']}")
            elif d.get("confidence", 0) > 0:
                lines.append(f"- `{det}`: {d.get('threat_type')} (conf={d.get('confidence')})")
            else:
                lines.append(f"- `{det}`: 未命中")
        lines.append("")

    # 6. 处置建议
    lines.append("## 6. 处置建议")
    lines.append("")
    if primary:
        threat_type = primary.get("threat_type", "")
        if "C2" in threat_type or "Beacon" in threat_type:
            lines.extend([
                f"- [ ] **拉取历史**: 御界中 real_attacker_ip={nat.get('real_attacker_ip')} 的所有告警",
                f"- [ ] **关联主机**: cwp-analyzer 拉取 real_victim_ip={nat.get('real_victim_ip')} 的 CWP 告警 (看是否已失陷)",
                "- [ ] **隔离受害主机**: CWP 隔离网络",
                f"- [ ] **阻断外联**: 安全组阻断到 {nat.get('real_attacker_ip')} 的所有流量",
            ])
        elif "隧道" in threat_type or "代理" in threat_type:
            lines.extend([
                "- [ ] **确认业务**: 询问业务方是否合法使用该 VPN/代理",
                "- [ ] **非法: 阻断**: 阻断端口 + 隔离主机",
                f"- [ ] **关联主机**: cwp 拉取 {nat.get('real_victim_ip')} 的进程, 是否有 VPN 客户端 (wireguard/openvpn)",
                "- [ ] **拉历史**: 时间窗 ±30min 内同 victim 的所有告警",
                "- [ ] **跨 VPC 隧道**: 联系云网络管理员确认是否合法 VPC 对等",
            ])
        elif "横向移动" in threat_type:
            lines.extend([
                "- [ ] **L2 聚合**: 同一 attacker 短时间多 dst_port → 端口扫描模式",
                f"- [ ] **隔离源**: real_attacker_ip={nat.get('real_attacker_ip')}",
                "- [ ] **拉受害主机**: cwp 看源主机的进程 / 命令",
            ])
        elif "外传" in threat_type:
            lines.extend([
                f"- [ ] **阻断外联**: real_attacker_ip={nat.get('real_attacker_ip')}",
                f"- [ ] **隔离受害**: real_victim_ip={nat.get('real_victim_ip')}",
                "- [ ] **关联主机**: cwp 拉受害主机的进程 / 文件系统",
            ])
    else:
        lines.append("- 无明显威胁场景, 建议保留待人工 review")
    lines.append("")

    # 7. 关联建议 (L2 消费)
    lines.append("## 7. 关联建议 (供 L2 消费)")
    lines.append("")
    if primary and primary.get("correlation_hints"):
        hints = primary["correlation_hints"]
        lines.append("```yaml")
        lines.append("threat:")
        lines.append("  threat_type: " + (primary.get("threat_type") or "null"))
        lines.append("  confidence: " + str(primary.get("confidence") or 0))
        lines.append("  kill_chain_phase: " + (primary.get("kill_chain_phase") or "null"))
        lines.append("  mitre_attack:")
        lines.append(f"    - \"{primary.get('ttp')}\"")
        lines.append("  iocs:")
        if nat.get("real_attacker_ip"):
            lines.append(f"    ips: [\"{nat['real_attacker_ip']}\"]")
        if nat.get("real_victim_ip"):
            lines.append(f"    ips: [\"{nat['real_victim_ip']}\"]")
        lines.append("  correlation_hints:")
        lines.append(f"    pivot_keys: {hints.get('pivot_keys', [])}")
        lines.append(f"    time_window_min: {hints.get('time_window_min', 60)}")
        lines.append(f"    rationale: \"{hints.get('rationale', '')}\"")
        lines.append("```")
    else:
        lines.append("- 无 correlation_hints")
    lines.append("")

    # 8. 附录
    lines.append("## 8. 附录: 原始数据")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({
        "l0_parsed": parsed,
        "l0_ocsf": ocsf,
    }, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="L1 御界分析")
    ap.add_argument("l0_jsonl", type=Path)
    ap.add_argument("--out", type=Path, default=Path("cases"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--min-confidence", type=float, default=0.5)
    ap.add_argument("--only-threats", action="store_true")
    args = ap.parse_args()

    if not args.l0_jsonl.exists():
        print(f"[ERR] L0 JSONL 不存在: {args.l0_jsonl}", file=sys.stderr)
        sys.exit(1)

    args.out.mkdir(parents=True, exist_ok=True)

    n_total = 0
    n_threat = 0
    n_skipped = 0
    n_threat_types = {}

    with open(args.l0_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            n_total += 1
            if args.limit and n_total > args.limit:
                break

            if record.get("product") != "yujie":
                n_skipped += 1
                continue

            analysis = analyze_event(record)
            if not analysis:
                continue

            primary = analysis.get("primary", {})
            if primary:
                confidence = primary.get("confidence", 0)
                if confidence < args.min_confidence:
                    n_skipped += 1
                    continue

            event_id = make_event_id(record)
            md = render_case_md(event_id, record, analysis)
            (args.out / f"{event_id}.md").write_text(md, encoding="utf-8")

            if primary:
                n_threat += 1
                t_type = primary.get("threat_type", "未知")
                n_threat_types[t_type] = n_threat_types.get(t_type, 0) + 1
            elif not args.only_threats:
                pass  # 上面已经写过 case 了
            else:
                continue  # only-threats 模式跳过

    print(f"[STATS] total={n_total} threat={n_threat} skipped={n_skipped}", file=sys.stderr)
    if n_threat_types:
        print(f"[STATS] 威胁类型分布:", file=sys.stderr)
        for t, c in sorted(n_threat_types.items(), key=lambda x: -x[1]):
            print(f"  {c:4d}  {t}", file=sys.stderr)


if __name__ == "__main__":
    main()
