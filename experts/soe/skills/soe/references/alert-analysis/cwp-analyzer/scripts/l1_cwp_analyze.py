#!/usr/bin/env python3
"""L1 主机安全分析 CLI

输入: L0 输出的 JSONL (soc-alert-pipeline/l0_parse.py 生成)
输出: cases/{event_id}.md 案例文档 (人读 + L2 可消费)

用法:
  python3 l1_cwp_analyze.py <l0_jsonl_path> --out cases/
  python3 l1_cwp_analyze.py <l0_jsonl_path> --limit 10 --pretty
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
    detect_brute_force,
    detect_reverse_shell,
    detect_persistence,
    detect_lateral_movement,
)


def analyze_event(record: dict) -> dict | None:
    """分析单条 L0 输出, 返回威胁判定

    Args:
        record: L0 输出的 dict (含 parsed / ocsf / row / product)

    Returns:
        威胁判定 dict (含 threat_type / ttp / confidence / reasons / signals / correlation_hints)
        或 None (无威胁)
    """
    parsed = record.get("parsed", {})
    if not parsed:
        return None

    raw_kv = parsed.get("_raw_kv", {}) or {}

    # 依次跑 4 个 detector, 第一个命中且 confidence >= 0.5 的就返回
    detectors = [
        ("brute_force", detect_brute_force),
        ("reverse_shell", detect_reverse_shell),
        ("persistence", detect_persistence),
        ("lateral_movement", detect_lateral_movement),
    ]

    results = []
    for name, detector in detectors:
        try:
            r = detector(parsed, raw_kv)
            if r:
                r["detector"] = name
                results.append(r)
        except Exception as e:
            # 单个 detector 失败不影响其他
            results.append({
                "detector": name,
                "error": f"{type(e).__name__}: {e}",
            })

    # 取 confidence 最高的 (如果都 < 0.5, 返回 None)
    valid = [r for r in results if r.get("confidence", 0) >= 0.5]
    if not valid:
        return None

    best = max(valid, key=lambda r: r.get("confidence", 0))
    return {
        "primary": best,
        "all_detections": results,  # 保留所有, 供调试
    }


def make_event_id(record: dict) -> str:
    """生成案例文档 ID"""
    row = record.get("row", 0)
    product = record.get("product", "cwp")
    return f"{product}_r{row:05d}_{uuid.uuid4().hex[:8]}"


def render_case_md(event_id: str, record: dict, analysis: dict) -> str:
    """渲染单条案例文档 (Markdown)

    结构:
      1. 基础信息
      2. 威胁判定
      3. 处置建议
      4. 关联建议 (L2 消费)
    """
    parsed = record.get("parsed", {})
    ocsf = record.get("ocsf", {})
    primary = analysis.get("primary", {})
    raw_kv = parsed.get("_raw_kv", {})

    lines = []
    lines.append(f"# 主机安全事件分析 - {event_id}")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 来源: {record.get('source_file', '?')} row={record.get('row', '?')}")
    lines.append("")

    # 1. 基础信息
    lines.append("## 1. 基础信息")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 事件时间 | {parsed.get('event_time', '?')} |")
    lines.append(f"| 告警名称 | {parsed.get('rule_name', '?')} |")
    lines.append(f"| 主机 | {parsed.get('host_ip') or '?'} |")
    lines.append(f"| 用户 | {parsed.get('user', '-')} |")
    lines.append(f"| 进程 | {parsed.get('process', '-')} |")
    lines.append(f"| 命令 | {(parsed.get('cmd') or '-')[:200]} |")
    lines.append(f"| 源 IP | {parsed.get('src_ip', '-')} |")
    lines.append(f"| 目的 IP:端口 | {parsed.get('dst_ip', '-')}:{parsed.get('dst_port', '-')} |")
    lines.append(f"| 严重度 (OCSF) | {ocsf.get('severity', '-')} |")
    lines.append(f"| 置信度 (OCSF) | {ocsf.get('confidence', '-')} |")
    lines.append("")

    # 2. 威胁判定
    lines.append("## 2. 威胁判定")
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
        signals = primary.get("signals", {})
        if signals:
            lines.append("**关键信号**:")
            lines.append("```json")
            lines.append(json.dumps(signals, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
    else:
        lines.append("- 未命中已知威胁场景 (但已执行全部 detector)")
        lines.append("")

    # 所有检测器结果 (调试)
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

    # 3. 处置建议
    lines.append("## 3. 处置建议")
    lines.append("")
    if primary:
        threat_type = primary.get("threat_type", "")
        if "暴力破解" in threat_type:
            lines.extend([
                "- [ ] **阻断源 IP**: 安全组 / WAF / CWP 阻断 `src_ip`",
                "- [ ] **检查登录日志**: 拉取 `lastb` / `/var/log/secure` / 腾讯云镜历史",
                "- [ ] **强制改密**: 涉及账号",
                "- [ ] **启用防护**: 腾讯云镜自带暴力破解防护 / fail2ban",
                "- [ ] **历史聚合**: 拉取此 src_ip 历史 CWP 告警",
            ])
        elif "反弹 Shell" in threat_type:
            lines.extend([
                "- [ ] **立即隔离主机**: CWP 隔离网络 / 安全组断网",
                "- [ ] **杀进程**: `ps aux | grep -E 'bash|nc|python'` → kill",
                "- [ ] **拉历史**: `cat ~/.bash_history`",
                "- [ ] **查外联**: `ss -tnp` / CWP 网络连接记录",
                "- [ ] **查持久化**: crontab / systemd / authorized_keys",
                "- [ ] **L2 关联**: 拉取此 dst_ip 在御界的告警 (C2 / 数据外传)",
            ])
        elif "持久化" in threat_type:
            lines.extend([
                "- [ ] **拉 cron**: `crontab -l` + `/etc/cron.*` + `/var/spool/cron/`",
                "- [ ] **拉 systemd**: `/etc/systemd/system/` + `~/.config/systemd/`",
                "- [ ] **查 SSH 后门**: `~/.ssh/authorized_keys` 异常公钥",
                "- [ ] **查启动项**: `~/.bashrc` `~/.bash_profile` `~/.zshrc`",
                "- [ ] **查 SUID**: `find / -perm -4000` 异常文件",
                "- [ ] **查 ld_preload**: `/etc/ld.so.preload` (正常应该不存在)",
            ])
        elif "横向移动" in threat_type:
            lines.extend([
                "- [ ] **拉历史**: 此 user 在内网其他主机的 CWP 告警 (L2 聚合)",
                "- [ ] **查凭据**: /etc/shadow 是否被读取 / Mimikatz 痕迹",
                "- [ ] **查扫描**: 短时间内多 dst_port 的告警",
                "- [ ] **隔离受感染主机**: 先隔离再排查",
                "- [ ] **全网改密**: 涉及的用户 / 服务账号",
            ])
        else:
            lines.append("- 通用处置: 隔离 → 排查 → 恢复 → 加固")
    else:
        lines.append("- 无明显威胁场景, 建议保留待人工 review")
    lines.append("")

    # 4. 关联建议 (L2 消费)
    lines.append("## 4. 关联建议 (供 L2 消费)")
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
        iocs_lines = []
        if parsed.get("src_ip"):
            iocs_lines.append(f"    ips: [\"{parsed['src_ip']}\"]")
        if parsed.get("dst_ip"):
            iocs_lines.append(f"    ips: [\"{parsed['dst_ip']}\"]")
        if parsed.get("user"):
            iocs_lines.append(f"    users: [\"{parsed['user']}\"]")
        if not iocs_lines:
            iocs_lines.append("    ips: []")
        for line in iocs_lines:
            lines.append(line)
        lines.append("  correlation_hints:")
        lines.append(f"    pivot_keys: {hints.get('pivot_keys', [])}")
        lines.append(f"    time_window_min: {hints.get('time_window_min', 60)}")
        lines.append(f"    rationale: \"{hints.get('rationale', '')}\"")
        lines.append("```")
    else:
        lines.append("- 无 correlation_hints (无威胁判定)")
    lines.append("")

    # 5. 附录: 原始数据
    lines.append("## 5. 附录: 原始数据")
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
    ap = argparse.ArgumentParser(
        description="L1 主机安全分析 (消费 L0 JSONL → 案例文档)",
    )
    ap.add_argument("l0_jsonl", type=Path, help="L0 输出的 JSONL 文件")
    ap.add_argument("--out", type=Path, default=Path("cases"),
                    help="案例输出目录 (默认 ./cases)")
    ap.add_argument("--limit", type=int, default=None, help="限制处理行数")
    ap.add_argument("--min-confidence", type=float, default=0.5,
                    help="最低置信度阈值, 低于此值不写案例 (默认 0.5)")
    ap.add_argument("--only-threats", action="store_true",
                    help="只输出有威胁的 (跳过无威胁的, 案例文档更聚焦)")
    args = ap.parse_args()

    if not args.l0_jsonl.exists():
        print(f"[ERR] L0 JSONL 不存在: {args.l0_jsonl}", file=sys.stderr)
        sys.exit(1)

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] 输出目录: {args.out}", file=sys.stderr)

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
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 解析失败 (line {n_total + 1}): {e}", file=sys.stderr)
                continue

            n_total += 1
            if args.limit and n_total > args.limit:
                break

            # 跳过非 cwp 记录
            if record.get("product") != "cwp":
                n_skipped += 1
                continue

            analysis = analyze_event(record)
            if not analysis:
                if not args.only_threats:
                    # 无威胁, 也写一个空案例
                    event_id = make_event_id(record)
                    md = render_case_md(event_id, record, {"primary": None, "all_detections": []})
                    (args.out / f"{event_id}.md").write_text(md, encoding="utf-8")
                continue

            primary = analysis.get("primary", {})
            confidence = primary.get("confidence", 0)
            if confidence < args.min_confidence:
                n_skipped += 1
                continue

            event_id = make_event_id(record)
            md = render_case_md(event_id, record, analysis)
            (args.out / f"{event_id}.md").write_text(md, encoding="utf-8")
            n_threat += 1

            t_type = primary.get("threat_type", "未知")
            n_threat_types[t_type] = n_threat_types.get(t_type, 0) + 1

    print(f"[STATS] total={n_total} threat={n_threat} skipped={n_skipped}", file=sys.stderr)
    if n_threat_types:
        print(f"[STATS] 威胁类型分布:", file=sys.stderr)
        for t, c in sorted(n_threat_types.items(), key=lambda x: -x[1]):
            print(f"  {c:4d}  {t}", file=sys.stderr)


if __name__ == "__main__":
    main()
