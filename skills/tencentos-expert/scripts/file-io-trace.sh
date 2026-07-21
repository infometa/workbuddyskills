#!/bin/bash
#
# 脚本名称：file-io-trace.sh
# 功能：一键采集进程文件 I/O 信息，辅助诊断 I/O 问题
# 用法：./file-io-trace.sh [PID] [采集时长(秒)]
#
# 作者：chaohaichen@tencent.com
# 版本：1.0.0
#

set -euo pipefail

# 引入公共函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="${SCRIPT_DIR}/../../../shared/utils/common.sh"
OUTPUT_SH="${SCRIPT_DIR}/../../../shared/utils/output.sh"

if [ -f "$COMMON_SH" ]; then
    source "$COMMON_SH"
else
    # 内置基础函数（独立运行时使用）
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
    success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
    warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
    error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fi

if [ -f "$OUTPUT_SH" ]; then
    source "$OUTPUT_SH"
fi

# 默认参数
TARGET_PID="${1:-}"
DURATION="${2:-5}"
REPORT_DIR=""

# 使用说明
usage() {
    cat << 'EOF'
用法: file-io-trace.sh [PID] [采集时长(秒)]

参数:
  PID           目标进程 PID（可选，不指定则显示系统整体 IO 概览）
  采集时长      strace/blktrace 等工具的采集时长，默认 5 秒

示例:
  ./file-io-trace.sh                # 系统整体 IO 概览
  ./file-io-trace.sh 1234           # 分析 PID 1234 的文件 IO（采集 5 秒）
  ./file-io-trace.sh 1234 10        # 分析 PID 1234 的文件 IO（采集 10 秒）

说明:
  - 部分功能需要 root 权限
  - 采集过程中 strace 会对目标进程产生一定性能影响
  - 报告输出到 /tmp/file-io-trace-<PID>-<timestamp>/ 目录
EOF
    exit 0
}

# 参数检查
if [ "${TARGET_PID}" = "-h" ] || [ "${TARGET_PID}" = "--help" ]; then
    usage
fi

# 检查进程是否存在
check_process() {
    local pid=$1
    if [ ! -d "/proc/$pid" ]; then
        error "进程 $pid 不存在"
        exit 1
    fi
}

# 打印分隔线
print_separator() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
    echo ""
}

# 采集系统整体 IO 概览
collect_system_overview() {
    print_separator "系统 I/O 概览"

    info "系统基本信息"
    echo "内核版本: $(uname -r)"
    echo "OS: $(cat /etc/os-release 2>/dev/null | grep -E '^PRETTY_NAME=' | cut -d= -f2 | tr -d '"')"
    echo "负载: $(uptime)"
    echo ""

    info "磁盘设备信息"
    lsblk -o NAME,TYPE,SIZE,MOUNTPOINT,SCHED 2>/dev/null || lsblk
    echo ""

    info "IO 调度器"
    for disk in /sys/block/sd* /sys/block/vd* /sys/block/nvme*; do
        if [ -f "$disk/queue/scheduler" ]; then
            echo "  $(basename "$disk"): $(cat "$disk/queue/scheduler")"
        fi
    done 2>/dev/null
    echo ""

    info "iostat 概览（${DURATION}秒采样）"
    if command -v iostat &>/dev/null; then
        iostat -x -t 1 "$DURATION" 2>/dev/null | tail -$(($(lsblk -d -n | wc -l) + 5))
    else
        warning "iostat 未安装（请安装 sysstat 包）"
    fi
    echo ""

    info "Dirty Page 状态"
    cat /proc/meminfo 2>/dev/null | grep -E "Dirty|Writeback"
    echo ""

    info "IO 高的进程 TOP 15"
    if command -v iotop &>/dev/null && [ "$EUID" -eq 0 ]; then
        iotop -b -o -n 2 2>/dev/null | head -20
    else
        if [ "$EUID" -ne 0 ]; then
            warning "iotop 需要 root 权限，使用 /proc/*/io 替代"
        fi
        echo "PID       READ_BYTES     WRITE_BYTES    COMM"
        for pid in $(ps -eo pid --no-headers); do
            if [ -f "/proc/$pid/io" ] && [ -r "/proc/$pid/io" ]; then
                io_data=$(cat "/proc/$pid/io" 2>/dev/null) || continue
                comm=$(cat "/proc/$pid/comm" 2>/dev/null) || continue
                read_bytes=$(echo "$io_data" | awk '/^read_bytes:/{print $2}')
                write_bytes=$(echo "$io_data" | awk '/^write_bytes:/{print $2}')
                if [ "${read_bytes:-0}" -gt 0 ] || [ "${write_bytes:-0}" -gt 0 ]; then
                    printf "%-9s %-14s %-14s %s\n" "$pid" "$read_bytes" "$write_bytes" "$comm"
                fi
            fi
        done 2>/dev/null | sort -t' ' -k3 -rn | head -15
    fi
}

# 采集进程 IO 详情
collect_process_io() {
    local pid=$1

    print_separator "进程 I/O 详情 (PID: $pid)"

    # 进程基本信息
    info "进程基本信息"
    ps -p "$pid" -o pid,ppid,user,%cpu,%mem,vsz,rss,stat,start,time,args 2>/dev/null
    echo ""
    echo "工作目录: $(readlink /proc/$pid/cwd 2>/dev/null || echo '无法读取')"
    echo "可执行文件: $(readlink /proc/$pid/exe 2>/dev/null || echo '无法读取')"
    echo ""

    # IO 统计
    info "进程 IO 统计 (/proc/$pid/io)"
    if [ -r "/proc/$pid/io" ]; then
        cat "/proc/$pid/io"
    else
        warning "无法读取 /proc/$pid/io（可能需要 root 权限）"
    fi
    echo ""

    # 文件描述符统计
    info "文件描述符统计"
    local fd_count
    fd_count=$(ls "/proc/$pid/fd" 2>/dev/null | wc -l)
    local fd_soft
    fd_soft=$(cat "/proc/$pid/limits" 2>/dev/null | grep 'Max open files' | awk '{print $4}')
    local fd_hard
    fd_hard=$(cat "/proc/$pid/limits" 2>/dev/null | grep 'Max open files' | awk '{print $5}')
    echo "当前打开 fd: $fd_count"
    echo "fd 上限 (soft): ${fd_soft:-未知}"
    echo "fd 上限 (hard): ${fd_hard:-未知}"
    if [ "$fd_count" -gt 0 ] && [ -n "$fd_soft" ] && [ "$fd_soft" != "unlimited" ]; then
        local usage_pct=$((fd_count * 100 / fd_soft))
        if [ "$usage_pct" -gt 80 ]; then
            warning "fd 使用率 ${usage_pct}%，接近上限！"
        else
            echo "fd 使用率: ${usage_pct}%"
        fi
    fi
    echo ""

    # 打开的文件列表
    info "打开的文件（lsof）"
    if command -v lsof &>/dev/null; then
        echo "--- 普通文件 ---"
        lsof -p "$pid" 2>/dev/null | grep REG | head -20
        echo ""
        echo "--- 按类型统计 ---"
        lsof -p "$pid" 2>/dev/null | awk 'NR>1{print $5}' | sort | uniq -c | sort -rn
    else
        warning "lsof 未安装"
        echo "--- /proc/$pid/fd ---"
        ls -la "/proc/$pid/fd" 2>/dev/null | head -20
    fi
    echo ""

    # strace 追踪
    info "strace IO 系统调用统计（${DURATION}秒采样）"
    if command -v strace &>/dev/null; then
        timeout "$DURATION" strace -p "$pid" \
            -e trace=open,openat,read,write,close,lseek,pread64,pwrite64,fsync,fdatasync \
            -c 2>&1 || true
    else
        warning "strace 未安装"
    fi
    echo ""
}

# 采集 IO 延迟信息
collect_io_latency() {
    print_separator "I/O 延迟分析"

    info "iostat 延迟详情（${DURATION}秒采样）"
    if command -v iostat &>/dev/null; then
        iostat -x -t 1 "$DURATION" 2>/dev/null
    else
        warning "iostat 未安装"
    fi
    echo ""

    info "块设备队列参数"
    for disk in /sys/block/sd* /sys/block/vd* /sys/block/nvme*; do
        if [ -d "$disk" ]; then
            local name
            name=$(basename "$disk")
            local nr_requests
            nr_requests=$(cat "$disk/queue/nr_requests" 2>/dev/null || echo "N/A")
            local read_ahead_kb
            read_ahead_kb=$(cat "$disk/queue/read_ahead_kb" 2>/dev/null || echo "N/A")
            local scheduler
            scheduler=$(cat "$disk/queue/scheduler" 2>/dev/null || echo "N/A")
            local max_sectors_kb
            max_sectors_kb=$(cat "$disk/queue/max_sectors_kb" 2>/dev/null || echo "N/A")
            echo "  $name: nr_requests=$nr_requests read_ahead_kb=${read_ahead_kb}KB max_sectors_kb=${max_sectors_kb}KB scheduler=$scheduler"
        fi
    done 2>/dev/null
    echo ""
}

# 采集 blktrace 数据
collect_blktrace() {
    print_separator "blktrace 块设备追踪"

    if ! command -v blktrace &>/dev/null; then
        warning "blktrace 未安装，跳过块设备追踪"
        return
    fi

    if [ "$EUID" -ne 0 ]; then
        warning "blktrace 需要 root 权限，跳过"
        return
    fi

    # 找到第一个有 IO 的块设备
    local target_dev
    target_dev=$(lsblk -d -n -o NAME,TYPE | awk '$2=="disk"{print "/dev/"$1; exit}')
    if [ -z "$target_dev" ]; then
        warning "未找到块设备"
        return
    fi

    info "采集 $target_dev 的块设备 IO 追踪（${DURATION}秒）..."

    local trace_prefix="${REPORT_DIR}/blktrace_$(basename "$target_dev")"

    timeout "$DURATION" blktrace -d "$target_dev" -o "$trace_prefix" 2>/dev/null || true

    if ls "${trace_prefix}".blktrace.* &>/dev/null; then
        info "blkparse 解析结果（最后 30 行）："
        blkparse -i "$trace_prefix" 2>/dev/null | tail -30

        if command -v btt &>/dev/null; then
            info "btt 延迟统计："
            blkparse -i "$trace_prefix" -d "${trace_prefix}.bin" 2>/dev/null
            btt -i "${trace_prefix}.bin" 2>/dev/null | head -40
        fi

        # 清理 blktrace 原始文件（保留 btt 摘要）
        rm -f "${trace_prefix}".blktrace.* "${trace_prefix}".bin 2>/dev/null
    else
        warning "blktrace 未采集到数据"
    fi
    echo ""
}

# 生成报告摘要
generate_summary() {
    print_separator "诊断摘要"

    if [ -n "$TARGET_PID" ]; then
        info "目标进程: PID=$TARGET_PID ($(cat /proc/$TARGET_PID/comm 2>/dev/null || echo '已退出'))"
    fi
    info "采集时长: ${DURATION}秒"
    info "采集时间: $(date '+%Y-%m-%d %H:%M:%S')"
    if [ -n "$REPORT_DIR" ] && [ -d "$REPORT_DIR" ]; then
        info "报告目录: $REPORT_DIR"
    fi

    echo ""
    echo "提示："
    echo "  1. 如需更详细分析，可增大采集时长"
    echo "  2. 使用 bpftrace 可获得更精确的延迟分析（需 TencentOS 3/4）"
    echo "  3. 生产环境建议使用 perf trace 替代 strace（开销更小）"
    echo ""
}

# 主函数
main() {
    info "=== 进程文件 I/O 追踪工具 ==="
    info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    if [ -n "$TARGET_PID" ]; then
        check_process "$TARGET_PID"

        # 创建报告目录
        REPORT_DIR="/tmp/file-io-trace-${TARGET_PID}-$(date +%Y%m%d%H%M%S)"
        mkdir -p "$REPORT_DIR"
        info "报告目录: $REPORT_DIR"

        # 采集数据
        collect_system_overview 2>&1 | tee "$REPORT_DIR/system_overview.txt"
        collect_process_io "$TARGET_PID" 2>&1 | tee "$REPORT_DIR/process_io.txt"
        collect_io_latency 2>&1 | tee "$REPORT_DIR/io_latency.txt"
        collect_blktrace 2>&1 | tee "$REPORT_DIR/blktrace.txt"
        generate_summary 2>&1 | tee "$REPORT_DIR/summary.txt"
    else
        # 无 PID 参数，只显示系统概览
        collect_system_overview
        collect_io_latency
        generate_summary
    fi
}

main "$@"
