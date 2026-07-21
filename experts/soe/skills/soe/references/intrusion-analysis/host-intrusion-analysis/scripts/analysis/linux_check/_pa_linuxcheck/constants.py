"""LinuxCheck.sh 日志预分析常量定义。

包含 LinuxCheck.sh Markdown 格式日志的章节标记、
噪声模式白名单和精简规则。
"""

import re

from _common import cloud_vendor as _cloud_vendor

# ---------------------------------------------------------------------------
# LinuxCheck.sh 日志格式识别
# ---------------------------------------------------------------------------

# LinuxCheck.sh 特征性章节标题（用于 can_handle 检测）
LINUXCHECK_MARKERS = [
    "## 基础配置检查",
    "## 进程信息检查",
    "## 网络/流量检查",
    "## 任务计划检查",
    "## 环境变量检查",
    "## 用户信息检查",
    "## Linux启动项排查",
    "## 服务状态检查",
    "## Rootkit检查",
    "## SSH检查",
    "## Webshell检查",
    "## 挖矿木马检查",
]

# ---------------------------------------------------------------------------
# 空内容检测
# ---------------------------------------------------------------------------

# 空代码块正则：```shell\n\n```（可能有少量空白）
RE_EMPTY_CODE_BLOCK = re.compile(
    r"```shell\s*\n\s*\n```", re.MULTILINE
)

# 单独的空 ```shell``` 或空 ``` ``` 块
RE_EMPTY_CODE_BLOCK_2 = re.compile(
    r"```(?:shell)?\s*\n```", re.MULTILINE
)

# ---------------------------------------------------------------------------
# last 登录历史精简
# ---------------------------------------------------------------------------

# last 输出行正则（匹配 "用户名 终端 IP 时间" 格式）
RE_LAST_LINE = re.compile(
    r"^(\S+)\s+(pts/\d+|tty\d+|system boot)\s+"
    r"(\S+)\s+\w{3}\s+\w{3}\s+\d+"
)

# 保留的最近登录条数上限（从 20 降到 5，归类表格已足够）
LAST_LOGIN_MAX_LINES = 5

# ---------------------------------------------------------------------------
# 标准系统进程白名单（用于 CPU/MEM TOP 过滤）
# ---------------------------------------------------------------------------

STANDARD_SYSTEM_PROCS = {
    "systemd-journald", "systemd-udevd", "systemd-networkd",
    "systemd-resolved", "systemd-logind", "systemd-timesyncd",
    "multipathd", "accounts-daemon", "dbus-daemon",
    "NetworkManager", "irqbalance", "networkd-dispatcher",
    "polkitd", "rsyslogd", "udisksd", "ModemManager",
    "wpa_supplicant", "nscd", "dhclient", "chronyd",
    "unattended-upgrade", "fwupd", "upowerd",
    "/sbin/init", "agetty", "cron", "atd",
}

# 云厂商 Agent 进程名（子字符串匹配）
# 从 ``config/cloud_vendor_processes.json`` 加载，本仓库默认空。
KNOWN_CLOUD_AGENT_PROCS = _cloud_vendor.agent_processes()

# 内核线程模式（子字符串匹配）
KERNEL_THREAD_PATTERNS = [
    "[kthreadd]", "[rcu_", "[ksoftirqd", "[migration",
    "[idle_inject", "[kworker", "[mm_percpu", "[watchdog",
    "[netns]", "[kblockd", "[ata_sff", "[md_", "[edac",
    "[devfreq", "[cpuhp", "[khugepaged", "[kcompactd",
    "[kswapd", "[kdevtmpfs", "[inet_frag", "[writeback",
    "[kintegrityd", "[bioset", "[crypto", "[kstriped",
]

# CPU/MEM TOP 保留的最大行数（只保留 Top N 非标准进程）
PROCESS_TOP_MAX_LINES = 5

# ---------------------------------------------------------------------------
# 标准 SUID/SGID 文件白名单
# ---------------------------------------------------------------------------

STANDARD_SUID_BASENAMES = {
    "passwd", "chage", "chfn", "chsh", "gpasswd", "newgrp", "expiry",
    "su", "sudo", "sudoedit", "pkexec", "fusermount", "fusermount3",
    "mount", "umount", "ping", "ping6", "traceroute", "traceroute6",
    "ssh-agent", "crontab", "wall", "write", "at",
    "unix_chkpwd", "pam_timestamp_check", "mount.nfs",
    "dbus-daemon-launch-helper", "ssh-keysign",
    "polkit-agent-helper-1", "snap-confine", "utempter",
    "postdrop", "postqueue", "mlocate", "locate", "pppd",
}

# ---------------------------------------------------------------------------
# 整节为空/无数据时可跳过的章节
# ---------------------------------------------------------------------------

# 这些章节如果内容为空或仅含空代码块，直接跳过不输出
SKIPPABLE_EMPTY_SECTIONS = {
    "## Webshell检查",
    "## 供应链投毒检测",
}

# ---------------------------------------------------------------------------
# /tmp 目录噪声过滤
# ---------------------------------------------------------------------------

# /tmp 和 /var/tmp 下的标准系统文件前缀（过滤噪声）
TMP_NOISE_PREFIXES = (
    "systemd-private-",
    ".font-unix",
    ".ICE-unix",
    ".XIM-unix",
    ".X11-unix",
    "safe-rm-source-flag-",
    "sandbox-source-flag-",
)

# ---------------------------------------------------------------------------
# 敏感文件噪声过滤
# ---------------------------------------------------------------------------

# 敏感文件检测中的 Python 缓存误报路径
# 通用条目内置；云厂商相关路径走 ``FILE_MTIME_NOISE_PATTERNS``（同样从 yaml 加载）。
SENSITIVE_FILE_NOISE_PATTERNS = [
    "/root/.cache/uv/",
    "site-packages/pip/",
    "site-packages/urllib3/",
    "site-packages/httpcore/",
]

# ---------------------------------------------------------------------------
# 标准系统服务白名单（用于 Service 列表过滤）
# ---------------------------------------------------------------------------

STANDARD_SYSTEM_SERVICES = {
    # systemd 核心
    "init.scope", "systemd-journald.service", "systemd-logind.service",
    "systemd-udevd.service", "systemd-timesyncd.service",
    "systemd-networkd.service", "systemd-resolved.service",
    # 网络
    "NetworkManager.service", "wpa_supplicant.service",
    "networking.service", "ModemManager.service",
    # 基础守护进程
    "dbus.service", "polkit.service", "rsyslog.service",
    "cron.service", "irqbalance.service", "nscd.service",
    "chrony.service", "ssh.service",
    # 终端
    "getty@tty1.service", "serial-getty@ttyS0.service",
    "user@0.service",
    # socket 单元
    "dbus.socket", "systemd-journald.socket",
    "systemd-journald-audit.socket", "systemd-journald-dev-log.socket",
    "systemd-udevd-control.socket", "systemd-udevd-kernel.socket",
    "syslog.socket",
    # automount
    "proc-sys-fs-binfmt_misc.automount",
    # 其他标准
    "console-setup.service", "e2scrub_reap.service",
    "remote-fs.target", "ufw.service",
}

# 云厂商 Agent 服务名（子字符串匹配）
# 从 ``config/cloud_vendor_processes.json`` 加载，本仓库默认空。
KNOWN_CLOUD_AGENT_SERVICES = _cloud_vendor.agent_services()

# ---------------------------------------------------------------------------
# History 敏感操作噪声过滤
# ---------------------------------------------------------------------------

# History 中混入的脚本源码特征行（不是用户命令而是 curl | bash 的副产物）
# 匹配策略：行首为函数定义、变量赋值（函数体内）、注释等
HISTORY_SCRIPT_NOISE_PATTERNS = [
    # bash 函数定义体
    "nvm_echo", "nvm_grep", "nvm_default_install_dir", "nvm_install_dir",
    "nvm_latest_version", "nvm_profile_is_bash_or_zsh", "nvm_source",
    "nvm_install_node", "nvm_check_global_modules", "nvm_reset",
    "nvm_try_profile", "nvm_download", "install_nvm_as_script",
    "COMPLETION_STR=", "BASH_OR_ZSH=", "SOURCE_STR=",
    "DETECTED_PROFILE=", "NVM_GITHUB_REPO=",
    # nodesource 安装脚本
    "configure_repo()", "handle_error", "dpkg --print-architecture",
    "URIs: https://deb.nodesource.com",
    # openclaw 安装脚本
    "detect_downloader", "run_remote_bash", "bootstrap_gum_temp",
    "detect_os_or_die", "show_footer_links", "run_quiet_step",
    "run_npm_global_install", "TAGLINES+=",
    "GUM_STATUS=", "GUM_REASON=", "GUM=",
    "NPM_LOGLEVEL", "NPM_SILENT_FLAG", "SHARP_IGNORE_GLOBAL_LIBVIPS",
    "LAST_NPM_INSTALL_CMD",
    # 通用脚本体特征
    "  local ", "  if [", "  fi;", "  else", "  done;",
    "  return", "  fi\n", "  fi ",
]

# History 行中有安全价值的关键词（这些行即使含脚本特征也要保留）
HISTORY_SECURITY_KEYWORDS = [
    "ssh-", "authorized_keys", "chmod 600", "chmod 700",
    "password", "passwd", "secret", "token", "sk-",
    "attack", "exploit", "reverse", "nohup ssh -R",
    "curl -X POST", "/etc/shadow", "iptables",
    "nc ", "ncat ", "netcat",
]

# History 保留的最大行数（安全关键行除外）
HISTORY_MAX_LINES = 15

# ---------------------------------------------------------------------------
# 网络连接噪声过滤
# ---------------------------------------------------------------------------

# localhost/回环地址（netstat 输出中的噪声连接）
LOCALHOST_PATTERNS = (
    "127.0.0.1", "::1", "0.0.0.0:*", ":::*",
)

# ---------------------------------------------------------------------------
# /etc/init.d 标准系统脚本白名单
# ---------------------------------------------------------------------------

STANDARD_INITD_SCRIPTS = {
    "udev", "ssh", "dbus", "console-setup.sh", "ufw", "chrony",
    "apparmor", "hwclock.sh", "networking", "procps", "kmod",
    "kexec-load", "kexec", "screen-cleanup", "keyboard-setup.sh",
    "cron", "irqbalance", "x11-common", "sudo", "nscd",
    "docker", "containerd", "nginx",
}

# 云厂商 init.d 脚本（子字符串匹配）
# 从 ``config/cloud_vendor_processes.json`` 的 initd_scripts 字段加载，本仓库默认空。
CLOUD_INITD_PATTERNS = tuple(_cloud_vendor.initd_scripts())

# ---------------------------------------------------------------------------
# 文件检查精简
# ---------------------------------------------------------------------------

# mtime/ctime 中的噪声路径（子字符串匹配）
# 通用条目内置；云厂商相关路径从 ``config/cloud_vendor_processes.json`` 的
# ``file_path_noise`` 字段加载，本仓库默认空。
FILE_MTIME_NOISE_PATTERNS = (
    "_log.md",      # 采集日志自身
    ".npm/",
) + _cloud_vendor.file_path_noise()

# ---------------------------------------------------------------------------
# SSH authorized_keys 精简
# ---------------------------------------------------------------------------

# 公钥截断长度（只保留类型 + 前N字符 + 用户注释）
SSH_KEY_DISPLAY_PREFIX_LEN = 16

# ---------------------------------------------------------------------------
# 整节删除的子章节标题（对入侵分析无额外价值、与其他章节重复）
# ---------------------------------------------------------------------------

SECTIONS_TO_REMOVE = {
    "网络流量",           # 原始字节计数对入侵分析无价值
    "对外开放端口",       # 与"端口监听"完全重复
    "父进程为1的进程信息",  # 与 running services + 端口监听重复
    "近七天文件改动 ctime",  # 与 mtime 高度重叠
    "/etc/init.d 黑特征",   # 标准 start-stop-daemon 不是黑特征
    "路由表",            # 标准路由对入侵分析无价值
    "ARP",              # ARP 表对入侵分析无价值
    "路由转发",          # 单行信息，可从基础配置获取
    "DNS Server",       # DNS 配置对入侵分析价值极低
    "网卡混杂模式",       # 通常为空或无问题
    "TCP连接状态",       # 统计数字对入侵分析无价值
    "/etc/profile",     # 标准系统默认配置
    ".profile",         # 标准系统默认配置
    "History文件",       # 文件大小信息无分析价值
    "最近添加的Service",  # 与 running services 重复
    "ifconfig",         # 基础配置检查已有 IPADDR
    "硬盘挂载",          # 存储挂载对入侵分析无价值
    "/etc/hosts",       # 标准 hosts 对入侵分析价值低
    "剩余空间",          # 磁盘空间对入侵分析无价值
    "IPTABLES防火墙",    # 云厂商安全组规则太长且非手动配置
}
