#!/bin/bash
# ============================================================
# get_log_all_in_one.sh — Linux 安全应急响应日志采集工具
# ============================================================
#
# 用途: 一键采集 Linux 服务器上的安全相关日志和系统状态，
#       输出为单个标准化文本文件，供 AI 自动化分析。
#
# 错误处理策略:
#   仅使用 set -u（防止变量拼写错误）
#   不使用 set -e 和 set -o pipefail（与"容错不中断"原则冲突）
#   所有命令通过 run_cmd 封装，内部捕获错误
#
# 兼容性: Debian/Ubuntu, CentOS/RHEL/Rocky/Alma/Fedora
# 依赖: bash + coreutils + 系统自带工具（零安装）
# ============================================================

set -u

# ============================================================
# 常量
# ============================================================
readonly SCRIPT_VERSION="1.2.0"
readonly DEFAULT_DAYS_BACK=7
readonly DEFAULT_MAX_LINES=2000
readonly DEFAULT_MAX_FILE_SIZE_MB=50
readonly DEFAULT_CMD_TIMEOUT=30

# 关键命令列表（用于 env_integrity 采集）
readonly KEY_CMDS=(ps ss netstat ls cat grep awk find bash sshd)

# init.d 已知默认脚本白名单
# ---------------------------------------------------------
# 作用: collect_persistence 遍历 /etc/init.d 时，白名单内的脚本仅输出
#       一行摘要（脚本名 + 文件类型），不再 head -20；白名单外的脚本
#       才输出前 20 行内容，聚焦真正可疑的自定义脚本。
#
# 维护: 按字母序排列；Debian 系 + RHEL 系共用同一白名单。
#       新增系统默认脚本时在对应位置插入即可。
# ---------------------------------------------------------
readonly KNOWN_INIT_SCRIPTS=(
    # 基础系统 / 引导
    README skeleton rc rcS single reboot halt killprocs sendsigs
    bootlogs bootmisc.sh checkfs.sh checkroot.sh checkroot-bootclean.sh
    hwclock.sh mountall.sh mountall-bootclean.sh mountdevsubfs.sh
    mountkernfs.sh mountnfs.sh mountnfs-bootclean.sh
    umountfs umountroot umountnfs.sh urandom hostname.sh
    # 网络
    networking network NetworkManager NetworkManager-wait-online
    network-manager network-functions ifupdown ifupdown-clean
    # 设备 / 内核模块
    udev udev-finish kmod console-setup console-setup.sh keyboard-setup.sh
    # 日志
    rsyslog syslog syslog-ng
    # 定时任务
    cron atd anacron
    # D-Bus / 消息总线
    dbus
    # 进程管理
    procps
    # 安全
    apparmor apport ufw iptables ip6tables firewalld ebtables
    selinux fail2ban
    # SSH / 远程
    ssh sshd
    # 系统服务
    acpid alsa-utils avahi-daemon bluetooth cgroupfs-mount chrony
    cpufrequtils cups cups-browsed cryptdisks cryptdisks-early
    dmesg gdm3 grub-common
    irqbalance iscsid lvm2 lvm2-lvmpolld mdadm mdadm-waitinotify
    multipath-tools nscd ntp ntpd open-iscsi open-vm-tools
    plymouth plymouth-log pppd-dns postfix resolvconf rsync
    screen-cleanup smartmontools sudo
    systemd-timesyncd thermald unattended-upgrades uuidd x11-common
    # RHEL / CentOS 特有
    auditd crond functions iptables ipset kdump lvmetad lvm2-lvmetad
    messagebus microcode_ctl nfs nfs-common nfslock portmap portreserve
    rhnsd rpcbind rpcgssd rpcidmapd rpcsvcgssd saslauthd snmpd
    sysstat tuned yum-updatesd
)

# ============================================================
# 全局变量
# ============================================================
DAYS_BACK=$DEFAULT_DAYS_BACK
MAX_LINES=$DEFAULT_MAX_LINES
MAX_FILE_SIZE_MB=$DEFAULT_MAX_FILE_SIZE_MB
CMD_TIMEOUT=$DEFAULT_CMD_TIMEOUT
OUTPUT_DIR=""
STEP_CHOICE=0           # 0 = 全部
OUTPUT_FILE=""
DISTRO=""               # ubuntu, centos, rhel, debian, etc.
DISTRO_FAMILY=""        # debian, rhel, unknown
AUTH_LOG_PATH=""         # 自动检测: /var/log/auth.log 或 /var/log/secure
STEP_TIMINGS=()         # 每步耗时记录
FILE_SIZE_EXCEEDED=0    # 文件大小超限标志
SCRIPT_START_NS=0       # 脚本开始时间（纳秒）

# ============================================================
# 工具函数
# ============================================================

# 输出进度信息到 stderr（不混入输出文件）
log_info() {
    echo "[INFO] $*" >&2
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

# --- check_root: 非 root 则报错退出 ---
check_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行。请使用: sudo bash $0"
        exit 1
    fi
}

# --- detect_distro: 检测发行版，设置 DISTRO/DISTRO_FAMILY/AUTH_LOG_PATH ---
detect_distro() {
    DISTRO="unknown"
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        DISTRO=$(echo "${ID:-unknown}" | tr '[:upper:]' '[:lower:]')
    fi

    case "$DISTRO" in
        ubuntu|debian|kali)
            DISTRO_FAMILY="debian"
            ;;
        centos|rhel|rocky|alma|fedora|oracle)
            DISTRO_FAMILY="rhel"
            ;;
        *)
            DISTRO_FAMILY="unknown"
            ;;
    esac

    # 认证日志路径自动检测
    if [[ -f /var/log/auth.log ]]; then
        AUTH_LOG_PATH="/var/log/auth.log"
    elif [[ -f /var/log/secure ]]; then
        AUTH_LOG_PATH="/var/log/secure"
    else
        AUTH_LOG_PATH=""  # fallback 到 journalctl
    fi

    log_info "发行版: $DISTRO (family: $DISTRO_FAMILY)"
    log_info "认证日志: ${AUTH_LOG_PATH:-journalctl fallback}"
}

# --- parse_args: 解析命令行参数 ---
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --days-back)
                DAYS_BACK="${2:?'--days-back 需要一个数值参数'}"
                shift 2
                ;;
            --max-lines)
                MAX_LINES="${2:?'--max-lines 需要一个数值参数'}"
                shift 2
                ;;
            --max-file-size)
                MAX_FILE_SIZE_MB="${2:?'--max-file-size 需要一个数值参数（MB）'}"
                shift 2
                ;;
            --cmd-timeout)
                CMD_TIMEOUT="${2:?'--cmd-timeout 需要一个数值参数（秒）'}"
                shift 2
                ;;
            --output-dir)
                OUTPUT_DIR="${2:?'--output-dir 需要一个目录路径'}"
                shift 2
                ;;
            --step)
                STEP_CHOICE="${2:?'--step 需要一个步骤编号（1-9）'}"
                if [[ "$STEP_CHOICE" -lt 1 || "$STEP_CHOICE" -gt 9 ]]; then
                    log_error "--step 参数必须在 1-9 之间"
                    exit 1
                fi
                shift 2
                ;;
            --version)
                echo "get_log_all_in_one.sh v${SCRIPT_VERSION}"
                exit 0
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# --- show_help: 显示帮助信息 ---
show_help() {
    cat >&2 <<EOF
用法: sudo bash get_log_all_in_one.sh [选项]

Linux 安全应急响应日志采集工具 v${SCRIPT_VERSION}

选项:
  --days-back N        采集最近 N 天的日志（默认: $DEFAULT_DAYS_BACK）
  --max-lines N        每个子段最大输出行数（默认: $DEFAULT_MAX_LINES）
  --max-file-size N    输出文件最大大小，单位 MB（默认: $DEFAULT_MAX_FILE_SIZE_MB）
  --cmd-timeout N      单个命令超时时间，单位秒（默认: $DEFAULT_CMD_TIMEOUT）
  --output-dir DIR     输出文件存放目录（默认: 脚本所在目录）
  --step N             只执行指定步骤（1-9），默认执行全部
  --version            显示版本信息
  --help               显示帮助信息

步骤编号:
  1  SystemInfo     系统基本信息
  2  AuthLogs       认证日志
  3  Processes      进程信息
  4  Network        网络信息
  5  Persistence    持久化机制
  6  SSH            SSH 安全
  7  ShellHistory   命令历史
  8  Environment    环境信息（环境变量/内核模块/时区NTP）
  9  FileIntegrity  文件完整性校验（rpm -Va / debsums）
EOF
}

# --- get_primary_ip: 获取主 IP 地址 ---
get_primary_ip() {
    local ip=""

    # 优先：ip 命令获取全局 scope 地址（过滤虚拟网卡）
    if command -v ip &>/dev/null; then
        ip=$(ip -4 addr show scope global 2>/dev/null \
            | grep -v -E '(docker|veth|br-)' \
            | grep inet \
            | head -1 \
            | awk '{print $2}' \
            | cut -d/ -f1)
    fi

    # 备选：hostname -I
    if [[ -z "$ip" ]]; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # 最终兜底
    echo "${ip:-unknown}"
}

# --- init_output_file: 生成文件名，写入 REPORT_BEGIN ---
init_output_file() {
    local ip hostname_str current_user timestamp

    ip=$(get_primary_ip)
    hostname_str=$(hostname 2>/dev/null || echo "unknown")
    current_user=$(whoami 2>/dev/null || echo "unknown")
    timestamp=$(date "+%Y%m%d_%H%M%S")

    # 清理文件名中的特殊字符
    ip=$(echo "$ip" | tr -c '[:alnum:]._-' '_')
    hostname_str=$(echo "$hostname_str" | tr -c '[:alnum:]._-' '_')
    current_user=$(echo "$current_user" | tr -c '[:alnum:]._-' '_')

    # 确定输出目录
    if [[ -z "$OUTPUT_DIR" ]]; then
        OUTPUT_DIR="$(cd "$(dirname "$0")" && pwd)"
    fi
    mkdir -p "$OUTPUT_DIR" 2>/dev/null || true

    OUTPUT_FILE="${OUTPUT_DIR}/log_${ip}_${hostname_str}_${current_user}_${timestamp}.txt"

    # 写入报告开始标记
    echo "REPORT_BEGIN" > "$OUTPUT_FILE"

    log_info "输出文件: $OUTPUT_FILE"
}

# --- check_disk_space: 检查输出目录可用空间 ---
check_disk_space() {
    local avail_kb
    avail_kb=$(df -k "$OUTPUT_DIR" 2>/dev/null | awk 'NR==2{print $4}')

    if [[ -n "$avail_kb" ]]; then
        local avail_mb=$((avail_kb / 1024))
        if [[ $avail_mb -lt 100 ]]; then
            log_warn "输出目录可用空间仅 ${avail_mb}MB（< 100MB），采集可能不完整！"
        fi
    fi
}

# --- check_file_size: 检查当前输出文件大小是否超限 ---
check_file_size() {
    if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
        return 0
    fi

    local file_size_bytes
    file_size_bytes=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || echo "0")
    local max_bytes=$((MAX_FILE_SIZE_MB * 1024 * 1024))

    if [[ "$file_size_bytes" -ge "$max_bytes" ]]; then
        FILE_SIZE_EXCEEDED=1
        log_warn "输出文件已达 ${MAX_FILE_SIZE_MB}MB 上限，后续采集将跳过"
    fi
}

# --- 分隔符写入函数 ---
#
# 防御性设计: 每个分隔符写入前先输出一个空行（printf '\n'），
# 确保即使前一个命令的输出末尾缺少换行符（如 authorized_keys），
# 分隔符也不会与内容粘连在同一行，导致解析器无法识别段边界。
#
#   正常情况:
#     ssh-rsa AAAAB3... user@host\n
#     -------- SUB: pam_check --------
#
#   缺少尾部换行时（无防御）:
#     ssh-rsa AAAAB3... user@host  -------- SUB: pam_check --------
#                                  ^^^^^^^^^ 粘连！解析器无法识别
#
#   缺少尾部换行时（有防御）:
#     ssh-rsa AAAAB3... user@host
#                                    <-- printf '\n' 强制的换行
#     -------- SUB: pam_check --------

write_section() {
    printf '\n' >> "$OUTPUT_FILE"
    echo "======== SECTION: $1 ========" >> "$OUTPUT_FILE"
}

write_sub() {
    printf '\n' >> "$OUTPUT_FILE"
    echo "  -------- SUB: $1 --------" >> "$OUTPUT_FILE"
}

write_category() {
    printf '\n' >> "$OUTPUT_FILE"
    echo "  -------- CATEGORY: $1 --------" >> "$OUTPUT_FILE"
}

write_events() {
    printf '\n' >> "$OUTPUT_FILE"
    echo "    -------- EVENTS: $1 --------" >> "$OUTPUT_FILE"
}

# --- run_cmd: 统一命令执行封装 ---
#
# 用法:
#   run_cmd "描述" "命令字符串" [max_lines] [timeout_sec]
#
# 行为:
#   1. 检查文件大小是否已超限 → 超限则跳过并标注
#   2. 用 timeout 包裹命令执行
#   3. exit_code=124 → 超时
#   4. exit_code!=0 → 失败
#   5. 空输出 → 写 (无数据)
#   6. 超行数 → 截断并标注
#   7. 永远返回 0
run_cmd() {
    local desc="$1"
    local cmd="$2"
    local max_lines="${3:-0}"
    local timeout_sec="${4:-$CMD_TIMEOUT}"

    # 文件大小检查
    if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
        echo "(已跳过: 输出文件大小已超过 ${MAX_FILE_SIZE_MB}MB 上限)" >> "$OUTPUT_FILE"
        return 0
    fi

    # 使用 timeout 执行命令
    local output=""
    local exit_code=0
    output=$(timeout "$timeout_sec" bash -c "$cmd" 2>&1) || exit_code=$?

    if [[ $exit_code -eq 124 ]]; then
        echo "(命令超时: $desc, timeout=${timeout_sec}s)" >> "$OUTPUT_FILE"
    elif [[ $exit_code -eq 127 ]]; then
        echo "(命令不可用: $desc)" >> "$OUTPUT_FILE"
    elif [[ $exit_code -ne 0 ]]; then
        echo "(命令执行失败: $desc, exit_code=$exit_code)" >> "$OUTPUT_FILE"
    elif [[ -z "$output" ]]; then
        echo "(无数据)" >> "$OUTPUT_FILE"
    else
        if [[ $max_lines -gt 0 ]]; then
            local total_lines
            total_lines=$(echo "$output" | wc -l)
            if [[ $total_lines -gt $max_lines ]]; then
                echo "$output" | head -n "$max_lines" >> "$OUTPUT_FILE"
                echo "... (truncated, showing $max_lines of $total_lines total lines)" >> "$OUTPUT_FILE"
            else
                echo "$output" >> "$OUTPUT_FILE"
            fi
        else
            echo "$output" >> "$OUTPUT_FILE"
        fi
    fi

    # 每次写入后检查文件大小
    check_file_size

    return 0
}

# --- run_cmd_raw: 直接追加内容到输出文件（不经过命令执行，用于自定义逻辑） ---
write_raw() {
    if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
        echo "(已跳过: 输出文件大小已超过 ${MAX_FILE_SIZE_MB}MB 上限)" >> "$OUTPUT_FILE"
        return 0
    fi
    echo "$1" >> "$OUTPUT_FILE"
    check_file_size
    return 0
}

# --- write_meta: 写 META 段 ---
write_meta() {
    local ip hostname_str current_user os_pretty kernel_ver arch_str
    local collection_ts

    ip=$(get_primary_ip)
    hostname_str=$(hostname 2>/dev/null || echo "unknown")
    current_user=$(whoami 2>/dev/null || echo "unknown")
    kernel_ver=$(uname -r 2>/dev/null || echo "unknown")
    arch_str=$(uname -m 2>/dev/null || echo "unknown")
    collection_ts=$(date "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "unknown")

    # 获取 OS 美化名称
    os_pretty="unknown"
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        os_pretty=$(. /etc/os-release && echo "${PRETTY_NAME:-unknown}")
    fi

    echo "META: _CollectionMeta" >> "$OUTPUT_FILE"
    cat >> "$OUTPUT_FILE" <<EOF
OSType: Linux
Hostname: $hostname_str
IP: $ip
User: $current_user
OS: $os_pretty
Kernel: $kernel_ver
Arch: $arch_str
CollectionTimestamp: $collection_ts
ScriptVersion: $SCRIPT_VERSION
Distro: $DISTRO
DistroFamily: $DISTRO_FAMILY
PATH: $PATH
MaxFileSize: ${MAX_FILE_SIZE_MB}MB
DaysBack: $DAYS_BACK
MaxLines: $MAX_LINES
CmdTimeout: ${CMD_TIMEOUT}
EOF
}

# --- _ns: 获取当前纳秒级时间戳 ---
# 优先使用 date +%s%N（GNU coreutils），若不支持则退回到 $SECONDS（整数秒）。
# 返回值单位: 纳秒（如 1711785600123456789）。
_ns() {
    local t
    t=$(date +%s%N 2>/dev/null)
    # 某些 busybox / macOS 的 date 不支持 %N，输出字面 "N"
    if [[ "$t" == *N* ]]; then
        echo "$(( SECONDS * 1000000000 ))"
    else
        echo "$t"
    fi
}

# --- _elapsed_sec: 计算两个纳秒时间戳之间的差值，返回带 1 位小数的秒数 ---
# 用法: _elapsed_sec start_ns end_ns → "1.3"
_elapsed_sec() {
    local start_ns="$1" end_ns="$2"
    awk "BEGIN { printf \"%.1f\", ($end_ns - $start_ns) / 1000000000 }"
}

# --- timed_run: 计时执行采集函数（亚秒精度） ---
timed_run() {
    local func_name="$1"
    local step_name="$2"
    local step_start_ns
    step_start_ns=$(_ns)

    log_info "开始采集: $step_name ..."
    "$func_name"

    local step_end_ns elapsed
    step_end_ns=$(_ns)
    elapsed=$(_elapsed_sec "$step_start_ns" "$step_end_ns")
    STEP_TIMINGS+=("${step_name}|${elapsed}")
    log_info "完成: $step_name (${elapsed}s)"
}

# --- finalize: 写 _ExecutionTiming + REPORT_END ---
finalize() {
    local total_end_ns total_elapsed
    total_end_ns=$(_ns)
    total_elapsed=$(_elapsed_sec "$SCRIPT_START_NS" "$total_end_ns")
    local file_size_human
    file_size_human=$(du -h "$OUTPUT_FILE" 2>/dev/null | cut -f1)

    echo "META: _ExecutionTiming" >> "$OUTPUT_FILE"

    local i=1
    for timing in "${STEP_TIMINGS[@]}"; do
        # timing 格式: "SectionName|X.X"
        local step_name="${timing%%|*}"
        local step_elapsed="${timing##*|}"
        echo "Step $i ($step_name): ${step_elapsed}s" >> "$OUTPUT_FILE"
        i=$((i + 1))
    done

    echo "Total: ${total_elapsed}s" >> "$OUTPUT_FILE"
    echo "OutputFileSize: ${file_size_human:-unknown}" >> "$OUTPUT_FILE"

    if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
        echo "Warning: 输出文件达到大小上限(${MAX_FILE_SIZE_MB}MB)，部分采集被跳过" >> "$OUTPUT_FILE"
    fi

    echo "REPORT_END" >> "$OUTPUT_FILE"
}

# ============================================================
# 认证日志辅助函数
# ============================================================

# --- build_date_patterns: 生成最近 N 天的 "Mon DD" / "Mon  D" 格式用于 grep ---
build_date_patterns() {
    local days="$1"
    local patterns=""
    local i d

    for i in $(seq 0 "$days"); do
        # date -d "N days ago" 是 GNU date 语法
        d=$(date -d "$i days ago" "+%b %_d" 2>/dev/null) || continue
        if [[ -n "$d" ]]; then
            patterns="${patterns}|${d}"
        fi
    done

    # 去掉开头的 |
    echo "${patterns:1}"
}

# --- grep_auth_file: 对单个日志文件执行 grep，支持 .gz ---
grep_auth_file() {
    local file="$1"
    local pattern="$2"
    local date_filter="$3"

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    if [[ "$file" == *.gz ]]; then
        # 压缩文件用 zgrep
        if command -v zgrep &>/dev/null; then
            if [[ -n "$date_filter" ]]; then
                zgrep -E "^($date_filter)" "$file" 2>/dev/null | grep -E "$pattern" 2>/dev/null || true
            else
                zgrep -E "$pattern" "$file" 2>/dev/null || true
            fi
        elif command -v zcat &>/dev/null; then
            if [[ -n "$date_filter" ]]; then
                zcat "$file" 2>/dev/null | grep -E "^($date_filter)" 2>/dev/null | grep -E "$pattern" 2>/dev/null || true
            else
                zcat "$file" 2>/dev/null | grep -E "$pattern" 2>/dev/null || true
            fi
        fi
    else
        if [[ -n "$date_filter" ]]; then
            grep -E "^($date_filter)" "$file" 2>/dev/null | grep -E "$pattern" 2>/dev/null || true
        else
            grep -E "$pattern" "$file" 2>/dev/null || true
        fi
    fi
}

# --- search_auth_logs: 在所有相关日志文件中搜索指定模式 ---
#
# 参数:
#   $1 — grep 模式
#   $2 — max_lines 限制
#
# 使用文件日志或 journalctl fallback
search_auth_logs() {
    local pattern="$1"
    local max_lines="${2:-$MAX_LINES}"
    local output=""
    local total_lines=0

    if [[ -n "$AUTH_LOG_PATH" ]]; then
        # 文件日志策略
        local log_dir base_name date_filter
        log_dir=$(dirname "$AUTH_LOG_PATH")
        base_name=$(basename "$AUTH_LOG_PATH")
        date_filter=$(build_date_patterns "$DAYS_BACK")

        # 找到相关日志文件（按 mtime 过滤）
        local log_files
        log_files=$(find "$log_dir" -name "${base_name}*" -mtime -"$DAYS_BACK" 2>/dev/null | sort)

        if [[ -z "$log_files" ]]; then
            echo "(无数据: 未找到最近 ${DAYS_BACK} 天内修改过的日志文件)" >> "$OUTPUT_FILE"
            return 0
        fi

        local f
        for f in $log_files; do
            local chunk
            chunk=$(grep_auth_file "$f" "$pattern" "$date_filter")
            if [[ -n "$chunk" ]]; then
                output="${output}${chunk}"$'\n'
            fi
        done
    else
        # journalctl fallback（精确时间过滤）
        if command -v journalctl &>/dev/null; then
            output=$(timeout "$CMD_TIMEOUT" journalctl _COMM=sshd --since "${DAYS_BACK} days ago" --no-pager 2>/dev/null \
                | grep -E "$pattern" 2>/dev/null) || true

            if [[ -z "$output" ]]; then
                output=$(timeout "$CMD_TIMEOUT" journalctl -u sshd --since "${DAYS_BACK} days ago" --no-pager 2>/dev/null \
                    | grep -E "$pattern" 2>/dev/null) || true
            fi
        fi
    fi

    # 去掉尾部空行
    output=$(echo "$output" | sed '/^$/d')

    if [[ -z "$output" ]]; then
        echo "(无数据)" >> "$OUTPUT_FILE"
    else
        total_lines=$(echo "$output" | wc -l)
        if [[ $total_lines -gt $max_lines ]]; then
            echo "$output" | head -n "$max_lines" >> "$OUTPUT_FILE"
            echo "... (truncated, showing $max_lines of $total_lines total lines)" >> "$OUTPUT_FILE"
        else
            echo "$output" >> "$OUTPUT_FILE"
        fi
    fi

    check_file_size
    return 0
}

# ============================================================
# Step 1: collect_system_info — 系统基本信息
# ============================================================
collect_system_info() {
    write_section "SystemInfo"

    # --- SUB: whoami ---
    write_sub "whoami"
    run_cmd "whoami" "echo '-- cmd: whoami --'; whoami && echo '-- cmd: id --'; id && echo '-- cmd: groups --'; groups"

    # --- SUB: os_release ---
    write_sub "os_release"
    run_cmd "os_release" "echo '-- cmd: cat /etc/os-release --'; cat /etc/os-release 2>/dev/null; echo '-- cmd: uname -a --'; uname -a 2>/dev/null"

    # /etc/*-release 逐文件输出（含 lsb-release、centos-release 等）
    write_raw "== /etc/*-release files =="
    {
        local found_release=0
        for f in /etc/*-release; do
            if [[ -f "$f" ]]; then
                found_release=1
                echo "-- file: $f --"
                cat "$f" 2>/dev/null || echo "(无法读取)"
            fi
        done
        if [[ $found_release -eq 0 ]]; then
            echo "(未发现 /etc/*-release 文件)"
        fi
    } >> "$OUTPUT_FILE"

    # --- SUB: hardware ---
    write_sub "hardware"
    run_cmd "hardware" "echo '== CPU =='; grep 'model name' /proc/cpuinfo 2>/dev/null | head -1; echo '== Memory =='; free -h 2>/dev/null; echo '== Disk =='; timeout $CMD_TIMEOUT df -h 2>/dev/null"

    # --- SUB: security_hygiene ---
    write_sub "security_hygiene"
    {
        # SELinux
        if command -v getenforce &>/dev/null; then
            echo "SELinux: $(getenforce 2>/dev/null || echo 'unknown')"
        else
            echo "SELinux: not_installed"
        fi

        # Firewall UFW
        if command -v ufw &>/dev/null; then
            local ufw_status
            ufw_status=$(ufw status 2>/dev/null | head -1 | awk '{print $2}')
            echo "Firewall_UFW: ${ufw_status:-unknown}"
        else
            echo "Firewall_UFW: not_installed"
        fi

        # Firewall firewalld
        if command -v firewall-cmd &>/dev/null; then
            local fwd_state
            fwd_state=$(firewall-cmd --state 2>/dev/null || echo "not running")
            echo "Firewall_firewalld: $fwd_state"
        else
            echo "Firewall_firewalld: not_installed"
        fi

        # SSH Service
        if command -v systemctl &>/dev/null; then
            if systemctl is-active sshd &>/dev/null; then
                echo "SSH_Service: running"
            elif systemctl is-active ssh &>/dev/null; then
                echo "SSH_Service: running"
            else
                echo "SSH_Service: stopped"
            fi
        elif command -v service &>/dev/null; then
            if service sshd status &>/dev/null || service ssh status &>/dev/null; then
                echo "SSH_Service: running"
            else
                echo "SSH_Service: stopped"
            fi
        else
            echo "SSH_Service: not_installed"
        fi

        # SSH config parsing
        local sshd_config="/etc/ssh/sshd_config"
        if [[ -f "$sshd_config" ]]; then
            local permit_root password_auth ssh_port

            permit_root=$(grep -i "^PermitRootLogin" "$sshd_config" 2>/dev/null | awk '{print $2}' | head -1)
            echo "SSH_PermitRootLogin: ${permit_root:-(配置未找到)}"

            password_auth=$(grep -i "^PasswordAuthentication" "$sshd_config" 2>/dev/null | awk '{print $2}' | head -1)
            echo "SSH_PasswordAuth: ${password_auth:-(配置未找到)}"

            ssh_port=$(grep -i "^Port" "$sshd_config" 2>/dev/null | awk '{print $2}' | head -1)
            echo "SSH_Port: ${ssh_port:-22}"
        else
            echo "SSH_PermitRootLogin: (配置未找到)"
            echo "SSH_PasswordAuth: (配置未找到)"
            echo "SSH_Port: (配置未找到)"
        fi

        # Password policy
        if [[ -f /etc/login.defs ]]; then
            local max_days min_days
            max_days=$(grep "^PASS_MAX_DAYS" /etc/login.defs 2>/dev/null | awk '{print $2}')
            min_days=$(grep "^PASS_MIN_DAYS" /etc/login.defs 2>/dev/null | awk '{print $2}')
            echo "PasswordMaxDays: ${max_days:-(未设置)}"
            echo "PasswordMinDays: ${min_days:-(未设置)}"
        else
            echo "PasswordMaxDays: (login.defs 不存在)"
            echo "PasswordMinDays: (login.defs 不存在)"
        fi

        # Auditd
        if command -v auditctl &>/dev/null; then
            if pidof auditd &>/dev/null; then
                echo "Auditd: running"
            else
                echo "Auditd: stopped"
            fi
        else
            echo "Auditd: not_installed"
        fi

        # Available disk space for output dir
        local avail_mb
        avail_mb=$(df -m "$OUTPUT_DIR" 2>/dev/null | awk 'NR==2{print $4}')
        echo "AvailDiskMB: ${avail_mb:-unknown}"

    } >> "$OUTPUT_FILE"

    # --- SUB: users ---
    write_sub "users"
    run_cmd "loginable_users" "echo '-- cmd: loginable_users --'; grep -v -E '(nologin|false|/bin/sync|/usr/sbin/nologin)$' /etc/passwd 2>/dev/null; echo '-- cmd: lastlog --'; lastlog 2>/dev/null | grep -v 'Never logged in' || echo '(lastlog 不可用)'"

    # --- SUB: sudoers ---
    write_sub "sudoers"
    run_cmd "sudoers" "echo '-- cmd: sudoers --'; grep -v -E '^#|^$' /etc/sudoers 2>/dev/null || echo '(无法读取 /etc/sudoers)'; echo '-- cmd: ls sudoers.d --'; ls -la /etc/sudoers.d/ 2>/dev/null || echo '(目录不存在)'" "$MAX_LINES"

    # 遍历 sudoers.d 下文件
    if [[ -d /etc/sudoers.d ]]; then
        local sfile
        for sfile in /etc/sudoers.d/*; do
            if [[ -f "$sfile" ]]; then
                write_raw "-- file: $sfile --"
                run_cmd "sudoers.d/$(basename "$sfile")" "grep -v -E '^#|^$' '$sfile' 2>/dev/null"
            fi
        done
    fi

    # --- SUB: env_integrity ---
    write_sub "env_integrity"
    {
        local cmd_name cmd_path cmd_hash
        for cmd_name in "${KEY_CMDS[@]}"; do
            cmd_path=$(command -v "$cmd_name" 2>/dev/null || echo "")
            if [[ -n "$cmd_path" ]]; then
                cmd_hash=$(md5sum "$cmd_path" 2>/dev/null | awk '{print $1}')
                echo "$cmd_name: path=$cmd_path hash=${cmd_hash:-unknown}"
            else
                echo "$cmd_name: (不可用)"
            fi
        done
    } >> "$OUTPUT_FILE"
}

# ============================================================
# Step 2: collect_auth_logs — 认证日志
# ============================================================
collect_auth_logs() {
    write_section "AuthLogs"

    # 标注时间过滤模式
    if [[ -n "$AUTH_LOG_PATH" ]]; then
        write_raw "时间过滤: 尽力模式（基于文件 mtime + 月日匹配, 最近 ${DAYS_BACK} 天）"
    else
        write_raw "时间过滤: 精确模式（journalctl --since, 最近 ${DAYS_BACK} 天）"
    fi

    # --- CATEGORY: SSH ---
    write_category "SSH"

    write_events "ssh_login_success"
    search_auth_logs "Accepted" "$MAX_LINES"

    write_events "ssh_login_failed"
    search_auth_logs "Failed password|authentication failure" "$MAX_LINES"

    write_events "ssh_accepted_keys"
    search_auth_logs "Accepted publickey" "$MAX_LINES"

    # --- CATEGORY: Sudo ---
    write_category "Sudo"

    write_events "sudo_commands"
    search_auth_logs "sudo:.*COMMAND=" "$MAX_LINES"

    # --- CATEGORY: UserMgmt ---
    write_category "UserMgmt"

    write_events "user_created"
    search_auth_logs "useradd|adduser" "$MAX_LINES"

    write_events "user_modified"
    search_auth_logs "usermod|passwd|chage" "$MAX_LINES"
}

# ============================================================
# Step 3: collect_processes — 进程信息
# ============================================================
collect_processes() {
    write_section "Processes"

    # --- SUB: cpu_top15 ---
    write_sub "cpu_top15"
    run_cmd "ps_cpu_top15" "ps aux --sort=-%cpu | head -16"

    # --- SUB: mem_top15 ---
    write_sub "mem_top15"
    run_cmd "ps_mem_top15" "ps aux --sort=-%mem | head -16"

    # --- SUB: ppid1_processes ---
    write_sub "ppid1_processes"
    run_cmd "ppid1" "ps -eo pid,ppid,user,stat,%cpu,%mem,start,time,args --sort=-start | awk 'NR==1 || \$2==1'" "$MAX_LINES"

    # --- SUB: reverse_shell_check ---
    write_sub "reverse_shell_check"

    # 1. 已建立的 TCP 连接
    write_raw "== Established TCP connections (with process info) =="
    run_cmd "ss_estab" "ss -tnp 2>/dev/null | grep ESTAB || netstat -tnp 2>/dev/null | grep ESTABLISHED"

    # 2. 针对 ESTABLISHED 连接的进程检查 socket fd
    write_raw "== Socket FD check for ESTABLISHED PIDs =="
    run_cmd "socket_fd_check" "
        pids=\$(ss -tnp 2>/dev/null | grep ESTAB | grep -o 'pid=[0-9]*' | sed 's/pid=//' | sort -u)
        if [ -n \"\$pids\" ]; then
            for p in \$pids; do
                ls -la /proc/\$p/fd 2>/dev/null | grep socket && echo \"  ^-- PID: \$p ($(cat /proc/\$p/comm 2>/dev/null))\"
            done
        else
            echo '(无 ESTABLISHED 连接的 PID)'
        fi
    "

    # 3. /dev/tcp, /dev/udp
    write_raw "== /dev/tcp /dev/udp usage =="
    run_cmd "dev_tcp_udp" "ls -la /proc/*/fd 2>/dev/null | grep -E '/dev/(tcp|udp)' || echo '(未发现 /dev/tcp|udp 使用)'"

    # 4. 常见反弹 shell 模式（使用 [x]xx 避免匹配 grep 自身）
    write_raw "== Reverse shell pattern detection =="
    run_cmd "reverse_shell_patterns" "ps aux | grep -E '[b]ash -i|[n]c -e|[n]cat|[s]ocat|[p]ython.*pty|[p]erl.*socket|[r]uby.*TCPSocket|[p]hp.*fsockopen' || echo '(未发现常见反弹 shell 模式)'"
}

# ============================================================
# Step 4: collect_network — 网络信息
# ============================================================
collect_network() {
    write_section "Network"

    # --- SUB: listening_ports ---
    write_sub "listening_ports"
    run_cmd "listening" "ss -tulpn 2>/dev/null || netstat -tulpn 2>/dev/null" "$MAX_LINES"

    # --- SUB: established_tcp ---
    write_sub "established_tcp"
    run_cmd "established" "ss -tnp state established 2>/dev/null || netstat -tnp 2>/dev/null | grep ESTABLISHED" "$MAX_LINES"

    # --- SUB: route ---
    write_sub "route"
    run_cmd "route_table" "ip route 2>/dev/null || route -n 2>/dev/null"

    # --- SUB: arp ---
    write_sub "arp"
    run_cmd "arp_table" "ip neigh 2>/dev/null || arp -a 2>/dev/null"

    # --- SUB: dns ---
    write_sub "dns"
    run_cmd "dns_config" "cat /etc/resolv.conf 2>/dev/null"

    # --- SUB: iptables ---
    write_sub "iptables"
    run_cmd "iptables_v4" "echo '== IPv4 =='; iptables -L -n -v --line-numbers 2>/dev/null || echo '(iptables 不可用)'"
    run_cmd "iptables_v6" "echo '== IPv6 =='; ip6tables -L -n -v --line-numbers 2>/dev/null || echo '(ip6tables 不可用)'"

    # --- SUB: ip_forward ---
    write_sub "ip_forward"
    run_cmd "ip_forward" "echo 'IPv4 forwarding:'; cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo '(不可读)'; echo 'IPv6 forwarding:'; cat /proc/sys/net/ipv6/conf/all/forwarding 2>/dev/null || echo '(不可读)'"
}

# ============================================================
# Step 5: collect_persistence — 持久化机制
# ============================================================
collect_persistence() {
    write_section "Persistence"

    # --- SUB: crontab ---
    write_sub "crontab"
    run_cmd "root_crontab" "echo '== root crontab =='; crontab -l 2>/dev/null || echo '(root 无 crontab)'"

    # 遍历用户 crontab
    {
        local cron_dirs=("/var/spool/cron/crontabs" "/var/spool/cron")
        local cdir
        for cdir in "${cron_dirs[@]}"; do
            echo "== $cdir ==" >> "$OUTPUT_FILE"
            if [[ ! -d "$cdir" ]]; then
                echo "(目录不存在)" >> "$OUTPUT_FILE"
                continue
            fi
            local cfile found_cron_file=0
            for cfile in "$cdir"/*; do
                if [[ -f "$cfile" ]]; then
                    found_cron_file=1
                    echo "-- file: $(basename "$cfile") --" >> "$OUTPUT_FILE"
                    cat "$cfile" >> "$OUTPUT_FILE" 2>/dev/null || echo "(无法读取)" >> "$OUTPUT_FILE"
                fi
            done
            if [[ $found_cron_file -eq 0 ]]; then
                echo "(无数据)" >> "$OUTPUT_FILE"
            fi
        done
    }

    # --- SUB: crontab_files ---
    write_sub "crontab_files"
    run_cmd "etc_crontab" "echo '== /etc/crontab =='; cat /etc/crontab 2>/dev/null || echo '(不存在)'"

    # /etc/cron.d/
    if [[ -d /etc/cron.d ]]; then
        local cronf
        for cronf in /etc/cron.d/*; do
            if [[ -f "$cronf" ]]; then
                write_raw "-- file: $cronf --"
                run_cmd "cron.d/$(basename "$cronf")" "cat '$cronf' 2>/dev/null"
            fi
        done
    fi

    # --- SUB: init_d ---
    write_sub "init_d"
    run_cmd "init_d_list" "ls -la /etc/init.d/ 2>/dev/null || echo '(/etc/init.d 不存在)'"

    # 遍历 init.d 脚本：白名单内 → 一行摘要；白名单外 → head -20
    #
    #   输出示意:
    #     [known] apparmor  (ELF / ASCII text / Bourne-Again shell script ...)
    #     [known] cron      (ASCII text)
    #     --- /etc/init.d/mining_worker (前 20 行) ---
    #     #!/bin/bash
    #     ...
    if [[ -d /etc/init.d ]]; then
        local initf bname
        local known_count=0 custom_count=0

        for initf in /etc/init.d/*; do
            if [[ ! -f "$initf" ]]; then
                continue
            fi
            bname=$(basename "$initf")

            # 查白名单
            local is_known=0
            local k
            for k in "${KNOWN_INIT_SCRIPTS[@]}"; do
                if [[ "$bname" == "$k" ]]; then
                    is_known=1
                    break
                fi
            done

            if [[ $is_known -eq 1 ]]; then
                # 白名单脚本：仅输出一行摘要（名称 + file 类型）
                local ftype
                ftype=$(file -b "$initf" 2>/dev/null | cut -c1-60)
                write_raw "[known] $bname  ($ftype)"
                known_count=$((known_count + 1))
            else
                # 非白名单脚本：输出前 20 行以便审查
                write_raw "-- file: $initf (前 20 行) --"
                run_cmd "init.d/$bname" "head -20 '$initf' 2>/dev/null"
                custom_count=$((custom_count + 1))
            fi
        done

        write_raw "(init.d 统计: known=$known_count, custom/unknown=$custom_count)"
    fi

    # --- SUB: systemd_units ---
    write_sub "systemd_units"
    run_cmd "systemd_enabled" "systemctl list-unit-files --type=service --state=enabled --no-pager 2>/dev/null || echo '(systemctl 不可用)'" "$MAX_LINES"

    # 自定义 systemd 服务文件
    if [[ -d /etc/systemd/system ]]; then
        write_raw "== 自定义 systemd service 文件 =="
        local svcf
        for svcf in /etc/systemd/system/*.service; do
            if [[ -f "$svcf" && ! -L "$svcf" ]]; then
                write_raw "-- file: $svcf --"
                run_cmd "systemd/$(basename "$svcf")" "cat '$svcf' 2>/dev/null"
            fi
        done
    fi

    # --- SUB: shell_profiles ---
    write_sub "shell_profiles"

    # 系统级
    local sys_profile
    for sys_profile in /etc/profile /etc/bash.bashrc /etc/bashrc; do
        if [[ -f "$sys_profile" ]]; then
            write_raw "-- file: $sys_profile --"
            run_cmd "profile/$(basename "$sys_profile")" "cat '$sys_profile' 2>/dev/null" "$MAX_LINES"
        fi
    done

    # 用户级：统一遍历
    local home_dir
    for home_dir in /root /home/*; do
        if [[ ! -d "$home_dir" ]]; then
            continue
        fi
        local pfile
        for pfile in .bashrc .bash_profile .profile .bash_logout; do
            local target="${home_dir}/${pfile}"
            if [[ -f "$target" ]]; then
                write_raw "-- file: $target --"
                run_cmd "profile/${home_dir##*/}/$pfile" "cat '$target' 2>/dev/null" "$MAX_LINES"
            fi
        done
    done

    # --- SUB: rc_local ---
    write_sub "rc_local"
    local rcf
    for rcf in /etc/rc.local /etc/rc.d/rc.local; do
        if [[ -f "$rcf" ]]; then
            write_raw "-- file: $rcf --"
            run_cmd "rc_local/$rcf" "echo '-- cmd: stat --'; echo 'permissions: $(stat -c %a \"$rcf\" 2>/dev/null)'; echo 'executable: $(test -x \"$rcf\" && echo yes || echo no)'; echo '-- cmd: cat --'; cat '$rcf' 2>/dev/null"
        fi
    done
    # 如果两个都不存在
    if [[ ! -f /etc/rc.local && ! -f /etc/rc.d/rc.local ]]; then
        write_raw "(rc.local 不存在)"
    fi
}

# ============================================================
# Step 6: collect_ssh — SSH 安全
# ============================================================
collect_ssh() {
    write_section "SSH"

    # --- SUB: sshd_stat ---
    write_sub "sshd_stat"
    run_cmd "sshd_stat" "
        if [ -f /usr/sbin/sshd ]; then
            echo '== stat ==';
            stat /usr/sbin/sshd 2>/dev/null;
            echo '== md5sum ==';
            md5sum /usr/sbin/sshd 2>/dev/null;
        else
            echo '(sshd 二进制文件未找到: /usr/sbin/sshd)';
            # 尝试其他路径
            sshd_path=\$(command -v sshd 2>/dev/null);
            if [ -n \"\$sshd_path\" ]; then
                echo \"Found at: \$sshd_path\";
                stat \"\$sshd_path\" 2>/dev/null;
                md5sum \"\$sshd_path\" 2>/dev/null;
            fi
        fi
    "

    # --- SUB: sshd_config_check ---
    write_sub "sshd_config_check"
    run_cmd "sshd_config" "echo '== /etc/ssh/sshd_config (去注释空行) =='; grep -v -E '^#|^$' /etc/ssh/sshd_config 2>/dev/null || echo '(不存在)'" "$MAX_LINES"

    # sshd_config.d
    if [[ -d /etc/ssh/sshd_config.d ]]; then
        write_raw "== /etc/ssh/sshd_config.d/ =="
        run_cmd "sshd_config_d_list" "ls -la /etc/ssh/sshd_config.d/ 2>/dev/null"
        local scf
        for scf in /etc/ssh/sshd_config.d/*; do
            if [[ -f "$scf" ]]; then
                write_raw "--- $scf ---"
                run_cmd "sshd_config.d/$(basename "$scf")" "grep -v -E '^#|^$' '$scf' 2>/dev/null"
            fi
        done
    fi

    # --- SUB: authorized_keys ---
    write_sub "authorized_keys"
    {
        local found=0
        local home_dir
        for home_dir in /root /home/*; do
            if [[ ! -d "$home_dir" ]]; then
                continue
            fi
            local akf
            for akf in "${home_dir}/.ssh/authorized_keys" "${home_dir}/.ssh/authorized_keys2"; do
                if [[ -f "$akf" ]]; then
                    found=1
                    {
                        echo "-- file: $akf --"
                        echo "permissions: $(stat -c '%a' "$akf" 2>/dev/null || echo 'unknown')"
                        echo "owner: $(stat -c '%U:%G' "$akf" 2>/dev/null || echo 'unknown')"
                        cat "$akf" 2>/dev/null || echo "(无法读取)"
                    } >> "$OUTPUT_FILE"
                fi
            done
        done

        if [[ $found -eq 0 ]]; then
            echo "(未发现 authorized_keys 文件)" >> "$OUTPUT_FILE"
        fi
    }

    # --- SUB: pam_check ---
    write_sub "pam_check"
    run_cmd "pam_sshd" "echo '== /etc/pam.d/sshd =='; cat /etc/pam.d/sshd 2>/dev/null || echo '(不存在)'"

    # 最近 30 天修改过的 PAM .so 文件
    write_raw "== 最近 30 天修改过的 PAM .so 文件 =="
    run_cmd "pam_recent_so" "
        found=0
        for dir in /lib/security /lib64/security /usr/lib/security /usr/lib64/security /usr/lib/x86_64-linux-gnu/security; do
            if [ -d \"\$dir\" ]; then
                result=\$(find \"\$dir\" -name '*.so' -mtime -30 -ls 2>/dev/null)
                if [ -n \"\$result\" ]; then
                    echo \"\$result\"
                    found=1
                fi
            fi
        done
        if [ \$found -eq 0 ]; then
            echo '(未发现近 30 天修改的 PAM .so 文件)'
        fi
    "
}

# ============================================================
# Step 7: collect_shell_history — 命令历史
# ============================================================
collect_shell_history() {
    write_section "ShellHistory"

    # --- SUB: bash_history_sensitive ---
    write_sub "bash_history_sensitive"
    {
        local found=0
        local home_dir
        for home_dir in /root /home/*; do
            local hfile="${home_dir}/.bash_history"
            if [[ -f "$hfile" ]]; then
                found=1
                write_raw "-- file: $hfile --"
                # 检查行数，超限则截取最近的记录
                local line_count
                line_count=$(wc -l < "$hfile" 2>/dev/null || echo "0")
                if [[ "$line_count" -gt "$MAX_LINES" ]]; then
                    tail -n "$MAX_LINES" "$hfile" >> "$OUTPUT_FILE" 2>/dev/null
                    write_raw "... (truncated, showing last $MAX_LINES of $line_count total lines)"
                else
                    cat "$hfile" >> "$OUTPUT_FILE" 2>/dev/null
                fi
                check_file_size
                if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
                    break
                fi
            fi
        done
        if [[ $found -eq 0 ]]; then
            write_raw "(未发现 .bash_history 文件)"
        fi
    }

    # --- SUB: zsh_history_sensitive ---
    write_sub "zsh_history_sensitive"
    {
        local found=0
        local home_dir
        for home_dir in /root /home/*; do
            local hfile="${home_dir}/.zsh_history"
            if [[ -f "$hfile" ]]; then
                found=1
                write_raw "-- file: $hfile --"
                local line_count
                line_count=$(wc -l < "$hfile" 2>/dev/null || echo "0")
                if [[ "$line_count" -gt "$MAX_LINES" ]]; then
                    tail -n "$MAX_LINES" "$hfile" >> "$OUTPUT_FILE" 2>/dev/null
                    write_raw "... (truncated, showing last $MAX_LINES of $line_count total lines)"
                else
                    cat "$hfile" >> "$OUTPUT_FILE" 2>/dev/null
                fi
                check_file_size
                if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
                    break
                fi
            fi
        done
        if [[ $found -eq 0 ]]; then
            write_raw "(未发现 .zsh_history 文件)"
        fi
    }
}

# ============================================================
# Step 8: collect_environment — 环境信息
# ============================================================
#
# 采集范围:
#   - 环境变量（可疑变量高亮）
#   - 已加载内核模块
#   - 系统时区与 NTP 同步状态
#
# 安全分析价值:
#   - LD_PRELOAD / LD_LIBRARY_PATH 可被用于劫持库加载
#   - 异常内核模块可能是 rootkit
#   - 时区/NTP 偏差可能表明日志时间不可信
# ============================================================
collect_environment() {
    write_section "Environment"

    # --- SUB: env_variables ---
    write_sub "env_variables"
    run_cmd "env_all" "env 2>/dev/null | sort" "$MAX_LINES"

    # 高亮可疑环境变量（单独列出，方便 AI 分析）
    write_raw "== 可疑环境变量检查 =="
    run_cmd "env_suspicious" "
        suspicious=0
        for var in LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT HISTFILE HISTSIZE HISTFILESIZE PROMPT_COMMAND; do
            val=\$(printenv \"\$var\" 2>/dev/null)
            if [ -n \"\$val\" ]; then
                echo \"\$var=\$val\"
                suspicious=1
            fi
        done
        # 检查 LD_PRELOAD 指向的文件是否存在
        if [ -n \"\$(printenv LD_PRELOAD 2>/dev/null)\" ]; then
            echo '== LD_PRELOAD 文件检查 =='
            for f in \$(printenv LD_PRELOAD | tr ':' ' '); do
                if [ -f \"\$f\" ]; then
                    echo \"存在: \$f ($(ls -la \"\$f\" 2>/dev/null))\"
                else
                    echo \"不存在: \$f\"
                fi
            done
        fi
        if [ \$suspicious -eq 0 ]; then
            echo '(未发现可疑环境变量)'
        fi
    "

    # --- SUB: kernel_modules ---
    write_sub "kernel_modules"
    run_cmd "lsmod" "lsmod 2>/dev/null" "$MAX_LINES"

    # 最近 30 天加载的非标准内核模块（通过 modinfo 检查签名）
    write_raw "== 无签名/非标准内核模块检查 =="
    run_cmd "unsigned_modules" "
        if command -v modinfo >/dev/null 2>&1; then
            unsigned=0
            for mod in \$(lsmod 2>/dev/null | awk 'NR>1{print \$1}'); do
                sig=\$(modinfo \"\$mod\" 2>/dev/null | grep -i 'sig_id\\|signer')
                if [ -z \"\$sig\" ]; then
                    modpath=\$(modinfo -n \"\$mod\" 2>/dev/null)
                    echo \"无签名: \$mod (\$modpath)\"
                    unsigned=\$((unsigned+1))
                fi
            done
            if [ \$unsigned -eq 0 ]; then
                echo '(所有已加载模块均有签名)'
            else
                echo \"共 \$unsigned 个无签名模块\"
            fi
        else
            echo '(modinfo 不可用，跳过签名检查)'
        fi
    " "$MAX_LINES" 60

    # --- SUB: timezone_ntp ---
    write_sub "timezone_ntp"
    run_cmd "timezone" "
        echo '== 时区 =='
        if command -v timedatectl >/dev/null 2>&1; then
            timedatectl 2>/dev/null
        else
            echo \"TZ=\${TZ:-未设置}\"
            date '+%Z %:z' 2>/dev/null
            cat /etc/timezone 2>/dev/null || echo '(/etc/timezone 不存在)'
        fi
        echo '== NTP 同步 =='
        if command -v timedatectl >/dev/null 2>&1; then
            timedatectl show --property=NTPSynchronized 2>/dev/null || echo '(timedatectl show 不支持)'
        fi
        if command -v ntpq >/dev/null 2>&1; then
            echo '-- ntpq peers --'
            ntpq -p 2>/dev/null || echo '(ntpq 不可用)'
        fi
        if command -v chronyc >/dev/null 2>&1; then
            echo '-- chronyc tracking --'
            chronyc tracking 2>/dev/null || echo '(chronyc 不可用)'
        fi
    "
}

# ============================================================
# Step 9: collect_file_integrity — 文件完整性校验
# ============================================================
#
# 采集范围:
#   - RHEL 系: rpm -Va（校验所有已安装包的文件完整性）
#   - Debian 系: debsums -c（报告校验失败的文件）
#
# 安全分析价值:
#   - 检测被篡改的系统二进制（如 sshd, su, sudo 被植入后门）
#   - 发现被修改的配置文件
#   - 注意: debsums 可能未预装，需要处理依赖缺失
# ============================================================
collect_file_integrity() {
    write_section "FileIntegrity"

    # --- SUB: package_verify ---
    write_sub "package_verify"

    if [[ "$DISTRO_FAMILY" == "rhel" ]]; then
        # RHEL 系: rpm -Va
        # 输出格式: SM5DLUGT c <file>
        # S=Size, M=Mode, 5=MD5, D=Device, L=Link, U=User, G=Group, T=mTime
        write_raw "== rpm -Va（包文件完整性校验）=="
        run_cmd "rpm_verify" "rpm -Va 2>/dev/null | grep -v '^\\.\\.' || echo '(所有文件校验通过或 rpm 不可用)'" "$MAX_LINES" 120

        # 单独列出关键二进制的校验结果
        write_raw "== 关键二进制校验 =="
        run_cmd "rpm_verify_critical" "
            for bin in /usr/sbin/sshd /usr/bin/sudo /usr/bin/su /usr/bin/passwd /usr/bin/login /usr/bin/ssh /usr/sbin/crond /usr/sbin/cron; do
                if [ -f \"\$bin\" ]; then
                    result=\$(rpm -Vf \"\$bin\" 2>/dev/null)
                    if [ -n \"\$result\" ]; then
                        echo \"⚠ \$bin: \$result\"
                    else
                        echo \"✓ \$bin: 校验通过\"
                    fi
                fi
            done
        " "$MAX_LINES" 60

    elif [[ "$DISTRO_FAMILY" == "debian" ]]; then
        # Debian 系: debsums
        if command -v debsums &>/dev/null; then
            write_raw "== debsums -c（校验失败的文件）=="
            run_cmd "debsums_check" "debsums -c 2>/dev/null || echo '(debsums 校验完成，无异常或执行失败)'" "$MAX_LINES" 120

            # 单独校验关键包
            write_raw "== 关键包校验 =="
            run_cmd "debsums_critical" "
                for pkg in openssh-server sudo login passwd coreutils; do
                    if dpkg -l \"\$pkg\" >/dev/null 2>&1; then
                        result=\$(debsums -c \"\$pkg\" 2>/dev/null)
                        if [ -n \"\$result\" ]; then
                            echo \"⚠ \$pkg: \$result\"
                        else
                            echo \"✓ \$pkg: 校验通过\"
                        fi
                    fi
                done
            " "$MAX_LINES" 60
        else
            write_raw "== debsums 未安装 =="
            write_raw "(debsums 未安装，无法进行包文件完整性校验)"
            write_raw "安装命令: apt-get install debsums"

            # Fallback: 手动校验关键二进制的 dpkg MD5
            write_raw "== Fallback: dpkg MD5 校验关键二进制 =="
            run_cmd "dpkg_md5_verify" "
                for bin in /usr/sbin/sshd /usr/bin/sudo /usr/bin/su /usr/bin/passwd /usr/bin/login /usr/bin/ssh; do
                    if [ -f \"\$bin\" ]; then
                        pkg=\$(dpkg -S \"\$bin\" 2>/dev/null | head -1 | cut -d: -f1)
                        if [ -n \"\$pkg\" ]; then
                            expected=\$(grep \"\$bin\" /var/lib/dpkg/info/\${pkg}.md5sums 2>/dev/null | awk '{print \$1}')
                            actual=\$(md5sum \"\$bin\" 2>/dev/null | awk '{print \$1}')
                            if [ -n \"\$expected\" ] && [ -n \"\$actual\" ]; then
                                if [ \"\$expected\" = \"\$actual\" ]; then
                                    echo \"✓ \$bin (\$pkg): MD5 匹配\"
                                else
                                    echo \"⚠ \$bin (\$pkg): MD5 不匹配! expected=\$expected actual=\$actual\"
                                fi
                            else
                                echo \"? \$bin (\$pkg): 无法获取 MD5 (expected=\${expected:-无} actual=\${actual:-无})\"
                            fi
                        else
                            echo \"? \$bin: 未找到所属包\"
                        fi
                    fi
                done
            " "$MAX_LINES" 60
        fi

    else
        write_raw "(未知发行版族 '$DISTRO_FAMILY'，跳过包完整性校验)"
    fi

    # --- SUB: suid_sgid ---
    # SUID/SGID 文件列表（跨发行版通用）
    write_sub "suid_sgid"
    write_raw "== SUID 文件 =="
    run_cmd "suid_files" "find / -perm -4000 -type f -ls 2>/dev/null | grep -v -E '(/proc/|/sys/)'" "$MAX_LINES" 60
    write_raw "== SGID 文件 =="
    run_cmd "sgid_files" "find / -perm -2000 -type f -ls 2>/dev/null | grep -v -E '(/proc/|/sys/)'" "$MAX_LINES" 60
}
main() {
    SCRIPT_START_NS=$(_ns)

    check_root
    parse_args "$@"
    detect_distro
    init_output_file
    check_disk_space
    write_meta

    log_info "开始采集 (days_back=$DAYS_BACK, max_lines=$MAX_LINES, max_file_size=${MAX_FILE_SIZE_MB}MB, cmd_timeout=${CMD_TIMEOUT}s)"

    # Step 1: SystemInfo
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 1 ]]; then
        timed_run "collect_system_info" "SystemInfo"
    fi

    # Step 2: AuthLogs
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 2 ]]; then
        timed_run "collect_auth_logs" "AuthLogs"
    fi

    # Step 3: Processes
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 3 ]]; then
        timed_run "collect_processes" "Processes"
    fi

    # Step 4: Network
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 4 ]]; then
        timed_run "collect_network" "Network"
    fi

    # Step 5: Persistence
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 5 ]]; then
        timed_run "collect_persistence" "Persistence"
    fi

    # Step 6: SSH
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 6 ]]; then
        timed_run "collect_ssh" "SSH"
    fi

    # Step 7: ShellHistory
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 7 ]]; then
        timed_run "collect_shell_history" "ShellHistory"
    fi

    # Step 8: Environment
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 8 ]]; then
        timed_run "collect_environment" "Environment"
    fi

    # Step 9: FileIntegrity
    if [[ $STEP_CHOICE -eq 0 || $STEP_CHOICE -eq 9 ]]; then
        timed_run "collect_file_integrity" "FileIntegrity"
    fi

    finalize

    log_info "========================================="
    log_info "采集完成!"
    log_info "输出文件: $OUTPUT_FILE"
    log_info "文件大小: $(du -h "$OUTPUT_FILE" 2>/dev/null | cut -f1)"
    log_info "总耗时: $(_elapsed_sec "$SCRIPT_START_NS" "$(_ns)")s"
    if [[ $FILE_SIZE_EXCEEDED -eq 1 ]]; then
        log_warn "注意: 输出文件达到大小上限(${MAX_FILE_SIZE_MB}MB)，部分采集可能被跳过"
    fi
    log_info "========================================="
}

main "$@"
