#!/usr/bin/env python3
"""
Linux 原始 /var/log/ 目录预分析器

从原始 /var/log/ 目录（而非采集脚本 .txt 输出）直接读取 syslog 文件，
提取 SSH 认证事件、Cron 任务、NTP 信息，独立生成 Markdown 预分析报告。
不依赖 LinuxPreAnalyzer，无临时文件，无 SECTION 格式中间层。

数据流:
  var/log/ 目录
    → 读取 secure/messages/cron 等 syslog 文件（时间排序）
    → 直接提取 auth log 行 → SSH 分析 + 威胁评分
    → Markdown stdout

支持的文件:
  - secure, secure-YYYYMMDD   ← SSH 认证日志（最重要）
  - messages, messages-YYYYMMDD ← 系统综合日志（NTP）
  - cron, cron-YYYYMMDD         ← 定时任务日志

用法（通过统一入口）:
  python3 scripts/analysis/preanalyze.py /path/to/var/log/

用法（直接调用）:
  cd scripts/analysis/linux_log_folder
  python3 preanalyze_linux_log_folder.py /path/to/var/log/
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# 支持直接调用：确保 _common 和 linux 包可导入
_THIS_DIR = Path(__file__).resolve().parent          # .../scripts/analysis/linux_log_folder
_ANALYSIS_DIR = _THIS_DIR.parent                     # .../scripts/analysis
_LINUX_DIR = _ANALYSIS_DIR / "linux"

for p in [str(_THIS_DIR), str(_ANALYSIS_DIR), str(_LINUX_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from _common.parsers import classify_ip
from linux_log_folder import __version__

# 复用 linux/_pa_linux 中的独立分析函数（无 sections 依赖）
from _pa_linux.ssh_analysis import (
    _parse_ssh_failures_raw,
    _parse_ssh_successes_raw,
    _parse_ssh_protocol_anomalies_raw,
    analyze_ssh_brute_force,
    analyze_ssh_protocol_anomalies,
)
from _pa_linux.threat_score import compute_threat_score
from _pa_linux.handlers import extract_iocs_from_lines

# ---------------------------------------------------------------------------
# 日志辅助（仅 --debug 模式输出 INFO，否则静默）
# ---------------------------------------------------------------------------

def _info(msg: str) -> None:
    """输出 INFO 日志到 stderr，仅当 PREANALYZE_DEBUG=1 时生效。"""
    if os.environ.get("PREANALYZE_DEBUG") == "1":
        print(f"[INFO] linux_log_folder: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 任务委派接口
# ---------------------------------------------------------------------------

def can_handle(path: str) -> bool:
    """判断路径是否为包含 syslog 的 var/log 目录。"""
    try:
        p = Path(path)
        if not p.is_dir():
            return False
        # 存在 secure 或 messages 文件即认为是 var/log 目录
        for name in ("secure", "messages", "auth.log"):
            if (p / name).exists():
                return True
        # 也接受 secure-* 或 messages-* 轮转文件
        for child in p.iterdir():
            if child.name.startswith("secure") or child.name.startswith("messages"):
                return True
        return False
    except Exception as e:
        print(f"[WARN] linux_log_folder can_handle 检测异常: {e}", file=sys.stderr)
        return False


def run(path: str, hostname_hint: str = "") -> str:
    """执行原始 var/log 目录预分析，返回 Markdown 文本。

    Args:
        path: var/log 目录路径
        hostname_hint: 主机名提示（如从 tar 文件名推断），空则从日志提取
    """
    analyzer = LinuxLogFolderAnalyzer(path, hostname_hint=hostname_hint)
    return analyzer.run()


# ---------------------------------------------------------------------------
# 日志文件排序键
# ---------------------------------------------------------------------------

def _log_sort_key(path: Path) -> tuple:
    """日志文件排序：轮转文件按日期升序，当前文件排最后（最新）。

    secure-20260322 < secure-20260329 < secure（最新）
    """
    name = path.name
    # 提取日期后缀（YYYYMMDD）
    m = re.search(r"-(\d{8})$", name)
    if m:
        return (0, m.group(1))  # 有日期的轮转文件，按日期排序（旧→新）
    return (1, "")              # 无日期的当前文件，排最后


# ---------------------------------------------------------------------------
# 主分析器
# ---------------------------------------------------------------------------

class LinuxLogFolderAnalyzer:
    """从原始 var/log 目录直接提取 auth log 并生成 Markdown 预分析报告。

    不依赖 LinuxPreAnalyzer，独立完成 SSH 分析 + 威胁评分。
    数据源仅限 var/log 中的 syslog 文件（secure/messages/cron）。
    """

    # 要处理的 syslog 文件基础名（按此顺序查找）
    SYSLOG_BASES = ["secure", "auth.log", "messages", "cron"]

    def __init__(self, log_dir: str, hostname_hint: str = ""):
        self.log_dir = Path(log_dir).resolve()
        self.hostname_hint = hostname_hint
        self.hostname = hostname_hint or ""

    def run(self) -> str:
        """执行分析，返回 Markdown 文本。"""
        start_time = time.time()

        # Step 1: 收集日志文件
        syslog_files = self._collect_syslog_files()
        if not syslog_files:
            print(
                f"[ERROR] {self.log_dir} 下未找到可识别的 syslog 文件",
                file=sys.stderr,
            )
            return f"# 预分析报告\n\n[ERROR] 未找到可识别的 syslog 文件\n"

        # Step 2: 读取所有 syslog
        all_lines_by_type = self._read_syslog_files(syslog_files)

        # Step 3: 从日志中推断 hostname（如果未提供）
        if not self.hostname:
            self.hostname = self._infer_hostname(all_lines_by_type)

        # Step 4: SSH 分析（直接调用，不走 LinuxPreAnalyzer）
        auth_lines = all_lines_by_type.get("secure", []) + all_lines_by_type.get("auth.log", [])
        cron_lines = all_lines_by_type.get("cron", [])
        messages_lines = all_lines_by_type.get("messages", [])

        ssh_failures = _parse_ssh_failures_raw(auth_lines)
        ssh_successes = _parse_ssh_successes_raw(auth_lines)
        brute_force = analyze_ssh_brute_force(ssh_failures, ssh_successes)

        # SSH 协议异常
        ssh_anomalies = _parse_ssh_protocol_anomalies_raw(auth_lines)
        ssh_anomaly_stats = analyze_ssh_protocol_anomalies(ssh_anomalies)

        # 威胁评分（persistence_vectors 为空，因为 linux_log_folder 无 crontab 完整配置）
        threat_score = compute_threat_score(brute_force, ssh_successes, [])

        # IOC 汇总
        raw_iocs = extract_iocs_from_lines(auth_lines + cron_lines + messages_lines)
        elapsed = time.time() - start_time

        # Step 5: 生成 Markdown
        out = []
        out.append("# 预分析报告")
        out.append("")
        out.append(
            f"platform: Linux | data_source: raw_var_log_folder | "
            f"linux_log_folder_version: {__version__} | host: {self.hostname}"
        )
        out.append(
            f"log_dir: {self.log_dir} | "
            f"分析: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"原始: {sum(len(v) for v in all_lines_by_type.values())} 行 | "
            f"耗时: {round(elapsed, 1)}s"
        )
        out.append("")
        # 摘要
        out.extend(self._render_summary(
            brute_force, ssh_successes, ssh_anomaly_stats, threat_score,
            sum(len(v) for v in all_lines_by_type.values()),
        ))

        # SSH 暴力破解交叉验证
        out.extend(self._render_brute_force(brute_force))

        # SSH 成功登录
        out.extend(self._render_ssh_successes(ssh_successes))

        # SSH 协议异常
        out.extend(self._render_ssh_protocol_anomalies(ssh_anomaly_stats))

        # 持久化：Crontab
        out.extend(self._render_crontab(cron_lines))

        # 环境：NTP
        ntp_lines = [
            l for l in messages_lines
            if "chronyd" in l and ("time" in l.lower() or "ntp" in l.lower())
        ]
        if ntp_lines:
            out.append("")
            out.append("## Environment")
            out.append("")
            out.append("### timezone_ntp")
            for l in ntp_lines[:5]:
                out.append(l)
            out.append("")

        # IOC 汇总
        out.extend(self._render_ioc_summary(ssh_failures, ssh_successes, raw_iocs))

        # 威胁评分
        out.append("")
        out.append(
            f"## 威胁评分: {threat_score['final_score']}/100 "
            f"{threat_score['risk_label']}"
        )
        out.append("")
        out.append("# 预分析结束")

        return "\n".join(out) + "\n"

    def _render_summary(
        self, brute_force, ssh_successes, ssh_anomaly_stats, threat_score, total_lines,
    ) -> list[str]:
        """渲染摘要章节。"""
        out = []
        out.append("")
        out.append("## 摘要")
        out.append(
            f"- 读取 {total_lines} 行日志"
        )
        out.append(
            f"- SSH 暴力破解: "
            f"{brute_force['total_attack_ips']}攻击IP / "
            f"{brute_force['total_attempts']}次尝试 / "
            f"{sum(1 for a in brute_force['attack_ips'] if a['found_in_success'])}渗透成功"
        )
        out.append(f"- SSH 成功登录: {len(ssh_successes)}条")
        if ssh_anomaly_stats["total_events"] > 0:
            out.append(
                f"- ⚠️ SSH 协议异常: "
                f"{ssh_anomaly_stats['total_events']}次事件 / "
                f"{ssh_anomaly_stats['total_ips']}个来源IP"
                "（可能存在 HTTP 路径遍历探测）"
            )
        out.append(
            f"- 威胁评分: {threat_score['final_score']}/100 "
            f"({threat_score['risk_label']})"
        )
        return out

    def _render_brute_force(self, brute_force: dict) -> list[str]:
        """渲染 SSH 暴力破解交叉验证章节。"""
        out = []
        out.append("")
        out.append("## SSH 暴力破解交叉验证")
        out.append(
            f"攻击IP: {brute_force['total_attack_ips']} | "
            f"总尝试: {brute_force['total_attempts']}"
        )
        ips = brute_force["attack_ips"]
        if ips:
            all_default = all(
                not a["found_in_success"] and a["success_count"] == 0
                for a in ips
            )
            _MAX_BRUTE_IPS = 20
            penetrated = [a for a in ips if a.get("found_in_success")]
            non_penetrated = [a for a in ips if not a.get("found_in_success")]
            remaining_slots = max(0, _MAX_BRUTE_IPS - len(penetrated))
            display_ips = penetrated + non_penetrated[:remaining_slots]
            omitted_count = len(ips) - len(display_ips)

            out.append("")
            if all_default:
                out.append(
                    "| ip | type | attempts | first_attempt | last_attempt |"
                )
                out.append("| --- | --- | --- | --- | --- |")
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
                out.append("| --- | --- | --- | --- | --- | --- | --- |")
                for a in display_ips:
                    out.append(
                        f"| {a['ip']} | {a['ip_type']} | {a['attempts']} "
                        f"| {a['first_attempt']} | {a['last_attempt']} "
                        f"| {a['found_in_success']} | {a['success_count']} |"
                    )
            if omitted_count > 0:
                omitted_attempts = sum(a["attempts"] for a in ips[len(display_ips):])
                out.append(
                    f"(以下省略 {omitted_count} 个低频攻击 IP，"
                    f"合计 {omitted_attempts:,} 次尝试，均未渗透成功)"
                )
        return out

    def _render_ssh_successes(self, ssh_successes: list[dict]) -> list[str]:
        """渲染 SSH 成功登录章节。"""
        out = []
        out.append("")
        out.append("## SSH 成功登录")
        if ssh_successes:
            login_counter: dict[tuple, dict] = {}
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
                "| user | method | ip | ip_type | count | first | last |"
            )
            out.append("| --- | --- | --- | --- | --- | --- | --- |")
            for (user, method, ip), info in sorted(
                login_counter.items(), key=lambda x: -x[1]["count"]
            ):
                out.append(
                    f"| {user} | {method} | {ip} | {info['ip_type']} "
                    f"| {info['count']} | {info['first']} | {info['last']} |"
                )
        else:
            out.append("(无数据)")
        return out

    def _render_ssh_protocol_anomalies(self, anomaly_stats: dict) -> list[str]:
        """渲染 SSH 协议异常章节（SA-R003）。"""
        out = []
        if anomaly_stats["total_events"] == 0:
            return out

        out.append("")
        out.append("## SSH 协议异常")
        out.append(
            f"事件总数: {anomaly_stats['total_events']} | "
            f"来源IP: {anomaly_stats['total_ips']} 个"
        )
        if anomaly_stats["unknown_ip_events"] > 0:
            out.append(
                f"⚠️ 其中 {anomaly_stats['unknown_ip_events']} 条事件未能提取来源 IP"
            )

        ip_stats = anomaly_stats["ip_stats"]
        if ip_stats:
            all_unknown = all(s["ip"] == "(未知)" for s in ip_stats)
            if all_unknown and len(ip_stats) == 1:
                s = ip_stats[0]
                types_str = ", ".join(s["types"])
                sample = s["sample_details"][0] if s["sample_details"] else "-"
                if len(sample) > 80:
                    sample = sample[:77] + "..."
                out.append(
                    f"全部 {s['count']} 次事件均未记录来源 IP，"
                    f"异常类型: {types_str}，示例: {sample}"
                )
            else:
                out.append("")
                out.append(
                    "| IP | 分类 | 次数 | 异常类型 | 首次 | 最后 | 示例详情 |"
                )
                out.append("| --- | --- | --- | --- | --- | --- | --- |")
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

    def _render_crontab(self, cron_lines: list[str]) -> list[str]:
        """渲染 Crontab 章节（从 cron syslog 提取唯一命令）。"""
        out = []
        out.append("")
        out.append("## Persistence")
        out.append("")
        out.append("### crontab")
        crond_cmd_lines = [l for l in cron_lines if "CMD (" in l]
        if crond_cmd_lines:
            seen_cmds: set[str] = set()
            dedup_cmds: list[str] = []
            for l in crond_cmd_lines:
                m = re.search(r"CMD \((.+)\)", l)
                if m:
                    cmd = m.group(1).strip()
                    if cmd not in seen_cmds:
                        seen_cmds.add(cmd)
                        dedup_cmds.append(l)
            out.append(f"共 {len(dedup_cmds)} 条唯一 cron 命令（去重后）")
            for l in dedup_cmds[:50]:
                out.append(l)
            if len(dedup_cmds) > 50:
                out.append(f"... (截断，共 {len(dedup_cmds)} 条唯一 cron 命令)")
        else:
            out.append("(无数据)")
        return out

    def _render_ioc_summary(
        self, ssh_failures, ssh_successes, raw_iocs,
    ) -> list[str]:
        """渲染 IOC 汇总章节。"""
        out = []
        ssh_ips: set[str] = set()
        for f in ssh_failures:
            ssh_ips.add(f["ip"])
        for s in ssh_successes:
            ssh_ips.add(s["ip"])

        all_ips = ssh_ips | raw_iocs["ips"]
        external_ips = sorted(
            ip for ip in all_ips if classify_ip(ip) == "external"
        )
        domains = sorted(raw_iocs["domains"])

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
            _MAX_IOC_IPS = 30
            success_ips = {
                s["ip"] for s in ssh_successes
                if classify_ip(s.get("ip", "")) == "external"
            }
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
                    "可通过预分析解压目录精准回查)"
                )

        if domains:
            out.append("### 可疑域名")
            for d in domains:
                out.append(f"- {d}")

        return out

    def _collect_syslog_files(self) -> dict[str, list[Path]]:
        """收集各类型 syslog 文件，按时间排序（旧→新）。

        返回: {"secure": [Path, ...], "messages": [...], "cron": [...]}
        """
        result: dict[str, list[Path]] = {}
        for base in self.SYSLOG_BASES:
            files = []
            for f in self.log_dir.iterdir():
                # 匹配 secure, secure-YYYYMMDD, auth.log, auth.log.1 等
                if f.name == base or f.name.startswith(base + "-") or f.name.startswith(base + "."):
                    if f.is_file() and f.stat().st_size > 0:
                        files.append(f)
            if files:
                files.sort(key=_log_sort_key)
                result[base] = files
                _info(
                    f"找到 {base} 文件 {len(files)} 个: "
                    f"{[f.name for f in files]}"
                )
        return result

    def _read_syslog_files(
        self, syslog_files: dict[str, list[Path]]
    ) -> dict[str, list[str]]:
        """读取各类型 syslog 文件，返回按时间排序的行列表。

        对于超大文件（secure > 50MB），只读取最新的 secure 文件以控制 token。
        """
        LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB

        result: dict[str, list[str]] = {}
        for base, files in syslog_files.items():
            lines: list[str] = []
            for f in files:
                size = f.stat().st_size
                # secure 超大文件：只取最新文件（文件列表已排序，最新在末尾）
                if base in ("secure", "auth.log") and size > LARGE_FILE_THRESHOLD:
                    if f != files[-1]:
                        _info(
                            f"跳过大文件 {f.name} ({size // 1024 // 1024}MB)，"
                            f"仅保留最新"
                        )
                        continue
                    _info(f"读取大文件 {f.name} ({size // 1024 // 1024}MB)")
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                    file_lines = text.splitlines()
                    lines.extend(file_lines)
                    _info(f"读取 {f.name}: {len(file_lines)} 行")
                except Exception as e:
                    print(f"[WARN] 读取 {f} 失败: {e}", file=sys.stderr)
            result[base] = lines
        return result

    def _infer_hostname(self, all_lines: dict[str, list[str]]) -> str:
        """从 syslog 行中推断主机名（取第一行的第三字段）。

        syslog 格式: "Apr 12 03:27:01 HOSTNAME process[PID]: message"
        """
        for base in ("secure", "auth.log", "messages", "cron"):
            for line in all_lines.get(base, [])[:20]:
                parts = line.split()
                if len(parts) >= 4:
                    # syslog 标准格式: month day time hostname ...
                    hostname = parts[3]
                    if hostname and not hostname.startswith("[") and ":" not in hostname:
                        return hostname
        return self.hostname_hint or "unknown"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Linux 原始 /var/log/ 目录预分析工具（Markdown 输出到 stdout）",
        epilog=(
            "示例:\n"
            "  python3 preanalyze_linux_log_folder.py /var/log/\n"
            "  python3 preanalyze_linux_log_folder.py /tmp/extracted/var/log/\n"
            "\n"
            "推荐通过统一入口调用:\n"
            "  python3 scripts/analysis/preanalyze.py /path/to/var/log/\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("log_dir", help="var/log 目录路径")
    parser.add_argument("--hostname", default="", help="主机名提示（可选，自动从日志推断）")

    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"[ERROR] 目录不存在: {log_dir}", file=sys.stderr)
        sys.exit(1)
    if not log_dir.is_dir():
        print(f"[ERROR] 不是目录: {log_dir}", file=sys.stderr)
        sys.exit(1)

    if not can_handle(str(log_dir)):
        print("[ERROR] 该目录不包含可识别的 syslog 文件", file=sys.stderr)
        sys.exit(1)

    print(run(str(log_dir), hostname_hint=args.hostname))


if __name__ == "__main__":
    main()
