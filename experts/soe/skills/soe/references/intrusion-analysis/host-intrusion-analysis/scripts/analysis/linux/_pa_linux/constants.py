"""Linux 预分析常量定义。

包含持久化类型常量、SSH syslog 正则、shell 配置文件标记、恶意模式白名单、
用户管理正则、Shell History 相关常量、sshd_config 安全基线、
标准 DNS 白名单、标准 sudoers 白名单。
"""

import re

# ---------------------------------------------------------------------------
# 持久化类型常量（threat_score.py 和 handlers.py 共用）
# ---------------------------------------------------------------------------
PERSIST_CRONTAB = "Crontab"
PERSIST_SYSTEMD = "Systemd Service"
PERSIST_INITD = "Init.d Script"
PERSIST_PROFILE = "Shell Profile"
PERSIST_AUTHKEY = "SSH Authorized Key"
PERSIST_RCLOCAL = "RC.local"
PERSIST_RCLOCAL_INACTIVE = "RC.local(不可执行)"

# ---------------------------------------------------------------------------
# SSH Syslog 正则
# ---------------------------------------------------------------------------

# syslog 行中 SSH 失败登录的正则
# 格式 1 (Disconnecting): "sshd[PID]: Disconnecting authenticating user root 192.168.1.101 port 59720: Too many..."
# 格式 2 (Disconnecting, 无 PID): "sshd: Disconnecting invalid user admin 192.168.1.101 port 59720: Too many..."
RE_SSH_FAIL_DISCONNECT = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sshd(?:\[\d+\])?:\s+"
    r"Disconnecting\s+(?:authenticating|invalid)\s+user\s+(\S+)\s+(\S+)\s+port\s+\d+"
)

# SA-R008: SSH 失败登录 (Failed password 格式)
# 格式: "sshd[PID]: Failed password for root from 192.168.100.200 port 52413 ssh2"
#     或: "sshd: Failed password for invalid user admin from 10.0.0.99 port 48201 ssh2"
RE_SSH_FAIL_PASSWORD = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sshd(?:\[\d+\])?:\s+"
    r"Failed\s+password\s+for\s+(?:invalid\s+user\s+)?(\S+)\s+from\s+(\S+)\s+port\s+\d+"
)

# SSH 成功登录（兼容有/无 PID 格式）
# 格式 1: "sshd[PID]: Accepted publickey for root from 192.168.1.102 port 9276 ssh2"
# 格式 2: "sshd: Accepted password for root from 192.168.1.103 port 52413 ssh2"
RE_SSH_SUCCESS = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sshd(?:\[\d+\])?:\s+"
    r"Accepted\s+(\S+)\s+for\s+(\S+)\s+from\s+(\S+)\s+port\s+(\d+)"
)

# SA-R003: SSH 协议异常检测正则
# 当攻击者通过 SSH 端口发送 HTTP 请求（如路径遍历探测 GET /..%2F..%2Fetc%2Fpasswd）时，
# sshd 会记录 kex_exchange_identification 或 Bad protocol version 错误。
# 这些日志是 HTTP 路径遍历探测的关键信号。

# 格式: "sshd[PID]: error: kex_exchange_identification: banner line contains invalid characters"
#     或: "sshd: error: kex_exchange_identification: ... from 192.168.1.100 port 12345"
RE_SSH_KEX_ERROR = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sshd(?:\[\d+\])?:\s+"
    r"error:\s+kex_exchange_identification:(.+)"
)

# 格式: "sshd[PID]: Bad protocol version identification '...' from 192.168.1.100 port 12345"
RE_SSH_BAD_PROTOCOL = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sshd(?:\[\d+\])?:\s+"
    r"Bad protocol version identification\s+'([^']*)'\s+from\s+(\S+)\s+port\s+(\d+)"
)

# 通用 IP 提取（用于从 kex_exchange_identification 等消息中提取源 IP）
_RE_FROM_IP = re.compile(r"from\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")

# ---------------------------------------------------------------------------
# Shell Profile 精简常量
# ---------------------------------------------------------------------------

# 已知标准 shell 配置文件内容特征（用于过滤默认 .bashrc 等）
STANDARD_PROFILE_MARKERS = [
    "# ~/.bashrc:",
    "# ~/.profile:",
    "# /etc/profile:",
    "# System-wide .bashrc",
    "# enable programmable completion",
    "# enable color support",
    "# set a fancy prompt",
    "# If not running interactively",
    "# some more ls aliases",
    "# Alias definitions",
    "# sudo hint",
    "# if the command-not-found package",
    "mesg n",
]

# SA-R009: 恶意模式白名单——即使在标准配置文件区域内，包含这些模式的行永不省略
NEVER_SKIP_PATTERNS = [
    "curl ",
    "wget ",
    "/dev/tcp",
    "/dev/udp",
    "bash -c",
    "| bash",
    "|bash",
    "python -c",
    "python3 -c",
    "perl -e",
    "nc ",
    "ncat ",
    "socat ",
    "base64",
    "eval ",
    "/tmp/",
    "crontab",
    "chmod +x",
    "nohup ",
]

# ---------------------------------------------------------------------------
# /etc/passwd 解析正则
# ---------------------------------------------------------------------------

# passwd 行格式: user:x:UID:GID:comment:home:shell[尾部可能有任意附加内容]
# 安全设计：shell 字段后不要求行尾终止（去掉 $），允许尾部有任意内容。
# 攻击者可能在行尾注入垃圾数据试图绕过正则匹配导致账户被静默丢弃，
# 放宽匹配后所有 passwd 格式的行都会被解析，由大模型最终判断。
RE_PASSWD_LINE = re.compile(
    r"^([^:]+):([^:]*):(\d+):(\d+):([^:]*):(\/[^:]*):(\S+)"
)

# ---------------------------------------------------------------------------
# AuthLogs 正则
# ---------------------------------------------------------------------------

# SA-R012: sudo 命令提取正则
RE_SUDO = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+sudo(?:\[\d+\])?:\s+"
    r"(\S+)\s+:\s+.*?COMMAND=(.*)"
)

# SA-R012: 用户创建/修改正则
RE_USERADD = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+useradd(?:\[\d+\])?:\s+new user:\s+name=([^,\s]+)"
)
RE_USERMOD = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+usermod(?:\[\d+\])?:\s+(.+)"
)
RE_GROUPADD = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+groupadd(?:\[\d+\])?:\s+new group:\s+name=([^,\s]+)"
)
RE_PASSWD_CHANGE = re.compile(
    r"(\w+\s+\d+\s+[\d:]+)\s+\S+\s+(?:passwd|chage)(?:\[\d+\])?:\s+.*?(\S+)$"
)

# ---------------------------------------------------------------------------
# Shell History 常量
# ---------------------------------------------------------------------------

# OPT-P03: Shell History 用户分组正则
RE_HISTORY_USER = re.compile(r"^==\s*user:\s*(\S+)\s*==|^--\s*file:\s*/(?:home|root)/([^/]+)/")

# OPT-P03: Shell History 高危命令模式
HISTORY_HIGH_RISK_PATTERNS = [
    "curl ", "wget ", "/dev/tcp", "/dev/udp", "nc -", "ncat ",
    "python3 -c", "python -c", "perl -e", "base64",
    "chmod +s", "chmod +x", "chown root",
    "/etc/shadow", "/etc/passwd", "/etc/sudoers",
    "sudo su", "sudo -i", "sudo /bin/bash",
    "nmap ", "masscan ",
    "scp ", "rsync ",
    "rootkit", "backdoor", "miner",
    "iptables -", "crontab -",
    "eval ", "| bash", "|bash",
]


# ---------------------------------------------------------------------------
# sshd_config 安全基线（正向提取异常项策略）
# ---------------------------------------------------------------------------

# 偏离基线需告警的 sshd_config 异常项（正向匹配，找到就输出）
SSHD_CONFIG_ALERT_PATTERNS = [
    ("PermitRootLogin", "yes"),
    ("PermitEmptyPasswords", "yes"),
    ("PasswordAuthentication", "yes"),
    ("GatewayPorts", "yes"),
]

# MaxAuthTries 异常阈值（>6 视为异常）
SSHD_MAX_AUTH_TRIES_THRESHOLD = 6

# ---------------------------------------------------------------------------
# 标准 DNS 服务器白名单（条件输出时过滤标准公网 DNS）
# ---------------------------------------------------------------------------

STANDARD_DNS_SERVERS = {
    "8.8.8.8", "8.8.4.4",           # Google DNS
    "1.1.1.1", "1.0.0.1",           # Cloudflare DNS
    "9.9.9.9",                       # Quad9 DNS
    "114.114.114.114",               # 国内公共 DNS
    "119.29.29.29",                  # DNSPod
    "223.5.5.5", "223.6.6.6",       # 阿里 DNS
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "127.0.0.53",                    # systemd-resolved 本地 DNS 缓存
}

# ---------------------------------------------------------------------------
# sudoers 标准行白名单（默认配置不输出，只保留自定义规则）
# ---------------------------------------------------------------------------

STANDARD_SUDOERS_LINES = {
    "root\tALL=(ALL:ALL) ALL",
    "root    ALL=(ALL:ALL) ALL",
    "root ALL=(ALL:ALL) ALL",
    "%admin ALL=(ALL) ALL",
    "%admin\tALL=(ALL) ALL",
    "%sudo\tALL=(ALL:ALL) ALL",
    "%sudo   ALL=(ALL:ALL) ALL",
    "%sudo ALL=(ALL:ALL) ALL",
}

# 标准 sudoers 注释/指令前缀（过滤）
STANDARD_SUDOERS_PREFIXES = (
    "#", "Defaults", "@includedir", "includedir",
)

# ---------------------------------------------------------------------------
# 云厂商 Agent 统一白名单
# ---------------------------------------------------------------------------
# 云厂商 agent 标识（进程名、iptables 链等）从 ``config/cloud_vendor_processes.json``
# 外部配置加载——本仓库默认配置为空。请参见该文件同目录的 README.md，按部署所在
# 的云平台填入对应标识；handlers.py 中各处自动生效，无需改代码。

from _common import cloud_vendor as _cloud_vendor

# 云 Agent 进程名（子字符串匹配，用于 ESTABLISHED 连接、监听端口、PPID=1 进程过滤）
KNOWN_CLOUD_AGENT_PROCS = _cloud_vendor.agent_processes()

# 云安全 iptables 链名（用于过滤已知云安全防火墙规则）
# Docker 默认链与云厂商无关，保留为内置；其余从配置加载。
KNOWN_CLOUD_IPTABLES_CHAINS = {
    # Docker 默认链
    "DOCKER", "DOCKER-ISOLATION", "DOCKER-USER",
} | _cloud_vendor.iptables_chains()
