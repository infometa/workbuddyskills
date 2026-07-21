#!/usr/bin/env python3
"""
Linux 入侵检测日志预分析工具

从 Bash 采集脚本生成的纯文本日志中提取结构化摘要。
核心功能：SSH 暴力破解交叉验证 + 各章节精简输出。

用法（通过统一入口）:
  python3 scripts/analysis/preanalyze.py <log_file.txt>

用法（直接调用）:
  cd scripts/analysis/linux && python3 preanalyze_linux.py <log_file.txt>

数据流:
  log_xxx.txt → 章节解析(复用 _common) → SSH 交叉验证 → 章节精简 → Markdown stdout

  ┌──────────────────────────────────────────────┐
  │  复用 _common:                                │
  │   - parse_log_structure() 章节解析            │
  │   - classify_ip() IP 分类                     │
  │                                               │
  │  Linux 专有 (_pa_linux/):                     │
  │   - constants.py   正则/白名单常量            │
  │   - condenser.py   章节精简框架               │
  │   - ssh_analysis.py SSH 暴力破解交叉验证      │
  │   - handlers.py    各章节精简处理器            │
  └──────────────────────────────────────────────┘
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# 支持直接调用：确保 _common 和 _pa_linux 均可导入
_THIS_DIR = Path(__file__).resolve().parent          # .../scripts/analysis/linux
_ANALYSIS_DIR = _THIS_DIR.parent                     # .../scripts/analysis
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))               # 使 _pa_linux 可导入
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))            # 使 _common 可导入

from _common.models import SectionIndex
from _common.parsers import classify_ip, parse_log_structure

from _pa_linux import __version__
from _pa_linux.condenser import condense_section, get_sub_lines
from _pa_linux.threat_score import compute_threat_score
from _pa_linux.constants import RE_PASSWD_LINE
from _pa_linux.handlers import (
    extract_iocs_from_lines,
    extract_persistence_vectors,
    handler_authorized_keys,
    handler_crontab,
    handler_crontab_files,
    handler_dns,
    handler_env_variables,
    handler_established_tcp,
    handler_init_d,
    handler_ip_forward,
    handler_iptables,
    handler_kernel_modules,
    handler_listening_ports,
    handler_package_verify,
    handler_pam_check,
    handler_ppid1_processes,
    handler_reverse_shell_check,
    handler_security_hygiene,
    handler_shell_history,
    handler_shell_profiles,
    handler_skip,
    handler_sshd_config_check,
    handler_ssh_already_analyzed,
    handler_sudoers,
    handler_suid_sgid,
    handler_sudo_commands,
    handler_systemd_units,
    handler_timezone_ntp,
    handler_user_management,
    handler_users,
)
from _pa_linux.ssh_analysis import (
    analyze_ssh_brute_force,
    analyze_ssh_protocol_anomalies,
    parse_ssh_failures,
    parse_ssh_protocol_anomalies,
    parse_ssh_successes,
    parse_syslog_time,
)

# ---------------------------------------------------------------------------
# 任务委派接口
# ---------------------------------------------------------------------------

_RE_LINUX_META = re.compile(r"^\s*OSType\s*:\s*Linux", re.MULTILINE)

_LINUX_SECTION_MARKERS = [
    "======== SECTION: AuthLogs ========",
    "======== SECTION: Persistence ========",
    "======== SECTION: SSH ========",
    "======== SECTION: ShellHistory ========",
]


def can_handle(log_path: str) -> bool:
    """判断日志文件是否为 Linux 平台采集的日志。"""
    try:
        p = Path(log_path)
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        if _RE_LINUX_META.search(text[:5000]):
            return True
        for marker in _LINUX_SECTION_MARKERS:
            if marker in text:
                return True
        return False
    except Exception as e:
        print(f"[WARN] Linux can_handle 检测异常: {e}", file=sys.stderr)
        return False


def run(log_path: str) -> str:
    """执行 Linux 预分析，返回 Markdown 文本。"""
    analyzer = LinuxPreAnalyzer(log_path)
    return analyzer.run()


# ---------------------------------------------------------------------------
# Main Analyzer
# ---------------------------------------------------------------------------


class LinuxPreAnalyzer:
    """Linux 预分析器主类。"""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.lines: list[str] = []
        self.sections: list[SectionIndex] = []
        self.meta: dict = {}

    def run(self) -> str:
        """执行预分析，返回 Markdown 文本。"""
        start_time = time.time()

        text = self.log_path.read_text(encoding="utf-8-sig", errors="replace")
        self.lines = text.splitlines()
        self.sections = parse_log_structure(self.lines)

        # 元数据：Linux 采集脚本的 META 行格式不带 ======== 包裹，
        # 直接从前 30 行提取 KV 对
        self.meta = {}
        for line in self.lines[:30]:
            m = re.match(r"^(\w[\w.]*)\s*:\s*(.+)$", line)
            if m and m.group(1) not in ("REPORT_BEGIN", "META"):
                self.meta[m.group(1)] = m.group(2).strip()

        # SSH 交叉验证
        ssh_failures = parse_ssh_failures(self.lines, self.sections)
        ssh_successes = parse_ssh_successes(self.lines, self.sections)
        brute_force = analyze_ssh_brute_force(ssh_failures, ssh_successes)

        # SA-R003: SSH 协议异常检测（kex_exchange_identification / Bad protocol version）
        ssh_anomalies = parse_ssh_protocol_anomalies(self.lines, self.sections)
        ssh_anomaly_stats = analyze_ssh_protocol_anomalies(ssh_anomalies)

        # SA-R002: 计算原始日志行数用于命中率
        raw_fail_lines = get_sub_lines(self.lines, self.sections, "ssh_login_failed")
        raw_success_lines = get_sub_lines(self.lines, self.sections, "ssh_login_success")
        # 只统计非空非分隔符的 syslog 行
        raw_fail_count = sum(
            1 for l in raw_fail_lines
            if l.strip() and not l.strip().startswith("--------")
            and not l.strip().startswith("========")
        )
        raw_success_count = sum(
            1 for l in raw_success_lines
            if l.strip() and not l.strip().startswith("--------")
            and not l.strip().startswith("========")
        )

        # SA-R004: ATTACK_SIM_MARKER 统计
        attack_sim_count = sum(
            1 for l in self.lines if "ATTACK_SIM_MARKER" in l
        )

        elapsed = time.time() - start_time

        # Phase 3.5: 威胁评分自动计算（需在摘要之前完成）
        persistence_vectors = extract_persistence_vectors(
            self.lines, self.sections, get_sub_lines
        )
        threat_score = compute_threat_score(
            brute_force, ssh_successes, persistence_vectors,
        )

        # 渲染
        out = []
        out.append("# 预分析报告")
        out.append("")
        # 统一头部元数据格式（与 Windows 对齐）
        out.append(
            "platform: Linux | "
            "template: templates/analysis_report_template.md | "
            f"preanalyze_version: {__version__} | "
            f"host: {self.meta.get('Hostname', '?')}"
        )
        out.append(
            f"log: {self.log_path.name} | "
            f"采集: {self.meta.get('CollectionTimestamp', '?')} | "
            f"分析: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"原始: {len(self.lines)} 行 | "
            f"耗时: {round(elapsed, 1)}s"
        )

        # 摘要
        out.append("")
        out.append("## 摘要")
        out.append(
            f"- 读取 {len(self.lines)} 行日志, "
            f"解析 {len([s for s in self.sections if s.section_type == 'SECTION'])} 个章节"
        )
        out.append(
            f"- SSH 暴力破解: "
            f"{brute_force['total_attack_ips']}攻击IP / "
            f"{brute_force['total_attempts']}次尝试 / "
            f"{sum(1 for a in brute_force['attack_ips'] if a['found_in_success'])}渗透成功"
        )
        out.append(
            f"- SSH 成功登录: {len(ssh_successes)}条"
        )
        # SA-R003: SSH 协议异常摘要
        if ssh_anomaly_stats["total_events"] > 0:
            out.append(
                f"- ⚠️ SSH 协议异常: "
                f"{ssh_anomaly_stats['total_events']}次事件 / "
                f"{ssh_anomaly_stats['total_ips']}个来源IP"
                "（可能存在 HTTP 路径遍历探测）"
            )
        # SA-R002: 命中率指标，帮助 AI 判断是否有数据遗漏
        out.append(
            f"- 解析命中率: "
            f"失败登录 {len(ssh_failures)}/{raw_fail_count} 行命中, "
            f"成功登录 {len(ssh_successes)}/{raw_success_count} 行命中"
        )
        # SA-R004: ATTACK_SIM_MARKER 统计
        if attack_sim_count > 0:
            out.append(
                f"- ⚠️ 发现 {attack_sim_count} 行含 ATTACK_SIM_MARKER 标记"
                "（可能来自攻击模拟/红队演练）"
            )
        # UID=0 后门账户快速预扫描（从 SystemInfo.users 提取）
        users_lines = get_sub_lines(self.lines, self.sections, "users")
        uid0_backdoor_names = []
        for ul in users_lines:
            pm = RE_PASSWD_LINE.match(ul.strip())
            if pm and int(pm.group(3)) == 0 and pm.group(1) != "root":
                uid0_backdoor_names.append(pm.group(1))
        if uid0_backdoor_names:
            out.append(
                f"- ⚠️ UID=0 后门账户: {', '.join(uid0_backdoor_names)}"
            )
        out.append(
            f"- 威胁评分: {threat_score['final_score']}/100 "
            f"({threat_score['risk_label']})"
        )

        # SSH 暴力破解交叉验证
        out.append("")
        out.append("## SSH 暴力破解交叉验证")
        out.append(
            f"攻击IP: {brute_force['total_attack_ips']} | "
            f"总尝试: {brute_force['total_attempts']}"
        )
        ips = brute_force["attack_ips"]
        if ips:
            # 检测 found_in_success/success_count 是否全为默认值
            all_default = all(
                not a["found_in_success"] and a["success_count"] == 0
                for a in ips
            )
            # P1: 暴力破解 IP 表最多输出 top 20（按 attempts 已排序）
            # 优先保留渗透成功的 IP，确保不被截断
            _MAX_BRUTE_IPS = 20
            penetrated = [a for a in ips if a.get("found_in_success")]
            non_penetrated = [a for a in ips if not a.get("found_in_success")]
            # 渗透成功的全量保留，剩余槽位由非渗透 IP 填充
            remaining_slots = max(0, _MAX_BRUTE_IPS - len(penetrated))
            display_ips = penetrated + non_penetrated[:remaining_slots]
            omitted_count = len(ips) - len(display_ips)

            out.append("")
            if all_default:
                # 省略 found_in_success/success_count 两列
                out.append(
                    "| ip | type | attempts | first_attempt | last_attempt |"
                )
                out.append(
                    "| --- | --- | --- | --- | --- |"
                )
                for a in display_ips:
                    out.append(
                        f"| {a['ip']} | {a['ip_type']} | {a['attempts']} "
                        f"| {a['first_attempt']} | {a['last_attempt']} |"
                    )
            else:
                out.append(
                    "| ip | type | attempts | first_attempt | last_attempt "
                    "| found_in_success | success_count |"
                )
                out.append(
                    "| --- | --- | --- | --- | --- | --- | --- |"
                )
                for a in display_ips:
                    out.append(
                        f"| {a['ip']} | {a['ip_type']} | {a['attempts']} "
                        f"| {a['first_attempt']} | {a['last_attempt']} "
                        f"| {a['found_in_success']} "
                        f"| {a['success_count']} |"
                    )
            if omitted_count > 0:
                omitted_attempts = sum(a["attempts"] for a in ips[len(display_ips):])
                out.append(
                    f"(以下省略 {omitted_count} 个低频攻击 IP，"
                    f"合计 {omitted_attempts:,} 次尝试，均未渗透成功)"
                )

        # SSH 成功登录（按 user+method+ip 归类计数）
        out.append("")
        out.append("## SSH 成功登录")
        if ssh_successes:
            # 按 (user, method, ip) 归类
            login_counter: dict[tuple[str, str, str], dict] = {}
            for s in ssh_successes:
                key = (s["user"], s["method"], s["ip"])
                if key not in login_counter:
                    login_counter[key] = {
                        "count": 0,
                        "first": s["time"],
                        "last": s["time"],
                        "ip_type": classify_ip(s["ip"]),
                    }
                login_counter[key]["count"] += 1
                login_counter[key]["last"] = s["time"]
            out.append(
                f"共 {len(ssh_successes)} 次成功登录，"
                f"归类为 {len(login_counter)} 组"
            )
            out.append("")
            out.append(
                "| user | method | ip | ip_type | count "
                "| first | last |"
            )
            out.append(
                "| --- | --- | --- | --- | --- | --- | --- |"
            )
            for (user, method, ip), info in sorted(
                login_counter.items(), key=lambda x: -x[1]["count"]
            ):
                out.append(
                    f"| {user} | {method} | {ip} | {info['ip_type']} "
                    f"| {info['count']} | {info['first']} | {info['last']} |"
                )
        else:
            out.append("(无数据)")

        # SA-R003: SSH 协议异常（HTTP 路径遍历探测等非 SSH 协议流量）
        out.extend(self._render_ssh_protocol_anomalies(ssh_anomaly_stats))

        # 各章节精简输出

        section_config = {
            "SystemInfo": {
                "whoami": handler_skip,
                "os_release": handler_skip,
                "hardware": handler_skip,
                "security_hygiene": handler_security_hygiene,
                "users": handler_users,
                "sudoers": handler_sudoers,
                "env_integrity": handler_skip,
            },
            "AuthLogs": {
                "sudo_commands": handler_sudo_commands,
                "user_created": handler_user_management,
                "user_modified": handler_user_management,
                "ssh_login_failed": handler_ssh_already_analyzed,
                "ssh_login_success": handler_ssh_already_analyzed,
                "ssh_accepted_keys": handler_ssh_already_analyzed,
            },
            "Processes": {
                "reverse_shell_check": handler_reverse_shell_check,
                "cpu_top15": handler_skip,
                "mem_top15": handler_skip,
                "ppid1_processes": handler_ppid1_processes,
            },
            "Network": {
                "listening_ports": handler_listening_ports,
                "established_tcp": handler_established_tcp,
                "route": handler_skip,
                "arp": handler_skip,
                "iptables": handler_iptables,
                "dns": handler_dns,
                "ip_forward": handler_ip_forward,
            },
            "Persistence": {
                "crontab": handler_crontab,
                "crontab_files": handler_crontab_files,
                "shell_profiles": handler_shell_profiles,
                "init_d": handler_init_d,
                "systemd_units": handler_systemd_units,
            },
            "SSH": {
                "sshd_stat": handler_skip,
                "sshd_config_check": handler_sshd_config_check,
                "authorized_keys": handler_authorized_keys,
                "pam_check": handler_pam_check,
            },
            "ShellHistory": {
                "bash_history_sensitive": handler_shell_history,
                "zsh_history_sensitive": handler_shell_history,
            },
            "Environment": {
                "env_variables": handler_env_variables,
                "kernel_modules": handler_kernel_modules,
                "timezone_ntp": handler_timezone_ntp,
            },
            "FileIntegrity": {
                "package_verify": handler_package_verify,
                "suid_sgid": handler_suid_sgid,
            },
        }

        for sec_name, handlers in section_config.items():
            condensed = condense_section(
                self.lines, self.sections, sec_name, handlers
            )
            # 整节为空（全部 handler 返回 None）时不输出 SECTION 标题
            if not any(line.strip() for line in condensed):
                continue
            out.append("")
            out.append(f"## {sec_name}")
            out.extend(condensed)

        # IOC 汇总：从全文提取外部 IP + 可疑域名
        out.extend(self._render_ioc_summary(ssh_failures, ssh_successes))

        # 持久化向量汇总：跨章节聚合所有持久化机制
        out.extend(self._render_persistence_summary())

        # 威胁评分渲染（threat_score 已在摘要前计算）
        out.extend(self._render_threat_score(threat_score))

        # Phase 4.5: 数据质量校验（对齐 Windows）
        dq_warnings = self._check_data_quality(
            brute_force, ssh_successes, ssh_failures,
            raw_fail_count, raw_success_count,
        )
        if dq_warnings:
            out.append("")
            out.append("## 数据质量告警")
            out.append("")
            out.append("| severity | source | detail |")
            out.append("| --- | --- | --- |")
            for w in dq_warnings:
                out.append(
                    f"| {w['severity']} | {w['source']} | {w['detail']} |"
                )

        out.append("")
        out.append("# 预分析结束")
        return "\n".join(out) + "\n"

    def _render_ssh_protocol_anomalies(
        self, anomaly_stats: dict,
    ) -> list[str]:
        """SA-R003: 渲染 SSH 协议异常章节。

        当攻击者通过 SSH 端口发送 HTTP 请求（路径遍历探测）或其他非 SSH 协议流量时，
        sshd 会记录 kex_exchange_identification / Bad protocol version 错误。
        这些信号对模型识别 HTTP 路径遍历攻击至关重要。
        """
        out: list[str] = []

        if anomaly_stats["total_events"] == 0:
            return out

        out.append("")
        out.append("## SSH 协议异常")
        out.append("")
        out.append(
            f"事件总数: {anomaly_stats['total_events']} | "
            f"来源IP: {anomaly_stats['total_ips']} 个"
        )
        if anomaly_stats["unknown_ip_events"] > 0:
            out.append(
                f"⚠️ 其中 {anomaly_stats['unknown_ip_events']} 条事件"
                "未能提取源 IP（建议回查原始日志）"
            )

        ip_stats = anomaly_stats["ip_stats"]
        if ip_stats:
            # 检查是否所有 IP 都是"未知"
            all_unknown = all(s["ip"] == "(未知)" for s in ip_stats)
            if all_unknown and len(ip_stats) == 1:
                s = ip_stats[0]
                types_str = ", ".join(s["types"])
                sample = s["sample_details"][0] if s["sample_details"] else "-"
                if len(sample) > 80:
                    sample = sample[:77] + "..."
                out.append(
                    f"全部 {s['count']} 次事件均未提取到源 IP，"
                    f"异常类型: {types_str}，示例: {sample}"
                )
            else:
                out.append("")
                out.append(
                    "| IP | 分类 | 次数 | 异常类型 | 首次 | 最后 | 示例详情 |"
                )
                out.append(
                    "| --- | --- | --- | --- | --- | --- | --- |"
                )
                for s in ip_stats:
                    types_str = ", ".join(s["types"])
                    sample = s["sample_details"][0] if s["sample_details"] else "-"
                    if len(sample) > 80:
                        sample = sample[:77] + "..."
                    out.append(
                        f"| {s['ip']} | {s['ip_type']} | {s['count']} "
                        f"| {types_str} | {s['first_seen']} | {s['last_seen']} "
                        f"| {sample} |"
                    )

        return out

    def _render_ioc_summary(
        self,
        ssh_failures: list[dict],
        ssh_successes: list[dict],
    ) -> list[str]:
        """渲染 IOC 汇总章节。

        数据来源:
        1. SSH 失败/成功登录中的外部 IP（已结构化）
        2. 全文正则扫描的外部 IP 和可疑域名
        去重后集中输出，供 AI 批量威胁情报查询。
        """
        out: list[str] = []

        # 从 SSH 分析结果提取 IP（精确、无噪声）
        ssh_ips: set[str] = set()
        for f in ssh_failures:
            ssh_ips.add(f["ip"])
        for s in ssh_successes:
            ssh_ips.add(s["ip"])

        # 从全文正则扫描提取 IP + 域名
        raw_iocs = extract_iocs_from_lines(self.lines)

        # 合并所有 IP，按 classify_ip 分类过滤
        all_ips = ssh_ips | raw_iocs["ips"]
        external_ips: list[str] = sorted(
            ip for ip in all_ips if classify_ip(ip) == "external"
        )
        domains: list[str] = sorted(raw_iocs["domains"])

        if not external_ips and not domains:
            return out

        out.append("")
        out.append("## IOC 汇总")
        out.append(
            f"外部 IP: {len(external_ips)} 个 | "
            f"可疑域名: {len(domains)} 个"
        )

        if external_ips:
            out.append("### 外部 IP")
            out.append("")
            # P2: IOC 外部 IP 最多展示 top 30（按字母排序），超出的合并为摘要行
            # 优先保留在 SSH 成功登录中出现的 IP（高价值）
            _MAX_IOC_IPS = 30
            success_ips = {s["ip"] for s in ssh_successes if classify_ip(s.get("ip", "")) == "external"}
            priority_ips = sorted(ip for ip in external_ips if ip in success_ips)
            remaining_ips = sorted(ip for ip in external_ips if ip not in success_ips)
            remaining_slots = max(0, _MAX_IOC_IPS - len(priority_ips))
            display_external = priority_ips + remaining_ips[:remaining_slots]
            omitted_ioc_count = len(external_ips) - len(display_external)

            out.append("| IP | 分类 |")
            out.append("| --- | --- |")
            for ip in display_external:
                out.append(f"| {ip} | {classify_ip(ip)} |")
            if omitted_ioc_count > 0:
                out.append(
                    f"(以下省略 {omitted_ioc_count} 个低优先级外部 IP，"
                    f"可通过预分析解压目录精准回查)"
                )

        if domains:
            out.append("### 可疑域名")
            for d in domains:
                out.append(f"- {d}")

        return out

    def _render_persistence_summary(self) -> list[str]:
        """渲染持久化向量汇总章节。

        压缩为一行类型×计数摘要（详情已在 Persistence 章节输出）。
        """
        out: list[str] = []

        vectors = extract_persistence_vectors(
            self.lines, self.sections, get_sub_lines
        )

        if not vectors:
            return out

        # 按类型计数
        type_counts: dict[str, int] = {}
        for v in vectors:
            t = v.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        parts = [f"{t}×{c}" for t, c in sorted(type_counts.items())]
        out.append("")
        out.append(
            f"## 持久化向量汇总: {len(vectors)} 个 — "
            + ", ".join(parts)
        )
        return out

    def _render_threat_score(self, threat_score: dict) -> list[str]:
        """渲染威胁评分（仅输出最终分 + 风险等级）。"""
        out: list[str] = []
        out.append("")
        out.append(
            f"## 威胁评分: {threat_score['final_score']}/100 "
            f"{threat_score['risk_label']}"
        )
        return out

    def _check_data_quality(
        self,
        brute_force: dict,
        ssh_successes: list[dict],
        ssh_failures: list[dict],
        raw_fail_count: int,
        raw_success_count: int,
    ) -> list[dict]:
        """Phase 4.5: 数据质量校验。

        检查项:
        1. SSH 解析命中率异常（大量行未被正则匹配）
        2. syslog 时间解析失败（跨年/格式异常）
        3. 章节完整性（预期章节缺失）
        4. 空数据段告警
        """
        warnings: list[dict] = []

        # --- 1. SSH 解析命中率校验 ---
        if raw_fail_count > 0:
            hit_rate = len(ssh_failures) / raw_fail_count
            if hit_rate < 0.5:
                warnings.append({
                    "severity": "low_hit_rate",
                    "source": "ssh_login_failed",
                    "detail": (
                        f"SSH 失败登录解析命中率仅 {hit_rate:.0%} "
                        f"({len(ssh_failures)}/{raw_fail_count})，"
                        "可能存在未识别的 syslog 格式变体，建议回查原始日志确认"
                    ),
                })

        if raw_success_count > 0:
            hit_rate = len(ssh_successes) / raw_success_count
            if hit_rate < 0.5:
                warnings.append({
                    "severity": "low_hit_rate",
                    "source": "ssh_login_success",
                    "detail": (
                        f"SSH 成功登录解析命中率仅 {hit_rate:.0%} "
                        f"({len(ssh_successes)}/{raw_success_count})，"
                        "可能存在未识别的 syslog 格式变体，建议回查原始日志确认"
                    ),
                })

        # --- 2. syslog 时间解析校验 ---
        time_parse_failures = 0
        for f in ssh_failures:
            if parse_syslog_time(f["time"]) is None:
                time_parse_failures += 1
        for s in ssh_successes:
            if parse_syslog_time(s["time"]) is None:
                time_parse_failures += 1
        if time_parse_failures > 0:
            warnings.append({
                "severity": "time_parse_error",
                "source": "syslog_time",
                "detail": (
                    f"{time_parse_failures} 条 syslog 时间解析失败，"
                    "可能导致时间排序和跨年判断不准确"
                ),
            })

        # --- 3. 章节完整性校验 ---
        expected_sections = [
            "SystemInfo", "AuthLogs", "Processes", "Network",
            "Persistence", "SSH", "ShellHistory", "Environment",
            "FileIntegrity",
        ]
        found_sections = {s.name for s in self.sections}
        for sec_name in expected_sections:
            if sec_name not in found_sections:
                warnings.append({
                    "severity": "missing_section",
                    "source": sec_name,
                    "detail": (
                        f"预期章节 {sec_name} 缺失，"
                        "该维度的分析数据将不可用"
                    ),
                })

        # --- 4. 空数据段告警 ---
        for sec in self.sections:
            if sec.section_type == "SECTION" and not sec.subsections:
                # 章节存在但无子段，可能数据采集失败
                content_lines = self.lines[sec.start_line:sec.end_line]
                non_empty = [
                    l for l in content_lines
                    if l.strip()
                    and not l.strip().startswith("========")
                    and not l.strip().startswith("--------")
                ]
                if not non_empty:
                    warnings.append({
                        "severity": "empty_section",
                        "source": sec.name,
                        "detail": (
                            f"章节 {sec.name} 存在但内容为空，"
                            "可能采集失败或目标系统无相关数据"
                        ),
                    })

        return warnings


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Linux 入侵检测日志预分析工具（Markdown 输出到 stdout）",
        epilog=(
            "示例:\n"
            "  python3 preanalyze_linux.py log_host_20260401.txt\n"
            "\n"
            "推荐通过统一入口调用:\n"
            "  python3 scripts/analysis/preanalyze.py log_host_20260401.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("log_file", help="Bash 采集的日志文件路径 (.txt)")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"[ERROR] 日志文件不存在: {log_path}", file=sys.stderr)
        sys.exit(1)

    if not can_handle(str(log_path)):
        print("[ERROR] 该日志文件不是 Linux 平台采集的日志", file=sys.stderr)
        sys.exit(1)

    print(run(str(log_path)))


if __name__ == "__main__":
    main()
