"""LinuxCheck.sh 日志精简处理器。

针对 LinuxCheck.sh (al0ne/LinuxCheck) 的 Markdown 格式日志，
按章节进行噪声过滤和信息压缩。

设计原则：
  - 目标 ~4K token（~12K chars），对标 Linux 自研预分析器
  - 激进精简：删除重复章节、截断低价值数据、只保留安全关键信息
  - 输出仍为 Markdown 格式（与原始日志兼容）
"""

import re
from collections import defaultdict

from .constants import (
    CLOUD_INITD_PATTERNS,
    FILE_MTIME_NOISE_PATTERNS,
    HISTORY_MAX_LINES,
    HISTORY_SCRIPT_NOISE_PATTERNS,
    HISTORY_SECURITY_KEYWORDS,
    KERNEL_THREAD_PATTERNS,
    KNOWN_CLOUD_AGENT_PROCS,
    KNOWN_CLOUD_AGENT_SERVICES,
    LAST_LOGIN_MAX_LINES,
    LOCALHOST_PATTERNS,
    PROCESS_TOP_MAX_LINES,
    RE_LAST_LINE,
    SENSITIVE_FILE_NOISE_PATTERNS,
    SSH_KEY_DISPLAY_PREFIX_LEN,
    STANDARD_INITD_SCRIPTS,
    STANDARD_SUID_BASENAMES,
    STANDARD_SYSTEM_PROCS,
    STANDARD_SYSTEM_SERVICES,
    TMP_NOISE_PREFIXES,
)


def compress_last_login(lines: list[str]) -> list[str]:
    """压缩 `last` 登录历史：按 IP 归类计数，只保留最近 N 条原始行。

    策略：
    1. 对全部数据按 (user, ip) 归类计数 → 摘要表格
    2. 保留最近 LAST_LOGIN_MAX_LINES 条原始行
    """
    raw_lines = []
    ip_stats: dict[tuple[str, str], int] = defaultdict(int)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        m = RE_LAST_LINE.match(stripped)
        if m:
            user = m.group(1)
            ip = m.group(3)
            if user != "reboot":
                ip_stats[(user, ip)] += 1
            raw_lines.append(line)
        elif stripped.startswith("wtmp begins"):
            continue
        else:
            raw_lines.append(line)

    result = []

    # 归类摘要（Top 5 IP）
    if ip_stats:
        result.append("")
        result.append("**登录来源统计（Top 5）：**")
        result.append("")
        result.append("| 用户 | 来源IP | 次数 |")
        result.append("| --- | --- | --- |")
        sorted_stats = sorted(ip_stats.items(), key=lambda x: -x[1])
        for (user, ip), count in sorted_stats[:5]:
            result.append(f"| {user} | {ip} | {count} |")
        remaining = len(sorted_stats) - 5
        if remaining > 0:
            result.append(f"| ... | ({remaining} 个其他来源) | |")
        result.append("")

    # 保留最近 N 条原始行
    if len(raw_lines) > LAST_LOGIN_MAX_LINES:
        result.append(
            f"**最近 {LAST_LOGIN_MAX_LINES} 条（共 {len(raw_lines)} 条）：**"
        )
        result.append("")
        result.append("```shell")
        result.extend(raw_lines[:LAST_LOGIN_MAX_LINES])
        result.append("```")
    elif raw_lines:
        result.append("```shell")
        result.extend(raw_lines)
        result.append("```")

    return result


def filter_process_top(lines: list[str]) -> list[str]:
    """过滤 CPU/MEM TOP 进程列表中的标准系统进程和云 Agent，并限制行数。"""
    filtered = []
    filtered_count = 0

    for line in lines:
        # 过滤内核线程
        if any(p in line for p in KERNEL_THREAD_PATTERNS):
            filtered_count += 1
            continue
        # 过滤标准系统守护进程
        if any(proc in line for proc in STANDARD_SYSTEM_PROCS):
            filtered_count += 1
            continue
        # 过滤已知云 Agent
        if any(proc in line for proc in KNOWN_CLOUD_AGENT_PROCS):
            filtered_count += 1
            continue
        filtered.append(line)

    # 只保留 Top N
    result = filtered[:PROCESS_TOP_MAX_LINES]
    extra = len(filtered) - PROCESS_TOP_MAX_LINES
    total_omit = filtered_count + max(0, extra)
    if total_omit > 0:
        result.append(f"(另有 {total_omit} 个进程已省略)")

    return result


def filter_suid_files(lines: list[str]) -> list[str]:
    """过滤标准系统 SUID/SGID 文件。"""
    result = []
    filtered_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 提取路径中的 basename
        path = stripped
        if " " in stripped:
            parts = stripped.split()
            for p in reversed(parts):
                if p.startswith("/"):
                    path = p
                    break
        basename = path.rsplit("/", 1)[-1] if "/" in path else path
        if basename in STANDARD_SUID_BASENAMES:
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个标准 SUID 文件已省略)")

    return result


def filter_tmp_directory(lines: list[str]) -> list[str]:
    """过滤 /tmp 目录列表中的标准系统噪声文件。"""
    result = []
    filtered_count = 0

    for line in lines:
        if any(p in line for p in TMP_NOISE_PREFIXES):
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个标准临时文件已省略)")

    return result


def filter_sensitive_files(lines: list[str]) -> list[str]:
    """过滤敏感文件检测中的 Python 缓存等误报。"""
    result = []
    filtered_count = 0

    for line in lines:
        if any(p in line for p in SENSITIVE_FILE_NOISE_PATTERNS):
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个缓存/云Agent文件已省略)")

    return result


def remove_empty_code_blocks(text: str) -> str:
    """移除空的 ```shell``` 代码块。"""
    text = re.sub(r"```shell\s*\n\s*\n```", "", text)
    text = re.sub(r"```shell\s*\n```", "", text)
    text = re.sub(r"```\s*\n\s*\n```", "", text)
    text = re.sub(r"```\s*\n```", "", text)
    return text


def remove_empty_sections(text: str) -> str:
    """移除内容为空的章节。"""
    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检测 ### 三级标题
        if line.startswith("### ") and not line.startswith("#### "):
            content_lines = []
            j = i + 1
            while j < len(lines):
                if lines[j].startswith("## ") or lines[j].startswith("### "):
                    break
                content_lines.append(lines[j])
                j += 1
            has_content = any(
                l.strip()
                and l.strip() not in ("```shell", "```", "```python")
                for l in content_lines
            )
            if has_content:
                result.append(line)
                i += 1
            else:
                i = j
            continue

        # 检测 ## 二级标题
        if line.startswith("## ") and not line.startswith("### "):
            content_lines = []
            j = i + 1
            while j < len(lines):
                if lines[j].startswith("## ") and not lines[j].startswith(
                    "### "
                ):
                    break
                content_lines.append(lines[j])
                j += 1
            has_content = any(
                l.strip()
                and l.strip() not in ("```shell", "```", "```python")
                and not l.startswith("### ")
                for l in content_lines
            )
            if has_content:
                result.append(line)
                i += 1
            else:
                i = j
            continue

        result.append(line)
        i += 1

    return "\n".join(result)


def collapse_consecutive_blank_lines(text: str) -> str:
    """将连续多个空行压缩为最多两个。"""
    return re.sub(r"\n{4,}", "\n\n\n", text)


def filter_lastlog(lines: list[str]) -> list[str]:
    """过滤 lastlog 输出中的 "Never logged in" 行。"""
    result = []
    filtered_count = 0

    for line in lines:
        if "**Never logged in**" in line or "Never logged in" in line:
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个系统账户从未登录)")

    return result


def filter_mining_self_process(lines: list[str]) -> list[str]:
    """过滤挖矿木马检测中 LinuxCheck.sh 自身进程的误报。"""
    result = []
    filtered_count = 0

    for line in lines:
        if "LinuxCheck" in line and ("bash" in line or "grep" in line):
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(已过滤 {filtered_count} 条 LinuxCheck 自身进程)")

    return result


def filter_running_services(lines: list[str]) -> list[str]:
    """过滤正在运行的 Service 列表中的标准系统服务。"""
    result = []
    std_count = 0
    cloud_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in STANDARD_SYSTEM_SERVICES:
            std_count += 1
            continue
        if any(p in stripped for p in KNOWN_CLOUD_AGENT_SERVICES):
            cloud_count += 1
            continue
        if stripped.endswith(".scope"):
            std_count += 1
            continue
        result.append(line)

    summary = []
    if std_count > 0:
        summary.append(f"{std_count} 个标准系统服务")
    if cloud_count > 0:
        summary.append(f"{cloud_count} 个云Agent服务")
    if summary:
        result.append(f"(另有 {'、'.join(summary)} 已省略)")

    return result


def filter_history_commands(lines: list[str]) -> list[str]:
    """过滤 History 敏感操作中的脚本源码噪声，去重并限制总行数。"""
    security_lines = []
    normal_lines = []
    filtered_count = 0
    seen_commands = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 去重：相同命令只保留一次
        if stripped in seen_commands:
            filtered_count += 1
            continue
        seen_commands.add(stripped)

        lower = stripped.lower()
        # 含安全关键词的行优先保留
        if any(kw in lower for kw in HISTORY_SECURITY_KEYWORDS):
            security_lines.append(line)
            continue

        # 匹配脚本噪声模式
        is_noise = any(p in stripped for p in HISTORY_SCRIPT_NOISE_PATTERNS)
        if is_noise:
            filtered_count += 1
            continue

        # 超长行过滤
        if len(stripped) > 200:
            filtered_count += 1
            continue

        normal_lines.append(line)

    # 合并：安全行全保留 + 普通行截断到 HISTORY_MAX_LINES
    result = security_lines[:]
    remaining_slots = max(0, HISTORY_MAX_LINES - len(security_lines))
    result.extend(normal_lines[:remaining_slots])
    extra_normal = len(normal_lines) - remaining_slots
    total_omit = filtered_count + max(0, extra_normal)

    if total_omit > 0:
        result.append(f"(已过滤 {total_omit} 行噪声/重复/非关键命令)")

    return result


def filter_network_connections(lines: list[str]) -> list[str]:
    """过滤并聚合网络连接。

    - UDP 连接全部过滤（与端口监听重复）
    - localhost 回环和云 Agent 连接过滤
    - 同一远端 IP 的多条连接聚合为一行
    """
    tcp_connections = {}  # remote_ip -> [{"local_port", "remote_port", "state", "proc"}]
    filtered_count = 0
    in_udp_section = False
    result = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检测 UDP 区域标记
        if "UDP" in stripped and ("连接" in stripped or "Connection" in stripped):
            in_udp_section = True
            continue

        # TCP 区域标记
        if "TCP" in stripped and ("连接" in stripped or "Connection" in stripped):
            in_udp_section = False
            continue

        # UDP 区域全部跳过
        if in_udp_section:
            filtered_count += 1
            continue

        # 解析 TCP 连接行
        parts = stripped.split()
        if len(parts) < 5 or parts[0] not in ("tcp", "tcp6"):
            # 非数据行跳过
            continue

        local_addr = parts[3]
        foreign_addr = parts[4]

        # 过滤 localhost
        local_is_lo = any(p in local_addr for p in LOCALHOST_PATTERNS)
        foreign_is_lo = any(p in foreign_addr for p in LOCALHOST_PATTERNS)
        if local_is_lo and foreign_is_lo:
            filtered_count += 1
            continue

        # 过滤云 Agent
        if any(proc in line for proc in KNOWN_CLOUD_AGENT_PROCS):
            filtered_count += 1
            continue

        # 提取远端 IP（去掉端口）
        is_ipv6 = parts[0] == "tcp6"
        if is_ipv6:
            # IPv6 格式：:::port 或 ::ffff:ip:port — 用最后一个 ":" 分割
            # 但 netstat IPv6 也可能是 ::1:631 形式
            if foreign_addr.startswith(":::"):
                remote_ip = "::"
            elif "." in foreign_addr:
                # IPv4-mapped: ::ffff:10.0.0.1:443 → 按最后一个 ":" 分割
                remote_ip = foreign_addr.rsplit(":", 1)[0]
            else:
                remote_ip = foreign_addr.rsplit(":", 1)[0]
        else:
            # IPv4 格式：ip:port
            remote_ip = foreign_addr.rsplit(":", 1)[0] if ":" in foreign_addr else foreign_addr

        # 提取本地端口
        if is_ipv6 and local_addr.startswith(":::"):
            local_port = local_addr[3:]
        elif ":" in local_addr:
            local_port = local_addr.rsplit(":", 1)[-1]
        else:
            local_port = ""

        # 提取状态和进程
        state = parts[5] if len(parts) > 5 else ""
        proc_info = ""
        for p in parts[6:]:
            if "/" in p:
                proc_info = p.split("/")[-1]
                break

        if remote_ip not in tcp_connections:
            tcp_connections[remote_ip] = []
        tcp_connections[remote_ip].append({
            "local_port": local_port,
            "state": state,
            "proc": proc_info,
        })

    # 输出聚合结果
    if tcp_connections:
        for remote_ip, conns in tcp_connections.items():
            if len(conns) == 1:
                c = conns[0]
                result.append(
                    f"→ {remote_ip} :{c['local_port']} {c['state']} {c['proc']}"
                )
            else:
                ports = ",".join(c["local_port"] for c in conns)
                proc = conns[0]["proc"]
                result.append(
                    f"→ {remote_ip} :{ports} ({len(conns)}连接) {proc}"
                )

    if filtered_count > 0:
        result.append(
            f"(另有 {filtered_count} 个UDP/回环/云Agent连接已省略)"
        )

    return result


def filter_port_listening(lines: list[str]) -> list[str]:
    """精简端口监听：只保留对外暴露的端口，去重 tcp6/udp6。"""
    result = []
    seen_ports = set()  # 按端口号去重（tcp6 中 :::22 与 tcp 中 0.0.0.0:22 重复）

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 过滤云 Agent 端口
        if any(proc in line for proc in KNOWN_CLOUD_AGENT_PROCS):
            continue

        parts = stripped.split()
        if len(parts) >= 7 and parts[0] in ("tcp", "tcp6", "udp", "udp6"):
            proto = parts[0]
            addr = parts[3]

            # 过滤 localhost 绑定
            if any(p in addr for p in ("127.0.0.1", "::1")):
                continue

            # 提取端口号
            port = addr.rsplit(":", 1)[-1] if ":" in addr else ""
            base_proto = proto.replace("6", "")  # tcp6 → tcp

            # tcp6/udp6 与 tcp/udp 重复则跳过
            if proto.endswith("6"):
                if f"{base_proto}|{port}" in seen_ports:
                    continue

            seen_ports.add(f"{base_proto}|{port}")

            proc_info = parts[-1] if "/" in parts[-1] else ""
            proc_name = proc_info.split("/")[-1] if proc_info else ""
            result.append(f"{base_proto} :{port} {proc_name}")
        else:
            result.append(line)

    return result


def filter_initd(lines: list[str]) -> list[str]:
    """过滤 /etc/init.d 中的标准系统脚本。"""
    result = []
    filtered_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 目录头行跳过
        if stripped.startswith("total ") or stripped.startswith("drwx"):
            continue
        # 提取脚本名（ls -la 格式最后一列）
        parts = stripped.split()
        if not parts:
            continue
        script_name = parts[-1].rsplit("/", 1)[-1] if parts[-1] else ""
        # 标准系统脚本
        if script_name in STANDARD_INITD_SCRIPTS:
            filtered_count += 1
            continue
        # 云厂商脚本
        if any(p in script_name for p in CLOUD_INITD_PATTERNS):
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个标准/云Agent脚本已省略)")

    return result


def filter_file_mtime(lines: list[str]) -> list[str]:
    """过滤文件 mtime 列表中的噪声文件。"""
    result = []
    filtered_count = 0

    for line in lines:
        if any(p in line for p in FILE_MTIME_NOISE_PATTERNS):
            filtered_count += 1
            continue
        result.append(line)

    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个临时/系统文件已省略)")

    return result


def filter_authorized_keys(lines: list[str]) -> list[str]:
    """截断 SSH authorized_keys 公钥内容，只保留类型+指纹前缀+注释。

    完整公钥内容对入侵分析无价值（太长），只需知道：
    1. 密钥类型（ssh-ed25519/ssh-rsa）
    2. 密钥指纹前缀（用于去重辨识）
    3. 用户注释（谁的密钥）
    """
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[0].startswith("ssh-"):
            key_type = parts[0]
            key_body = parts[1]
            comment = " ".join(parts[2:]) if len(parts) > 2 else ""
            truncated_key = key_body[:SSH_KEY_DISPLAY_PREFIX_LEN] + "..."
            entry = f"{key_type} {truncated_key}"
            if comment:
                entry += f" {comment}"
            result.append(entry)
        else:
            result.append(line)
    return result
