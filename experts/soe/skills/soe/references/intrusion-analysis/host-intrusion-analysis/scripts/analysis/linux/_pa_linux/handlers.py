"""各章节精简处理器。

每个 handler 函数接收一个子章节的原始文本行列表，
返回精简后的行列表。
"""

import re
from collections import defaultdict

from _common import cloud_vendor as _cloud_vendor

from .constants import (
    HISTORY_HIGH_RISK_PATTERNS,
    KNOWN_CLOUD_AGENT_PROCS,
    KNOWN_CLOUD_IPTABLES_CHAINS,
    NEVER_SKIP_PATTERNS,
    PERSIST_AUTHKEY,
    PERSIST_CRONTAB,
    PERSIST_INITD,
    PERSIST_PROFILE,
    PERSIST_RCLOCAL,
    PERSIST_RCLOCAL_INACTIVE,
    PERSIST_SYSTEMD,
    RE_GROUPADD,
    RE_HISTORY_USER,
    RE_PASSWD_CHANGE,
    RE_PASSWD_LINE,
    RE_SUDO,
    RE_USERADD,
    RE_USERMOD,
    SSHD_CONFIG_ALERT_PATTERNS,
    SSHD_MAX_AUTH_TRIES_THRESHOLD,
    STANDARD_DNS_SERVERS,
    STANDARD_PROFILE_MARKERS,
    STANDARD_SUDOERS_LINES,
    STANDARD_SUDOERS_PREFIXES,
)

# IP / 域名提取正则（用于 IOC 汇总）
_RE_IPV4 = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
# 域名匹配：TLD 为 2-6 位纯字母，排除 systemd unit 类型和常见文件扩展名
_RE_DOMAIN = re.compile(
    r"\b((?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"(?!(?:service|socket|timer|target|mount|slice|scope|swap|"
    r"config|conf|log|txt|py|sh|bash|md|yml|yaml|json|xml|csv|"
    r"lock|bak|old|tmp|pid|so|ko|img|iso|gz|xz|zst|deb|rpm)\b)"
    r"[a-zA-Z]{2,6})\b"
)

# 已知误报域名模式（Linux 系统路径、Python 模块等）
_FALSE_POSITIVE_DOMAINS = {
    "bash.bashrc", "cron.daily", "cron.hourly", "cron.weekly", "cron.monthly",
    "rc.local", "init.local", "pty.spawn", "time.sleep",
    "s.bind", "s.close", "s.listen", "s.connect", "s.accept", "s.send",
    "os.path", "os.system", "sys.exit", "sys.argv",
}

# 域名误报检测辅助规则
_FALSE_POSITIVE_DOMAIN_PATTERNS = [
    "dbus-org.",        # dbus 服务标识，非域名
    ".comssh",          # SSH 公钥注释粘连（如 user@example.comssh-rsa）
    "rootkit.tar",      # 文件名，非域名
]

# 已知良性 IP 白名单（公共 DNS、云元数据等），IOC 汇总时排除
# 基于 STANDARD_DNS_SERVERS 扩展，避免重复维护
_BENIGN_IPS = STANDARD_DNS_SERVERS | {
    "169.254.169.254",               # 云元数据服务
}

# 已知良性域名后缀白名单，IOC 汇总时排除
_BENIGN_DOMAIN_SUFFIXES = (
    ".ubuntu.com", ".debian.org", ".redhat.com", ".centos.org",
    ".fedoraproject.org", ".kernel.org", ".gnu.org", ".apache.org",
    ".github.com", ".githubusercontent.com",
    ".launchpad.net", ".sourceforge.net",
    ".google.com", ".googleapis.com", ".gstatic.com",
    ".microsoft.com", ".windows.com",
    ".cloudflare.com", ".akamai.com",
)

# 持久化汇总中 Shell Profile 误报白名单——标准 .bashrc 默认行
_PROFILE_FALSE_POSITIVE_PATTERNS = [
    "lesspipe",
    "dircolors",
    "command-not-found",
    "bash_completion",
]


def handler_skip(sub_lines: list[str]) -> list[str] | None:
    """通用跳过 handler，但恶意模式安全兜底。

    用于 hardware、mem_top15、route、arp、_ExecutionTiming、REPORT_END 等
    对 AI 分析无价值的子章节。如果任何行匹配恶意模式则全量输出。
    """
    for line in sub_lines:
        if any(p in line.lower() for p in NEVER_SKIP_PATTERNS):
            return sub_lines
    return None


def handler_whoami(sub_lines: list[str]) -> list[str]:
    """压缩 whoami 为一行摘要。"""
    user = "?"
    uid_info = ""
    for line in sub_lines:
        stripped = line.strip()
        if stripped.startswith("uid="):
            uid_info = stripped
        elif stripped and not stripped.startswith("--") and not uid_info:
            user = stripped
    if uid_info:
        return [uid_info]
    return [user]


def handler_security_hygiene(sub_lines: list[str]) -> list[str] | None:
    """精简 security_hygiene：只输出异常项。

    正常基线：SELinux=enforcing, Firewall=active, Auditd=running 等。
    偏离基线的项保留输出。
    """
    # 安全基线正常值（匹配则不输出）
    NORMAL_VALUES = {
        "SELinux": {"enforcing"},
        "Firewall_UFW": {"active"},
        "Firewall_firewalld": {"running"},
        "SSH_PermitRootLogin": {"no", "without-password", "prohibit-password"},
        "SSH_PasswordAuth": {"no"},
        "Auditd": {"running"},
    }
    # 纯信息项（永远不输出，不影响安全判断）
    INFO_ONLY_KEYS = {"SSH_Port", "AvailDiskMB", "SSH_Service"}

    abnormal = []
    for line in sub_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if key in INFO_ONLY_KEYS:
                continue
            if key in NORMAL_VALUES and val in NORMAL_VALUES[key]:
                continue
            # 不在基线中的项（如 not_installed）或偏离基线的项
            abnormal.append(stripped)
        else:
            abnormal.append(stripped)

    if not abnormal:
        return None
    result = [f"安全配置异常 ({len(abnormal)} 项):"]
    result.extend(abnormal)
    return result


def handler_sudoers(sub_lines: list[str]) -> list[str] | None:
    """精简 sudoers：过滤标准行和目录列表，只保留自定义 sudoers 规则。

    过滤内容：
    - 主 sudoers 文件的默认行（root/admin/sudo ALL=...、Defaults、注释）
    - sudoers.d 目录列表（ls -la 输出）
    - sudoers.d/README 内容
    保留内容：
    - 自定义 sudoers 规则（特别是 NOPASSWD 规则）
    """
    result = []
    in_dir_listing = False
    in_readme = False

    for line in sub_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # sudoers.d 目录列表段（ls -la 输出）→ 跳过
        if "sudoers.d" in stripped and stripped.startswith("-- cmd:"):
            in_dir_listing = True
            continue
        if in_dir_listing:
            if stripped.startswith(("total ", "drw", "-r", "lrw", ".")):
                continue
            in_dir_listing = False

        # sudoers.d 文件内容段
        if stripped.startswith("-- file:"):
            in_readme = False
            # README 文件内容不输出
            if "README" in stripped:
                in_readme = True
                continue
            result.append(line)
            continue
        if in_readme:
            continue

        # 命令执行失败行跳过
        if stripped.startswith("(命令执行失败"):
            continue

        # 主 sudoers 文件：过滤标准行
        if any(stripped.startswith(p) for p in STANDARD_SUDOERS_PREFIXES):
            continue
        if stripped in STANDARD_SUDOERS_LINES:
            continue
        # 段标题
        if stripped.startswith("-- cmd:") or stripped.startswith("=="):
            continue

        # 自定义规则
        result.append(line)

    if not result:
        return None
    return result


def handler_sshd_stat(sub_lines: list[str]) -> list[str]:
    """压缩 sshd_stat 为一行摘要：md5 + mtime + size。"""
    md5_val = mtime_val = size_val = "?"
    for line in sub_lines:
        stripped = line.strip()
        if stripped.startswith("md5") or "hash=" in stripped:
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                md5_val = parts[1].strip()
            elif " " in stripped:
                md5_val = stripped.split()[-1]
        elif "Modify:" in stripped or "mtime" in stripped.lower():
            parts = stripped.split(":", 1) if ":" in stripped else stripped.split("=", 1)
            if len(parts) == 2:
                mtime_val = parts[1].strip()
        elif "Size:" in stripped or "size" in stripped.lower():
            parts = stripped.split(":", 1) if ":" in stripped else stripped.split("=", 1)
            if len(parts) == 2:
                size_val = parts[1].strip()
        # 兜底：如果是 stat 输出格式行
        if stripped.startswith("  File:") or stripped.startswith("  Size:"):
            result_parts = stripped.split()
            for i, p in enumerate(result_parts):
                if p == "Size:" and i + 1 < len(result_parts):
                    size_val = result_parts[i + 1]

    return [f"sshd 二进制: md5={md5_val} | mtime={mtime_val} | size={size_val}"]


def handler_ip_forward(sub_lines: list[str]) -> list[str] | None:
    """ip_forward：值为 0 时跳过，非 0 时告警输出。"""
    has_nonzero = False
    for line in sub_lines:
        stripped = line.strip()
        if stripped.isdigit() and stripped != "0":
            has_nonzero = True
            break
        if stripped == "1":
            has_nonzero = True
            break
    if not has_nonzero:
        return None
    return ["⚠️ IP 转发已启用:"] + sub_lines


def handler_crontab(sub_lines: list[str]) -> list[str]:
    """精简 crontab 子章节：去掉注释/空行，保留实际 cron 条目。

    root crontab 和 /var/spool/cron/crontabs/root 内容常完全重复，
    脚本层去重只输出一份。
    """
    result = []
    # 按段收集 cron 条目用于去重
    root_crontab_entries: set[str] = set()
    current_section = ""
    in_spool = False

    for line in sub_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # 段标题
        if stripped.startswith("=="):
            current_section = stripped
            if "root crontab" in stripped:
                in_spool = False
                result.append(line)
            elif "/var/spool/cron" in stripped:
                in_spool = True
                result.append(line)
            else:
                in_spool = False
                result.append(line)
            continue
        if stripped.startswith("-- file:"):
            result.append(line)
            continue
        # 过滤环境变量设置
        if stripped.startswith(("SHELL=", "PATH=")):
            continue
        # 去重：spool 中与 root crontab 重复的条目不输出
        if "root crontab" in current_section:
            root_crontab_entries.add(stripped)
            result.append(line)
        elif in_spool and stripped in root_crontab_entries:
            continue  # 与 root crontab 重复，跳过
        else:
            result.append(line)

    # 清理只剩段标题但无实际条目的段
    # 第一遍：标记需要保留的行索引
    keep = [True] * len(result)
    for i, line in enumerate(result):
        stripped = line.strip()
        if stripped.startswith("==") or stripped.startswith("-- file:"):
            # 看后面是否有实际内容行
            has_content = False
            for j in range(i + 1, len(result)):
                next_s = result[j].strip()
                if next_s.startswith("=="):
                    break
                if (next_s and not next_s.startswith("--")
                        and not next_s.startswith("(无数据")):
                    has_content = True
                    break
            if not has_content:
                # 标记该段标题及其下属的 (无数据) 行都跳过
                keep[i] = False
                for j in range(i + 1, len(result)):
                    next_s = result[j].strip()
                    if next_s.startswith("=="):
                        break
                    if next_s.startswith("(无数据") or next_s.startswith("-- file:"):
                        keep[j] = False
                    elif next_s:
                        break

    cleaned = [line for i, line in enumerate(result) if keep[i]]

    if not cleaned:
        cleaned.append("(无 crontab 数据)")
    return cleaned


def handler_authorized_keys(sub_lines: list[str]) -> list[str]:
    """精简 authorized_keys：权限/owner 元数据压缩为行内标注。"""
    result = []
    current_file = ""
    current_perms = ""
    current_owner = ""

    for line in sub_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--------"):
            continue
        if line.startswith("-- file:"):
            # 输出上一个文件的信息
            current_file = line.replace("-- file:", "").strip().rstrip(" --")
            current_perms = ""
            current_owner = ""
            continue
        if stripped.startswith("permissions:"):
            current_perms = stripped.replace("permissions:", "").strip()
            continue
        if stripped.startswith("owner:"):
            current_owner = stripped.replace("owner:", "").strip()
            continue
        # SSH 公钥行：附加元数据为行内标注
        if stripped.startswith(("ssh-rsa", "ssh-ed25519", "ssh-dss", "ecdsa-sha2")):
            meta = ""
            if current_perms or current_owner:
                meta = f" [{current_perms} {current_owner}]".strip()
            if current_file and current_file not in str(result):
                result.append(f"**{current_file}**{meta}:")
            result.append(f"  {stripped}")
        else:
            result.append(line)

    if not result:
        result.append("(无 authorized_keys 数据)")
    return result


def handler_package_verify(sub_lines: list[str]) -> list[str] | None:
    """精简 package_verify：debsums 未安装时跳过，有异常时输出。"""
    has_data = False
    has_anomaly = False
    for line in sub_lines:
        stripped = line.strip()
        if "not installed" in stripped.lower() or "未安装" in stripped:
            continue
        if stripped and not stripped.startswith("--"):
            has_data = True
        if "FAILED" in stripped or "changed" in stripped.lower():
            has_anomaly = True
    if not has_data:
        return None
    if not has_anomaly:
        # 有数据但无异常 → 跳过（"无异常"对 AI 分析无指导价值）
        return None
    # 有异常，全量输出
    return sub_lines


def handler_shell_profiles(sub_lines: list[str]) -> list[str] | None:
    """精简 shell_profiles：跳过标准配置文件内容块。

    恶意模式白名单 (NEVER_SKIP_PATTERNS)：即使在标准文件区域内，
    匹配这些模式的行永远不会被省略，防止后门命令被误过滤。

    标准配置文件不逐个列出，最终聚合为一行计数摘要。
    """
    # .bash_logout 标准内容标记
    _BASH_LOGOUT_MARKERS = [
        "~/.bash_logout",
        "clear_console",
        "increase privacy",
    ]

    result = []
    in_standard_file = False
    current_file = ""
    malicious_lines_count = 0  # OPT-P02: 统计恶意模式命中行数
    standard_file_count = 0    # 标准配置文件计数（不逐个输出）
    current_file_is_standard = False  # 当前文件是否整体为标准配置

    for line in sub_lines:
        # 检测文件头
        if line.startswith("-- file:"):
            # 上一个文件如果是标准配置（没有恶意行输出），计入标准计数
            if current_file and current_file_is_standard:
                standard_file_count += 1

            current_file = line
            in_standard_file = False
            current_file_is_standard = True  # 假设标准，发现恶意/非标准行时翻转
            # 检测是否为 .bash_logout 文件（标准内容通常只有 clear_console）
            if ".bash_logout" in line:
                in_standard_file = True
                # 不输出文件头和标准标记，统计时处理
                continue
            # 暂不输出文件头，等确认有非标准内容再输出
            continue

        # SA-R009: 恶意模式永不省略（优先级最高）
        # 但排除标准 .bashrc 的 lesspipe/dircolors 行（含 eval 但无害）
        line_lower = line.lower()
        if any(p in line_lower for p in NEVER_SKIP_PATTERNS):
            if any(fp in line_lower for fp in _PROFILE_FALSE_POSITIVE_PATTERNS):
                if not in_standard_file:
                    in_standard_file = True
                continue
            # 即使在 .bash_logout 中，恶意模式也要输出
            if in_standard_file and ".bash_logout" in current_file:
                # 排除 .bash_logout 的标准内容匹配
                if any(m in line for m in _BASH_LOGOUT_MARKERS):
                    continue
            # 发现恶意行 → 输出文件头（如果尚未输出）
            if current_file_is_standard and current_file:
                result.append(current_file)
                current_file_is_standard = False
            result.append(line)
            malicious_lines_count += 1
            in_standard_file = False
            continue

        # 在标准文件中（包括 .bash_logout），跳过所有行
        if in_standard_file:
            if line.strip().startswith("--------"):
                in_standard_file = False
            continue

        # 检测是否进入标准配置文件
        if any(marker in line for marker in STANDARD_PROFILE_MARKERS):
            if not in_standard_file:
                in_standard_file = True
            continue

        # 非标准行 → 输出文件头（如果尚未输出）
        if current_file_is_standard and current_file:
            result.append(current_file)
            current_file_is_standard = False
        result.append(line)

    # 处理最后一个文件
    if current_file and current_file_is_standard:
        standard_file_count += 1

    # 标准文件聚合摘要
    if standard_file_count > 0:
        result.append(f"(另有 {standard_file_count} 个标准 shell 配置文件已省略)")

    # OPT-P02: 输出恶意行统计摘要
    if malicious_lines_count > 0:
        result.append("")
        result.append(
            f"⚠️ Shell Profile 中检测到 {malicious_lines_count} 行匹配恶意模式"
            "（curl/wget/nc/base64/eval 等），请逐行分析持久化后门"
        )

    # 只有标准文件计数、无恶意模式且无非标准内容时，返回 None
    has_content = any(
        l.strip()
        and not l.startswith("(另有")
        and not l.startswith("-- file:")
        for l in result
    )
    if not has_content and malicious_lines_count == 0:
        return None
    return result


def handler_init_d(sub_lines: list[str]) -> list[str]:
    """精简 init_d：压缩目录列表，去掉 INIT INFO 块，过滤已知云 agent 脚本。

    云 agent init.d 脚本名清单从 ``config/cloud_vendor_processes.json`` 的
    ``initd_scripts`` 字段加载（本仓库默认空），脚本内容不输出，只保留自定义/可疑
    脚本核心内容。
    """
    # 已知云厂商 init.d 脚本名（从外部配置加载，子字符串匹配；本仓库默认空）
    KNOWN_CLOUD_INITD = _cloud_vendor.initd_scripts()

    result = []
    in_dir_listing = True  # init_d 通常以 ls -la 目录列表开头
    in_init_info = False
    in_known_agent = False
    dir_file_count = 0

    for line in sub_lines:
        stripped = line.strip()
        # 跳过 [known] 标记的标准服务
        if stripped.startswith("[known]"):
            continue
        # 检测目录列表行（ls -la 格式：以权限、total、. 开头）
        if in_dir_listing:
            if stripped.startswith(("total ", "drw", "-rw", "lrw")):
                dir_file_count += 1
                continue
            else:
                in_dir_listing = False
        # 检测文件段标题（-- file: /etc/init.d/xxx --）
        if stripped.startswith("-- file:"):
            in_known_agent = False
            # 提取文件名
            fname = stripped.replace("-- file:", "").strip()
            # 去掉 "(前 N 行)" 后缀和 " --" 后缀
            fname = fname.split("(")[0].strip().rstrip(" -")
            # 提取基础名
            base = fname.rsplit("/", 1)[-1] if "/" in fname else fname
            if base in KNOWN_CLOUD_INITD:
                in_known_agent = True
                continue
            result.append(line)
            continue
        # 在已知 agent 文件内容段中，只保留恶意模式行
        if in_known_agent:
            if any(p in line for p in NEVER_SKIP_PATTERNS):
                result.append(line)
            continue
        # 跳过 INIT INFO 块（标准 init 脚本头部注释）
        if "### BEGIN INIT INFO" in stripped:
            in_init_info = True
            continue
        if "### END INIT INFO" in stripped:
            in_init_info = False
            continue
        if in_init_info:
            continue
        # 跳过 shebang 和空注释行（仅过滤 "#" 或 "#\n" 等无内容注释）
        if stripped.startswith("#!") or stripped == "#":
            continue
        result.append(line)
    return result


def handler_systemd_units(sub_lines: list[str]) -> list[str]:
    """精简 systemd_units：只保留自定义 unit 部分，并提取 ExecStart 命令内容。"""
    result = []
    in_custom = False
    exec_start_count = 0
    for line in sub_lines:
        if "自定义 systemd service" in line:
            in_custom = True
        if in_custom:
            result.append(line)
            # OPT-P01: 标注 ExecStart 命令便于 AI 识别 C2 信标
            stripped = line.strip()
            if stripped.startswith(("ExecStart=", "ExecStartPre=", "ExecStartPost=")):
                exec_start_count += 1
            continue
        # 跳过统计行（如 "66 unit files listed."），对分析无价值
    if not result:
        result.append("(无自定义 unit)")
    elif exec_start_count > 0:
        result.append("")
        result.append(
            f"⚠️ 自定义 unit 中包含 {exec_start_count} 条 ExecStart 命令，"
            "请逐条分析是否存在 C2 信标（网络回连/定时循环/编码执行）"
        )
    return result


def handler_reverse_shell_check(sub_lines: list[str]) -> list[str]:
    """精简 reverse_shell_check：结构化提取 ESTABLISHED 连接 + 反弹 Shell 检测结论。

    输出:
    1. ESTABLISHED 连接结构化表格（远程IP:端口 + 进程名）
    2. /dev/tcp|udp 使用检测结论
    3. 反弹 Shell 模式检测结果（含进程命令行）
    4. 连接状态交叉验证：反弹 Shell 目标 IP 是否在 ESTABLISHED 列表中
    """
    result = []
    established_conns: list[dict] = []   # {remote_ip, remote_port, process, pid}
    reverse_shell_lines: list[str] = []  # 反弹 Shell 模式检测命中行
    devtcp_conclusion = ""               # /dev/tcp|udp 使用检测结论

    # --- 解析 ---
    in_established = False
    in_reverse_pattern = False
    for line in sub_lines:
        stripped = line.strip()

        # ESTABLISHED 连接段
        if "Established TCP" in line:
            in_established = True
            in_reverse_pattern = False
            continue
        if in_established and stripped.startswith("ESTAB"):
            # 解析 ss -tnp 格式:
            # ESTAB  0  0  172.30.0.8:41776  100.64.250.72:2000  users:(("proc",pid=N,fd=M))
            # 使用正则提取 local:port、remote:port 和 users:(...) 段
            m_estab = re.search(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)\s+"
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)\s+"
                r"(users:\(.+)",
                stripped,
            )
            if m_estab:
                rip = m_estab.group(2)
                rport = m_estab.group(3)
                proc_info = m_estab.group(4).strip()
                established_conns.append({
                    "remote_ip": rip,
                    "remote_port": rport,
                    "process": proc_info,
                })
            # 原始 ESTAB 行不重复输出，已结构化提取到表格中
            continue
        if in_established and not stripped.startswith("ESTAB") and stripped:
            in_established = False

        # 跳过段标题行（== xxx ==）
        if stripped.startswith("==") and stripped.endswith("=="):
            # 检测 Reverse shell pattern 段标题
            if "reverse shell" in stripped.lower():
                in_reverse_pattern = True
            continue

        # /dev/tcp|udp 使用检测结论
        if "/dev/tcp" in line or "/dev/udp" in line:
            if "未发现" in line:
                devtcp_conclusion = stripped
            # 含 /dev/tcp 的进程命令行不在此处输出，由反弹 Shell 段处理
        elif "未发现" in line and ("tcp" in line.lower() or "udp" in line.lower()):
            devtcp_conclusion = stripped

        # 反弹 Shell 模式检测段
        if "Reverse shell pattern" in line or "reverse shell" in line.lower():
            in_reverse_pattern = True
            continue
        if in_reverse_pattern and stripped:
            reverse_shell_lines.append(stripped)

    # --- 输出结构化结果 ---
    # 过滤已知云 agent 的 ESTABLISHED 连接（对入侵分析无价值）
    suspicious_conns = []
    filtered_conn_count = 0
    for conn in established_conns:
        if any(p in conn["process"] for p in KNOWN_CLOUD_AGENT_PROCS):
            filtered_conn_count += 1
        else:
            suspicious_conns.append(conn)

    if suspicious_conns:
        result.insert(0, f"**ESTABLISHED 连接: {len(suspicious_conns)} 条可疑**")
        result.insert(1, "")
        result.insert(2, "| 远程IP | 端口 | 进程 |")
        result.insert(3, "| --- | --- | --- |")
        for i, conn in enumerate(suspicious_conns):
            result.insert(4 + i, f"| {conn['remote_ip']} | {conn['remote_port']} | {conn['process']} |")
        if filtered_conn_count > 0:
            result.insert(4 + len(suspicious_conns),
                          f"(另有 {filtered_conn_count} 个已知云 agent 连接已省略)")
        result.insert(4 + len(suspicious_conns) + (1 if filtered_conn_count else 0), "")

    if devtcp_conclusion:
        result.append(f"**/dev/tcp|udp 检查:** {devtcp_conclusion}")

    # 提取反弹 Shell 目标 IP 并交叉验证
    if reverse_shell_lines:
        result.append("")
        result.append("**反弹 Shell 模式检测:**")
        established_ips = {c["remote_ip"] for c in established_conns}  # 全量用于交叉验证
        for rs_line in reverse_shell_lines:
            # 截断过长的 ps 命令行（保留前 120 字符）
            display = rs_line if len(rs_line) <= 120 else rs_line[:117] + "..."
            result.append(f"- `{display}`")
            # 从完整行（非截断）提取目标 IP
            target_ip = None
            m = re.search(r"/dev/tcp/([^/]+)/(\d+)", rs_line)
            if m:
                target_ip = m.group(1)
            else:
                m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d+)", rs_line)
                if m:
                    target_ip = m.group(1)
            if target_ip:
                if target_ip in established_ips:
                    result.append(f"  → ✅ {target_ip} 在 ESTABLISHED 列表中")
                else:
                    result.append(f"  → ⚠️ {target_ip} 不在 ESTABLISHED 列表中")

    if not result:
        result.append("(无反弹 Shell 检测数据)")
    return result


def handler_pam_check(sub_lines: list[str]) -> list[str] | None:
    """精简 pam_check：只关注近 30 天修改的 PAM .so 文件和非标准 PAM 模块。

    标准 Ubuntu/Debian PAM 配置（@include common-*, pam_selinux.so 等）对
    入侵分析无价值。只有以下情况才输出：
    - 发现近 30 天修改的 PAM .so 文件
    - 发现恶意模式
    否则返回 None 跳过。
    """
    # 恶意模式兜底
    for line in sub_lines:
        if any(p in line.lower() for p in NEVER_SKIP_PATTERNS):
            return sub_lines

    # 只检查是否有近期修改的 PAM .so 文件
    in_pam_so = False
    recent_mod_files = []
    for line in sub_lines:
        if "最近 30 天修改" in line:
            in_pam_so = True
            continue
        if in_pam_so:
            stripped = line.strip()
            if stripped and "未发现" not in stripped and stripped != "(无)":
                recent_mod_files.append(line)

    if not recent_mod_files:
        return None

    result = ["== 最近 30 天修改过的 PAM .so 文件 =="]
    result.extend(recent_mod_files)
    return result


def handler_env_variables(sub_lines: list[str]) -> list[str] | None:
    """精简 env_variables：只保留可疑环境变量检查段结果。

    标准环境变量列表（HOME/PATH/SHELL 等）对入侵分析无价值。
    只关注"可疑环境变量检查"段的结论。
    结论为"未发现可疑"时返回 None 跳过。
    """
    # 恶意模式兜底
    for line in sub_lines:
        if any(p in line for p in NEVER_SKIP_PATTERNS):
            return sub_lines

    result = []
    in_suspicious = False
    has_suspicious = False

    for line in sub_lines:
        stripped = line.strip()
        # 可疑变量检查段 — 全部保留
        if "可疑环境变量检查" in line:
            in_suspicious = True
            result.append(line)
            continue
        if in_suspicious:
            result.append(line)
            if stripped and "未发现" not in stripped and "无可疑" not in stripped:
                has_suspicious = True
            continue
        # LD_PRELOAD / LD_LIBRARY_PATH / LD_AUDIT 异常值
        if "=" in line and not line.startswith("("):
            var_name = line.split("=", 1)[0].strip()
            if var_name in ("LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT"):
                has_suspicious = True
                result.append(line)

    if not has_suspicious:
        return None
    return result


def handler_kernel_modules(sub_lines: list[str]) -> list[str] | None:
    """精简 kernel_modules：只保留无签名模块检查结果。

    全部有签名时返回 None 跳过。
    """
    # 恶意模式兜底
    for line in sub_lines:
        if any(p in line for p in NEVER_SKIP_PATTERNS):
            return sub_lines

    result = []
    in_unsigned = False

    for line in sub_lines:
        # 无签名模块检查段 — 全部保留
        if "无签名" in line or "非标准内核模块" in line:
            in_unsigned = True
            result.append(line)
            continue
        if in_unsigned:
            result.append(line)
            continue

    # 全部有签名（无 unsigned 段内容，或结论为"全部有签名"）→ 跳过
    if not in_unsigned:
        return None
    # 如果 unsigned 段只有"所有已加载模块均有签名"类结论
    if all("均有签名" in l or "所有" in l or "all" in l.lower()
           for l in result if l.strip() and not l.strip().startswith("==")):
        return None
    return result



def handler_suid_sgid(sub_lines: list[str]) -> list[str] | None:
    """精简 suid_sgid：过滤标准系统 SUID/SGID 文件，只保留非标准/可疑文件。

    标准系统 SUID/SGID 文件（如 /usr/bin/passwd, /usr/bin/sudo 等）是正常的，
    过滤后大幅减少输出量，让 AI 聚焦于异常文件。
    """
    # 标准系统 SUID/SGID 文件白名单（常见 Linux 发行版）
    # 同时支持完整路径匹配和 basename 匹配，兼容不同发行版的安装路径差异
    # （如 /usr/lib/ vs /usr/libexec/）
    STANDARD_SUID_FILES = {
        # 基础系统工具
        "/usr/bin/passwd", "/usr/bin/chage", "/usr/bin/chfn", "/usr/bin/chsh",
        "/usr/bin/gpasswd", "/usr/bin/newgrp", "/usr/bin/expiry",
        # 权限/身份
        "/usr/bin/su", "/usr/bin/sudo", "/usr/bin/sudoedit",
        "/usr/bin/pkexec", "/usr/bin/fusermount",
        "/usr/bin/fusermount3", "/usr/bin/mount", "/usr/bin/umount",
        # 网络工具
        "/usr/bin/ping", "/usr/bin/ping6", "/usr/bin/traceroute",
        "/usr/bin/traceroute6",
        "/usr/bin/ssh-agent", "/usr/bin/crontab",
        # 打印/邮件
        "/usr/bin/wall", "/usr/bin/write", "/usr/bin/write.ul",
        "/usr/bin/at", "/usr/bin/bsd-write",
        # sbin 路径
        "/usr/sbin/pppd", "/usr/sbin/unix_chkpwd",
        "/usr/sbin/mount.nfs",
        # lib 路径
        "/usr/lib/dbus-1.0/dbus-daemon-launch-helper",
        "/usr/lib/openssh/ssh-keysign",
        "/usr/lib/eject/dmcrypt-get-device",
        "/usr/lib/policykit-1/polkit-agent-helper-1",
        "/usr/lib/snapd/snap-confine",
        "/usr/lib/x86_64-linux-gnu/utempter/utempter",
        # snap 路径
        "/snap/core/current/usr/bin/sudo",
        "/snap/snapd/current/usr/lib/snapd/snap-confine",
        # CentOS/RHEL 路径
        "/bin/su", "/bin/mount", "/bin/umount", "/bin/ping",
        "/sbin/unix_chkpwd", "/sbin/pam_timestamp_check",
        "/sbin/mount.nfs",
        # SGID 常见
        "/usr/bin/ssh-agent", "/usr/sbin/postdrop", "/usr/sbin/postqueue",
        "/usr/bin/mlocate", "/usr/bin/locate",
        "/usr/bin/dotlockfile", "/usr/bin/mail-lock", "/usr/bin/mail-unlock",
    }

    # basename 白名单：用于匹配不同路径下的同名标准二进制
    STANDARD_SUID_BASENAMES = {
        "passwd", "chage", "chfn", "chsh", "gpasswd", "newgrp", "expiry",
        "su", "sudo", "sudoedit", "pkexec", "fusermount", "fusermount3",
        "mount", "umount", "ping", "ping6", "traceroute", "traceroute6",
        "ssh-agent", "crontab", "wall", "write", "at",
        "unix_chkpwd", "pam_timestamp_check", "mount.nfs",
        "dbus-daemon-launch-helper", "ssh-keysign",
        "polkit-agent-helper-1", "snap-confine", "utempter",
        "postdrop", "postqueue", "mlocate", "locate",
    }

    result = []
    total_count = 0
    filtered_count = 0

    for line in sub_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 过滤 META/_ExecutionTiming/REPORT_END 调试元数据
        if stripped.startswith("META:") or stripped == "REPORT_END":
            continue
        if stripped.startswith("Step ") and ":" in stripped and "s" in stripped:
            # Step N (SectionName): X.Xs 格式的计时行
            continue
        if stripped.startswith("Total:") or stripped.startswith("OutputFileSize:"):
            continue

        # 保留段标题（后续会清理空段标题）
        if stripped.startswith("==") or stripped.startswith("--"):
            result.append(line)
            continue
        # 保留统计行
        if stripped.startswith("(") or "共" in stripped or "总计" in stripped:
            result.append(line)
            continue

        # 提取文件路径（权限行格式如: -rwsr-xr-x 1 root root 68208 ... /usr/bin/passwd）
        # 或纯路径格式: /usr/bin/passwd
        path = stripped
        if " /" in stripped:
            # ls -la 格式，取最后一个 / 开头的部分
            parts = stripped.split()
            for p in reversed(parts):
                if p.startswith("/"):
                    path = p
                    break

        total_count += 1
        # 优先完整路径匹配，回退 basename 匹配（兼容不同发行版路径）
        basename = path.rsplit("/", 1)[-1] if "/" in path else path
        if path in STANDARD_SUID_FILES or basename in STANDARD_SUID_BASENAMES:
            filtered_count += 1
            continue

        result.append(line)

    if total_count == filtered_count and total_count > 0:
        return None  # 全部为标准系统文件，无需输出

    # 清理空段标题（== SUID 文件 == 后面没有实际文件行时删除）
    cleaned = []
    for i, line in enumerate(result):
        stripped = line.strip()
        if stripped.startswith("=="):
            # 看下一个非空行是否也是段标题或结尾
            next_content = None
            for j in range(i + 1, len(result)):
                if result[j].strip():
                    next_content = result[j].strip()
                    break
            if next_content is None or next_content.startswith("=="):
                continue  # 空段标题，跳过
        cleaned.append(line)
    result = cleaned

    # 在开头插入过滤统计
    if total_count > 0:
        summary = (
            f"SUID/SGID 文件: {total_count} 个"
            f"（标准系统文件 {filtered_count} 个已过滤，"
            f"剩余 {total_count - filtered_count} 个需分析）"
        )
        result.insert(0, summary)

    # 只剩统计行没有实际文件时返回 None
    actual_files = [l for l in result if l.strip()
                    and not l.strip().startswith("SUID/SGID")
                    and not l.strip().startswith("==")
                    and not l.strip().startswith("(")]
    if not actual_files and filtered_count == total_count:
        return None
    if not result:
        return None
    return result


def handler_users(sub_lines: list[str]) -> list[str]:
    """解析 SystemInfo.users（loginable_users + lastlog）。

    输出可登录用户表格，UID=0 后门账户在用户名旁标注 ⚠️。
    数据来源: get_log_all_in_one.sh 中 loginable_users 命令
    (grep -v nologin/false /etc/passwd + lastlog)

    数据格式:
      -- cmd: loginable_users --
      root:x:0:0:root:/root:/bin/bash
      sysadm:x:0:100::/home/sysadm:/bin/bash
      -- cmd: lastlog --
      Username         Port     From             Latest
      root             pts/0    192.168.1.100    Mon Mar 24 09:52:47
    """
    users = []          # [(username, uid, gid, home, shell, tail)]
    uid0_backdoors = [] # 除 root 外 UID=0 的用户名
    lastlog_lines = []
    in_lastlog = False

    for line in sub_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 切换到 lastlog 段
        if "-- cmd: lastlog --" in line:
            in_lastlog = True
            continue
        # 跳过 cmd 标记行
        if "-- cmd:" in line:
            in_lastlog = False
            continue

        if in_lastlog:
            # 跳过 lastlog 表头
            if stripped.startswith("Username"):
                continue
            lastlog_lines.append(stripped)
            continue

        # 解析 passwd 行（正则已放宽，shell 字段后允许任意尾部内容）
        m = RE_PASSWD_LINE.match(stripped)
        if m:
            username = m.group(1)
            uid = int(m.group(3))
            gid = int(m.group(4))
            home = m.group(6)
            shell = m.group(7)
            # 检测 shell 字段之后是否有异常尾部内容（可能是攻击者注入的绕过数据）
            tail = stripped[m.end():].strip()
            users.append((username, uid, gid, home, shell, tail))
            if uid == 0 and username != "root":
                uid0_backdoors.append(username)

    if not users:
        return ["(无可登录用户数据)"]

    result = []
    uid0_count = sum(1 for _, uid, *_ in users if uid == 0)
    result.append(f"可登录用户: {len(users)} 个 (UID=0: {uid0_count} 个)")
    if uid0_backdoors:
        result.append(
            f"⚠️ UID=0 后门账户: {', '.join(uid0_backdoors)}"
        )
    result.append("")

    # 用户表格（UID=0 后门在用户名旁标 ⚠️，尾部异常内容记入备注列）
    # Home 列对入侵分析无价值，省略
    result.append("| 用户名 | UID | GID | Shell | 备注 |")
    result.append("| --- | --- | --- | --- | --- |")
    for username, uid, gid, home, shell, tail in users:
        name_col = f"⚠️ {username}" if uid == 0 and username != "root" else username
        note = f"⚠️ 行尾附加: `{tail}`" if tail else ""
        result.append(f"| {name_col} | {uid} | {gid} | {shell} | {note} |")

    # lastlog 已在 SSH 成功登录章节结构化展示，此处省略

    return result


def handler_shell_history(sub_lines: list[str]) -> list[str] | None:
    """OPT-P03: Shell History 分用户结构化提取。

    按用户分组输出：
    - 高危命令逐条保留（完整原文）
    - 非高危命令去重后只展示唯一命令列表（不重复列出）
    文件不存在时返回 None 跳过（如 zsh_history 在无 zsh 系统上）。
    """
    result = []
    current_user = "unknown"
    user_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "high_risk": 0})
    user_high_cmds: dict[str, list[str]] = defaultdict(list)
    user_normal_cmds: dict[str, set[str]] = defaultdict(set)

    for line in sub_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检测用户切换
        m = RE_HISTORY_USER.search(line)
        if m:
            user = m.group(1) or m.group(2) or "unknown"
            if user != current_user:
                current_user = user

        # 跳过分隔符行
        if stripped.startswith("--------") or stripped.startswith("========"):
            continue
        if stripped.startswith("-- file:"):
            # 从文件路径提取用户名（仅切换上下文，不作为命令记录）
            parts = stripped.split("/")
            for i, p in enumerate(parts):
                if p in ("home", "root") and i + 1 < len(parts):
                    current_user = parts[i + 1] if p == "home" else "root"
                    break
            continue

        # 跳过"未发现"等信息行（不统计为命令）
        if stripped.startswith("(") and ("未发现" in stripped or "无数据" in stripped):
            continue

        # 跳过段标题/标记行
        if stripped.startswith("==") or stripped.startswith("-- cmd:"):
            continue

        # 统计命令
        user_stats[current_user]["total"] += 1
        is_high = any(p in stripped.lower() for p in HISTORY_HIGH_RISK_PATTERNS)
        if is_high:
            user_stats[current_user]["high_risk"] += 1
            user_high_cmds[current_user].append(stripped)
        else:
            user_normal_cmds[current_user].add(stripped)

    # 输出分用户摘要
    if user_stats:
        result.append("**分用户命令统计：**")
        result.append("")
        result.append("| 用户 | 总命令数 | 高危命令数 | 风险 |")
        result.append("| --- | --- | --- | --- |")
        for user, stats in sorted(user_stats.items()):
            risk = "🔴" if stats["high_risk"] > 0 else "🟢"
            result.append(
                f"| {user} | {stats['total']} | {stats['high_risk']} "
                f"| {risk} |"
            )
        result.append("")

    # 分用户输出：高危命令逐条，非高危去重列表
    for user in sorted(set(list(user_high_cmds.keys()) + list(user_normal_cmds.keys()))):
        result.append(f"#### {user}")
        high = user_high_cmds.get(user, [])
        normal = sorted(user_normal_cmds.get(user, set()))

        if high:
            result.append(f"**高危命令 ({len(high)} 条)：**")
            for cmd in high:
                result.append(f"- `{cmd}`")
            result.append("")
        result.append("")

    if not result:
        # 检查是否文件不存在（如 zsh_history）
        has_data = any(l.strip() and not l.strip().startswith("--")
                       and not l.strip().startswith("========")
                       and not l.strip().startswith("--------")
                       for l in sub_lines)
        if not has_data:
            return None
        return ["(无敏感命令历史)"]

    return result


def handler_sudo_commands(sub_lines: list[str]) -> list[str]:
    """SA-R012: 从 AuthLogs.sudo_commands 提取结构化 sudo 命令表格。

    高危命令逐条保留，低风险命令按 (user, command) 归类计数。
    高危判定复用 HISTORY_HIGH_RISK_PATTERNS。
    """
    entries = []
    for line in sub_lines:
        m = RE_SUDO.search(line)
        if m:
            entries.append({
                "time": m.group(1),
                "user": m.group(2),
                "command": m.group(3).strip(),
            })

    if not entries:
        return ["(无 sudo 命令记录)"]

    # 分离高危与低风险
    high_risk = []
    low_risk_counter: dict[tuple[str, str], dict] = {}

    for e in entries:
        cmd_lower = e["command"].lower()
        is_high = any(p in cmd_lower for p in HISTORY_HIGH_RISK_PATTERNS)
        if is_high:
            high_risk.append(e)
        else:
            key = (e["user"], e["command"])
            if key not in low_risk_counter:
                low_risk_counter[key] = {
                    "count": 0,
                    "first": e["time"],
                    "last": e["time"],
                }
            low_risk_counter[key]["count"] += 1
            low_risk_counter[key]["last"] = e["time"]

    result = [
        f"共 {len(entries)} 条 sudo 命令"
        f"（高危 {len(high_risk)} 条，"
        f"低风险归类 {len(low_risk_counter)} 组）",
    ]

    # 高危命令逐条输出
    if high_risk:
        result.append("")
        result.append("**高危 sudo 命令：**")
        result.append("")
        result.append("| 时间 | 用户 | 命令 |")
        result.append("| --- | --- | --- |")
        for e in high_risk:
            result.append(f"| {e['time']} | {e['user']} | `{e['command']}` |")

    # 低风险命令归类计数
    if low_risk_counter:
        result.append("")
        result.append("**低风险 sudo 命令（归类计数）：**")
        result.append("")
        result.append("| 用户 | 命令 | 次数 | 首次 | 最后 |")
        result.append("| --- | --- | --- | --- | --- |")
        for (user, cmd), info in sorted(
            low_risk_counter.items(), key=lambda x: -x[1]["count"]
        ):
            result.append(
                f"| {user} | `{cmd}` | {info['count']} "
                f"| {info['first']} | {info['last']} |"
            )

    return result


def handler_user_management(sub_lines: list[str]) -> list[str]:
    """SA-R012: 从 AuthLogs 的 user_created/user_modified 提取结构化用户管理事件。"""
    events = []
    for line in sub_lines:
        m = RE_USERADD.search(line)
        if m:
            events.append({"time": m.group(1), "action": "创建用户", "detail": m.group(2)})
            continue
        m = RE_USERMOD.search(line)
        if m:
            events.append({"time": m.group(1), "action": "修改用户", "detail": m.group(2).strip()})
            continue
        m = RE_GROUPADD.search(line)
        if m:
            events.append({"time": m.group(1), "action": "创建组", "detail": m.group(2)})
            continue
        m = RE_PASSWD_CHANGE.search(line)
        if m:
            events.append({"time": m.group(1), "action": "密码变更", "detail": m.group(2)})
            continue

    if not events:
        return None

    result = [
        f"共 {len(events)} 条用户管理事件",
        "",
        "| 时间 | 操作 | 详情 |",
        "| --- | --- | --- |",
    ]
    for e in events:
        result.append(f"| {e['time']} | {e['action']} | {e['detail']} |")
    return result


# ---------------------------------------------------------------------------
# SSH 原始日志消除 handler（数据已被 ssh_analysis.py 结构化输出）
# ---------------------------------------------------------------------------


def handler_ssh_already_analyzed(sub_lines: list[str]) -> list[str] | None:
    """消除 SSH 原始日志的重复输出。

    ssh_login_failed / ssh_login_success / ssh_accepted_keys 的数据
    已被 ssh_analysis.py 提取并渲染为独立的结构化章节（暴力破解交叉验证、
    成功登录表格），此处不再重复输出原始 syslog 行。
    """
    return None


# ---------------------------------------------------------------------------
# Network 章节 handler
# ---------------------------------------------------------------------------

# 标准系统监听服务白名单（进程名），在 listening_ports 中过滤
_STANDARD_LISTEN_PROCS = {
    "systemd-resolve", "systemd-network", "chronyd", "sshd",
    "dhclient", "ntpd", "dnsmasq",
} | KNOWN_CLOUD_AGENT_PROCS


def handler_listening_ports(sub_lines: list[str]) -> list[str]:
    """精简 listening_ports：标记标准系统服务，突出可疑监听。"""
    result = []
    suspicious = []
    standard_count = 0
    for line in sub_lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 保留表头
        if stripped.startswith("Netid") or stripped.startswith("Proto"):
            result.append(line)
            continue
        # 检查是否为标准系统服务
        is_standard = any(proc in line for proc in _STANDARD_LISTEN_PROCS)
        if is_standard:
            standard_count += 1
        else:
            suspicious.append(line)
    if suspicious:
        result.extend(suspicious)
    if standard_count > 0:
        result.append(f"(另有 {standard_count} 个标准系统服务监听已省略)")
    if not result:
        result.append("(无监听端口数据)")
    return result


def handler_established_tcp(sub_lines: list[str]) -> list[str] | None:
    """精简 established_tcp：与 reverse_shell_check 的 ESTAB 行重复，直接跳过。"""
    return None


def handler_iptables(sub_lines: list[str]) -> list[str]:
    """精简 iptables：压缩空链，过滤已知云安全链，只保留异常规则。"""
    # 已知云安全 iptables 链名（对入侵分析无价值）
    result = []
    current_chain = ""
    chain_lines: list[str] = []
    has_rules = False
    is_cloud_chain = False
    filtered_chain_count = 0

    def flush_chain():
        nonlocal has_rules, filtered_chain_count
        if current_chain:
            if is_cloud_chain:
                filtered_chain_count += 1
            elif has_rules:
                # 从链的规则中移除指向云安全链的跳转规则
                filtered_lines = []
                for cl in chain_lines:
                    if any(cc in cl for cc in KNOWN_CLOUD_IPTABLES_CHAINS):
                        continue
                    filtered_lines.append(cl)
                # 检查过滤后是否还有实际规则
                actual_rules = [l for l in filtered_lines
                                if l.strip() and not l.strip().startswith(("num", "target", "Chain "))]
                if actual_rules:
                    result.extend(filtered_lines)
            # 空链不输出

    for line in sub_lines:
        stripped = line.strip()
        if stripped.startswith("Chain "):
            flush_chain()
            current_chain = stripped
            chain_lines = [line]
            has_rules = False
            # 检查是否为已知云安全链
            chain_name = stripped.split()[1] if len(stripped.split()) > 1 else ""
            is_cloud_chain = chain_name in KNOWN_CLOUD_IPTABLES_CHAINS
            continue
        if stripped.startswith("== "):
            flush_chain()
            current_chain = ""
            chain_lines = []
            has_rules = False
            is_cloud_chain = False
            result.append(line)
            continue
        if current_chain:
            chain_lines.append(line)
            # 有实际规则行（非表头、非空行）
            if stripped and not stripped.startswith(("num", "target")):
                has_rules = True
        else:
            result.append(line)

    flush_chain()
    if filtered_chain_count > 0:
        result.append(f"(另有 {filtered_chain_count} 个云安全链已省略)")
    if not result:
        result.append("(无 iptables 数据)")
    return result


def handler_dns(sub_lines: list[str]) -> list[str]:
    """精简 dns：去掉注释行，过滤标准公网 DNS，只保留非标准/可疑 nameserver。"""
    result = []
    standard_count = 0
    for line in sub_lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        # 检查是否为标准 DNS
        if stripped.startswith("nameserver"):
            parts = stripped.split()
            if len(parts) >= 2 and parts[1] in STANDARD_DNS_SERVERS:
                standard_count += 1
                continue
        result.append(line)
    if standard_count > 0:
        result.append(f"(另有 {standard_count} 个标准公网 DNS 已省略)")
    if not result:
        result.append("(无 DNS 配置)")
    return result


# ---------------------------------------------------------------------------
# Processes 章节 handler
# ---------------------------------------------------------------------------

# 标准 Linux 内核线程和系统进程白名单（用于过滤 cpu_top15/mem_top15/ppid1）
_KERNEL_THREAD_PATTERNS = [
    "[kthreadd]", "[rcu_", "[ksoftirqd", "[migration",
    "[idle_inject", "[kworker", "[mm_percpu", "[watchdog",
    "[netns]", "[kblockd", "[ata_sff", "[md_", "[edac",
    "[devfreq", "[cpuhp", "[khugepaged", "[kcompactd",
    "[kswapd", "[kdevtmpfs", "[inet_frag", "[writeback",
    "[kintegrityd", "[bioset", "[crypto", "[kstriped",
]

# 标准系统守护进程白名单（共享于 handler_process_top 和 handler_ppid1_processes）
_STANDARD_SYSTEM_PROCS = {
    "systemd-journald", "systemd-udevd", "systemd-networkd",
    "systemd-resolved", "systemd-logind", "systemd-timesyncd",
    "multipathd", "accounts-daemon", "dbus-daemon",
    "NetworkManager", "irqbalance", "networkd-dispatcher",
    "polkitd", "rsyslogd", "udisksd", "ModemManager",
    "wpa_supplicant", "nscd", "dhclient", "chronyd",
    "unattended-upgrade", "fwupd", "upowerd",
    "/sbin/init", "systemd --user",
    # ppid1 特有（PPID=1 的标准服务）
    "cron", "atd", "agetty",
} | KNOWN_CLOUD_AGENT_PROCS


def handler_process_top(sub_lines: list[str]) -> list[str]:
    """精简 cpu_top15 / mem_top15：过滤内核线程和标准系统守护进程。"""
    result = []
    filtered_count = 0
    for line in sub_lines:
        stripped = line.strip()
        # 保留表头
        if stripped.startswith("USER") or stripped.startswith("PID"):
            result.append(line)
            continue
        # 过滤内核线程
        if any(p in line for p in _KERNEL_THREAD_PATTERNS):
            filtered_count += 1
            continue
        # 过滤标准系统守护进程
        if any(proc in line for proc in _STANDARD_SYSTEM_PROCS):
            filtered_count += 1
            continue
        result.append(line)
    if filtered_count > 0:
        result.append(f"(另有 {filtered_count} 个内核线程/标准系统进程已省略)")
    return result


def handler_ppid1_processes(sub_lines: list[str]) -> list[str]:
    """精简 ppid1_processes：只保留非标准系统守护进程。

    PPID=1 的进程大多是 systemd 拉起的标准服务，只保留可疑的。
    """
    return _ppid1_core(sub_lines, set())


def _extract_pids_from_ps(lines: list[str]) -> set[str]:
    """从 ps 输出行中提取 PID 集合（用于跨子章节去重）。"""
    pids: set[str] = set()
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        # ps aux 格式: USER PID %CPU ...  → PID 是第 2 列
        # ps -eo 格式: PID PPID USER ... → PID 是第 1 列
        for p in parts[:3]:
            if p.isdigit():
                pids.add(p)
                break
    return pids


def make_ppid1_handler(cpu_top_output: list[str]):
    """工厂函数：创建能去重 cpu_top15 已输出进程的 ppid1 handler。"""
    seen_pids = _extract_pids_from_ps(cpu_top_output)

    def handler(sub_lines: list[str]) -> list[str]:
        return _ppid1_core(sub_lines, seen_pids)

    return handler


def _ppid1_core(
    sub_lines: list[str], seen_pids: set[str],
) -> list[str]:
    """ppid1_processes 核心逻辑，支持按 PID 去重。"""
    result = []
    filtered_count = 0
    dedup_count = 0
    for line in sub_lines:
        stripped = line.strip()
        # 保留表头
        if stripped.startswith("PID") or stripped.startswith("USER"):
            result.append(line)
            continue
        # 过滤标准系统守护进程
        if any(proc in line for proc in _STANDARD_SYSTEM_PROCS):
            filtered_count += 1
            continue
        # 过滤内核线程
        if any(p in line for p in _KERNEL_THREAD_PATTERNS):
            filtered_count += 1
            continue
        # 按 PID 去重：cpu_top15 已输出的进程在 ppid1 中不重复输出
        # 与 _extract_pids_from_ps 统一逻辑：检查前三个字段中第一个纯数字
        if seen_pids:
            parts = stripped.split()
            pid = None
            for p in parts[:3]:
                if p.isdigit():
                    pid = p
                    break
            if pid and pid in seen_pids:
                dedup_count += 1
                continue
        result.append(line)
    notes = []
    if filtered_count > 0:
        notes.append(f"{filtered_count} 个标准系统守护进程")
    if dedup_count > 0:
        notes.append(f"{dedup_count} 个已在 cpu_top15 输出")
    if notes:
        result.append(f"(另有 {' + '.join(notes)} 已省略)")
    return result


# ---------------------------------------------------------------------------
# Persistence 补充 handler
# ---------------------------------------------------------------------------


def handler_crontab_files(sub_lines: list[str]) -> list[str]:
    """精简 crontab_files：去掉注释/空行，过滤标准系统 cron 条目。"""
    result = []
    standard_cron_count = 0
    for line in sub_lines:
        stripped = line.strip()
        # 跳过注释和空行
        if stripped.startswith("#") or not stripped:
            continue
        # 保留段标题
        if stripped.startswith("==") or stripped.startswith("-- file:"):
            result.append(line)
            continue
        # 过滤标准系统 cron 条目（run-parts /etc/cron.{hourly,daily,weekly,monthly}）
        if "run-parts" in stripped and any(
            d in stripped for d in ("/etc/cron.hourly", "/etc/cron.daily",
                                    "/etc/cron.weekly", "/etc/cron.monthly")
        ):
            standard_cron_count += 1
            continue
        # 过滤标准维护 cron（e2scrub, popularity-contest 等）
        if any(p in stripped for p in ("e2scrub_all", "popularity-contest")):
            standard_cron_count += 1
            continue
        # 过滤重复的环境变量设置
        if stripped.startswith(("SHELL=", "PATH=")):
            continue
        # 保留实际 cron 条目
        result.append(line)
    if standard_cron_count > 0:
        result.append(f"(另有 {standard_cron_count} 个标准系统 cron 条目已省略)")
    if not result:
        result.append("(无 crontab 文件数据)")
    return result


# ---------------------------------------------------------------------------
# SystemInfo 补充 handler
# ---------------------------------------------------------------------------


def handler_os_release(sub_lines: list[str]) -> list[str]:
    """精简 os_release：压缩为一行摘要（PRETTY_NAME + 内核版本）。"""
    pretty_name = ""
    kernel = ""
    for line in sub_lines:
        stripped = line.strip()
        if "PRETTY_NAME=" in stripped:
            pretty_name = stripped.split("=", 1)[1].strip().strip('"')
        if stripped.startswith("Linux ") and "SMP" in stripped:
            # uname -a 输出
            parts = stripped.split()
            if len(parts) >= 3:
                kernel = parts[2]  # 内核版本号
    if pretty_name or kernel:
        return [f"{pretty_name or '?'} (kernel: {kernel or '?'})"]
    # 兜底：返回精简原始内容
    result = []
    seen_pretty_name = False
    for line in sub_lines:
        stripped = line.strip()
        if any(k in stripped for k in ("_URL=", "PRIVACY_POLICY")):
            continue
        if "PRETTY_NAME=" in stripped:
            if seen_pretty_name:
                continue
            seen_pretty_name = True
        result.append(line)
    return result


# ---------------------------------------------------------------------------
# Environment 补充 handler
# ---------------------------------------------------------------------------


def handler_timezone_ntp(sub_lines: list[str]) -> list[str] | None:
    """精简 timezone_ntp：NTP 正常同步时返回 None 跳过。

    仅在以下情况保留输出：
    - NTP 未同步（NTPSynchronized=no / NTP service: inactive）
    - 时区异常（非常见时区）
    - 发现恶意模式
    """
    ntp_synced = False
    ntp_active = False
    for line in sub_lines:
        stripped = line.strip()
        if any(p in line for p in NEVER_SKIP_PATTERNS):
            return sub_lines  # 恶意模式兜底
        if "NTPSynchronized=yes" in stripped:
            ntp_synced = True
        if "NTP service:" in stripped and "active" in stripped:
            ntp_active = True
        if "System clock synchronized:" in stripped and "yes" in stripped:
            ntp_synced = True
    if ntp_synced and ntp_active:
        return None
    # 异常情况保留输出
    return sub_lines


# ---------------------------------------------------------------------------
# SSH 补充 handler
# ---------------------------------------------------------------------------


def handler_sshd_config_check(sub_lines: list[str]) -> list[str]:
    """精简 sshd_config_check：正向提取偏离安全基线的异常项。
    
    只输出 PermitRootLogin yes、PasswordAuthentication yes 等异常配置，
    其余一行摘要。同时保留 sshd_config.d/ 下的自定义 .conf 文件。
    """
    result = []
    config_lines = []
    in_dir_listing = False
    in_custom_conf = False
    total_config_count = 0
    alert_items = []

    # 预计算：是否包含 sshd_config.d 内容（避免循环内 O(n) join）
    has_sshd_config_d = any("sshd_config.d" in l for l in sub_lines)

    for line in sub_lines:
        stripped = line.strip()
        # 跳过目录列表
        if stripped.startswith("total ") and has_sshd_config_d:
            in_dir_listing = True
            continue
        if in_dir_listing:
            if stripped.startswith(("drw", "-rw", "lrw", ".")):
                continue
            if stripped.startswith("---"):
                in_dir_listing = False
                in_custom_conf = True
                result.append(line)
                continue
            in_dir_listing = False

        # 自定义 .conf 文件内容全部保留
        if in_custom_conf:
            result.append(line)
            continue
        
        # 段标题
        if stripped.startswith("==") or stripped.startswith("-- cmd:"):
            continue

        # sshd_config 配置行
        if stripped and not stripped.startswith("#"):
            total_config_count += 1
            # 正向提取异常项
            for key, bad_val in SSHD_CONFIG_ALERT_PATTERNS:
                if stripped.startswith(key) and bad_val in stripped:
                    alert_items.append(f"⚠️ {stripped}")
                    break
            # MaxAuthTries 特殊检查
            if stripped.startswith("MaxAuthTries"):
                parts = stripped.split()
                if len(parts) >= 2:
                    try:
                        val = int(parts[1])
                        if val > SSHD_MAX_AUTH_TRIES_THRESHOLD:
                            alert_items.append(f"⚠️ {stripped} (>阈值{SSHD_MAX_AUTH_TRIES_THRESHOLD})")
                    except ValueError:
                        pass

    if alert_items:
        result = alert_items + result
    if total_config_count > 0:
        safe_count = total_config_count - len(alert_items)
        if safe_count > 0:
            result.append(f"(sshd_config 其余 {safe_count} 项均为标准配置)")
    if not result:
        result.append("(无 sshd_config 数据)")
    return result


# ---------------------------------------------------------------------------
# IOC 汇总提取
# ---------------------------------------------------------------------------


def extract_iocs_from_lines(raw_lines: list[str]) -> dict[str, set[str]]:
    """从原始日志行中提取 IOC（IP 地址 + 域名）。

    扫描全文，提取所有 IPv4 地址和可疑域名。
    返回 {"ips": set[str], "domains": set[str]}。

    内置白名单过滤：
    - IP: 公共 DNS、云元数据等已知良性 IP
    - 域名: 操作系统官方源、知名 CDN 等已知良性域名
    外部 IP 过滤（internal/loopback 等）由调用方根据 classify_ip() 决定。
    """
    ips: set[str] = set()
    domains: set[str] = set()

    for line in raw_lines:
        for m in _RE_IPV4.finditer(line):
            ip = m.group(1)
            if ip not in _BENIGN_IPS:
                ips.add(ip)
        for m in _RE_DOMAIN.finditer(line):
            domain = m.group(1).lower()
            if domain in _FALSE_POSITIVE_DOMAINS:
                continue
            if any(p in domain for p in _FALSE_POSITIVE_DOMAIN_PATTERNS):
                continue
            if not any(domain.endswith(s) for s in _BENIGN_DOMAIN_SUFFIXES):
                domains.add(domain)

    return {"ips": ips, "domains": domains}


# ---------------------------------------------------------------------------
# 持久化向量汇总
# ---------------------------------------------------------------------------


def extract_persistence_vectors(
    lines: list[str],
    sections: "list",
    get_sub_lines_fn: "callable",
) -> list[dict]:
    """从各持久化相关子章节提取可疑持久化向量。

    返回 [{"type": str, "path": str, "detail": str}, ...]

    检测逻辑:
    - crontab: 非注释、非标准系统 cron 的自定义条目
    - crontab_files: /etc/cron.d/ 下的自定义条目
    - systemd_units: 自定义 unit 的 ExecStart 命令
    - init_d: 非 [known] 的自定义脚本
    - shell_profiles: 匹配恶意模式 (NEVER_SKIP_PATTERNS) 的行
    - authorized_keys: 所有 SSH 公钥条目（含来源标注）
    - rc_local: /etc/rc.local 中的可执行命令
    """
    vectors: list[dict] = []

    # --- Crontab ---
    crontab_lines = get_sub_lines_fn(lines, sections, "crontab")
    current_cron_ctx = "crontab"
    in_spool = False
    root_crontab_entries: set[str] = set()
    for line in crontab_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("=="):
            current_cron_ctx = stripped.strip("= ")
            if "/var/spool/cron" in stripped:
                in_spool = True
            else:
                in_spool = False
            continue
        if stripped.startswith("--") or stripped.startswith("--------"):
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("(") and "无数据" in stripped:
            continue
        # 过滤标准系统 cron 条目
        if "run-parts" in stripped and any(
            d in stripped for d in ("/etc/cron.hourly", "/etc/cron.daily",
                                    "/etc/cron.weekly", "/etc/cron.monthly")
        ):
            continue
        # 过滤 crontab 文件头注释性说明
        if stripped.startswith("SHELL=") or stripped.startswith("PATH="):
            continue
        # 有定时规则的行视为自定义 cron 条目
        if re.match(r"^[\d\*/@]", stripped):
            # 去重：root crontab 先收集，spool 中重复的跳过
            if not in_spool:
                root_crontab_entries.add(stripped)
                vectors.append({
                    "type": PERSIST_CRONTAB,
                    "path": current_cron_ctx,
                    "detail": stripped[:120],
                })
            elif stripped not in root_crontab_entries:
                vectors.append({
                    "type": PERSIST_CRONTAB,
                    "path": current_cron_ctx,
                    "detail": stripped[:120],
                })

    # --- Crontab Files (/etc/cron.d/*) ---
    crontab_files_lines = get_sub_lines_fn(lines, sections, "crontab_files")
    current_cron_file = "crontab_files"
    for line in crontab_files_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("==") or stripped.startswith("-- file:"):
            current_cron_file = stripped.strip("= -").strip()
            continue
        if stripped.startswith("#") or stripped.startswith("("):
            continue
        # 过滤标准系统 cron 条目
        if "run-parts" in stripped and any(
            d in stripped for d in ("/etc/cron.hourly", "/etc/cron.daily",
                                    "/etc/cron.weekly", "/etc/cron.monthly")
        ):
            continue
        if any(p in stripped for p in ("e2scrub_all", "popularity-contest")):
            continue
        if stripped.startswith(("SHELL=", "PATH=")):
            continue
        # 有定时规则的行视为自定义 cron 条目
        if re.match(r"^[\d\*/@]", stripped):
            # 跳过已在 root crontab 中收集的重复条目
            if stripped not in root_crontab_entries:
                vectors.append({
                    "type": PERSIST_CRONTAB,
                    "path": current_cron_file,
                    "detail": stripped[:120],
                })

    # --- Systemd Units ---
    systemd_lines = get_sub_lines_fn(lines, sections, "systemd_units")
    in_custom = False
    current_unit = ""
    for line in systemd_lines:
        stripped = line.strip()
        if "自定义 systemd service" in line:
            in_custom = True
            continue
        if not in_custom:
            continue
        # unit 文件名行（支持 "-- file: xxx --" 和 "== xxx ==" 两种格式）
        if stripped.startswith("-- file:"):
            current_unit = stripped.replace("-- file:", "").strip().rstrip(" --")
            continue
        if stripped.startswith("== ") and stripped.endswith(" =="):
            current_unit = stripped.strip("= ")
            continue
        # ExecStart 命令
        if stripped.startswith(("ExecStart=", "ExecStartPre=", "ExecStartPost=")):
            vectors.append({
                "type": PERSIST_SYSTEMD,
                "path": current_unit,
                "detail": stripped[:120],
            })

    # --- Init.d ---
    initd_lines = get_sub_lines_fn(lines, sections, "init_d")
    in_custom_script = False
    current_script = ""
    for line in initd_lines:
        stripped = line.strip()
        # 自定义脚本内容段
        if stripped.startswith("== /etc/init.d/"):
            current_script = stripped.strip("= ")
            in_custom_script = True
            continue
        if stripped.startswith("[known]"):
            in_custom_script = False
            continue
        if in_custom_script and stripped and not stripped.startswith("--------"):
            # 只取首行摘要
            vectors.append({
                "type": PERSIST_INITD,
                "path": current_script,
                "detail": stripped[:120],
            })
            in_custom_script = False  # 只取第一行有效内容

    # --- Shell Profiles ---
    profile_lines = get_sub_lines_fn(lines, sections, "shell_profiles")
    current_file = ""
    for line in profile_lines:
        if line.startswith("-- file:"):
            current_file = line.replace("-- file:", "").strip().rstrip(" --")
            continue
        line_lower = line.lower()
        if any(p in line_lower for p in NEVER_SKIP_PATTERNS):
            # 排除标准 .bashrc 默认行的误报（lesspipe/dircolors 等含 eval）
            if any(fp in line_lower for fp in _PROFILE_FALSE_POSITIVE_PATTERNS):
                continue
            vectors.append({
                "type": PERSIST_PROFILE,
                "path": current_file,
                "detail": line.strip()[:120],
            })

    # --- Authorized Keys ---
    authkey_lines = get_sub_lines_fn(lines, sections, "authorized_keys")
    current_file = ""
    for line in authkey_lines:
        stripped = line.strip()
        if line.startswith("-- file:"):
            current_file = line.replace("-- file:", "").strip().rstrip(" --")
            continue
        if stripped.startswith("permissions:") or stripped.startswith("owner:"):
            continue
        if not stripped or stripped.startswith("--------"):
            continue
        # SSH 公钥行（可能多个公钥拼在同一行，按 ssh- 前缀分割）
        if stripped.startswith(("ssh-rsa", "ssh-ed25519", "ssh-dss", "ecdsa-sha2")):
            # 拆分同一行内的多个公钥
            key_entries = re.split(r"(?=ssh-(?:rsa|ed25519|dss)|ecdsa-sha2)", stripped)
            for entry in key_entries:
                entry = entry.strip()
                if not entry:
                    continue
                parts = entry.split()
                key_type = parts[0] if parts else "unknown"
                # comment 通常是最后一个非标记字段
                comment = parts[2] if len(parts) >= 3 else "(无注释)"
                vectors.append({
                    "type": PERSIST_AUTHKEY,
                    "path": current_file,
                    "detail": f"{key_type} ... {comment}",
                })

    # --- RC.local ---
    rclocal_lines = get_sub_lines_fn(lines, sections, "rc_local")
    rc_local_executable = False  # rc.local 是否可执行
    for line in rclocal_lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 解析 executable 字段
        if stripped.startswith("executable:"):
            val = stripped.split(":", 1)[1].strip().lower()
            rc_local_executable = (val == "yes")
            continue
        # 跳过其他元数据行（stat 输出、文件标记、权限信息等）
        if stripped.startswith(("-- file:", "-- cmd:", "permissions:", "#!/")):
            continue
        # 跳过纯注释行
        if stripped.startswith("#"):
            continue
        # 跳过 exit 语句
        if stripped in ("exit 0", "exit 1"):
            continue
        # 根据 rc.local 可执行性决定向量类型
        if rc_local_executable:
            # 可执行：作为有效的后门向量
            vectors.append({
                "type": PERSIST_RCLOCAL,
                "path": "/etc/rc.local",
                "detail": stripped[:120],
            })
        else:
            # 不可执行：输出告警向量，让 AI 知道内容存在但未生效
            vectors.append({
                "type": PERSIST_RCLOCAL_INACTIVE,
                "path": "/etc/rc.local",
                "detail": f"⚠️ rc.local 不可执行（当前未生效）: {stripped[:100]}",
            })

    return vectors
