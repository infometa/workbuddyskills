#!/bin/bash
# fs-latency-collect.sh
# 文件系统延迟分析 - 一键信息采集脚本
# 用法: ./fs-latency-collect.sh [--deep] [--duration <seconds>] [--device <dev>]
#
# --deep       启用深度分析（需要 blktrace/perf/bcc-tools）
# --duration   采集持续时间，默认 10 秒
# --device     指定磁盘设备（如 sda），默认分析所有设备
#
# 首次使用请先运行依赖安装脚本:
#   bash scripts/install-deps.sh --all
# 或单独安装: --bcc (bcc-tools) / --cflow (cflow) / --fix-tops (修复 t-ops)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMON_SH="${SCRIPT_DIR}/../../../shared/utils/common.sh"
OUTPUT_SH="${SCRIPT_DIR}/../../../shared/utils/output.sh"

# 引入公共函数（如果存在）
[ -f "$COMMON_SH" ] && source "$COMMON_SH"
[ -f "$OUTPUT_SH" ] && source "$OUTPUT_SH"

# ============ 默认参数 ============
DEEP_MODE=false
DURATION=10
TARGET_DEVICE=""
OUTPUT_DIR="/tmp/fs-latency-$(date +%Y%m%d_%H%M%S)"

# ============ 颜色定义（fallback） ============
if ! type info &>/dev/null; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
    success() { echo -e "${GREEN}[OK]${NC} $*"; }
    warning() { echo -e "${YELLOW}[WARN]${NC} $*"; }
    error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fi

# ============ 参数解析 ============
while [[ $# -gt 0 ]]; do
    case $1 in
        --deep)     DEEP_MODE=true; shift ;;
        --duration) DURATION=$2; shift 2 ;;
        --device)   TARGET_DEVICE=$2; shift 2 ;;
        --help|-h)
            echo "用法: $0 [--deep] [--duration <seconds>] [--device <dev>]"
            echo ""
            echo "  --deep       启用深度分析（需要 blktrace/perf/bcc-tools）"
            echo "  --duration   采集持续时间，默认 10 秒"
            echo "  --device     指定磁盘设备（如 sda），默认分析所有设备"
            exit 0
            ;;
        *) error "未知参数: $1"; exit 1 ;;
    esac
done

# ============ 权限检查 ============
if [ "$EUID" -ne 0 ]; then
    error "此脚本需要 root 权限运行"
    exit 1
fi

# ============ 创建输出目录 ============
mkdir -p "$OUTPUT_DIR"
REPORT_FILE="$OUTPUT_DIR/report.txt"

# 同时输出到终端和文件
exec > >(tee -a "$REPORT_FILE") 2>&1

echo "========================================"
echo "  文件系统延迟分析报告"
echo "  采集时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  主机名: $(hostname)"
echo "  内核版本: $(uname -r)"
echo "  采集时长: ${DURATION}s"
echo "========================================"
echo ""

# ============ 步骤 1：文件系统基础信息 ============
info "步骤 1/7: 收集文件系统基础信息"
echo ""
echo "--- 文件系统使用率 ---"
df -hT 2>/dev/null
echo ""

echo "--- inode 使用率 ---"
df -i 2>/dev/null
echo ""

echo "--- 挂载参数 ---"
findmnt -t ext4,xfs,btrfs,ext3 -o TARGET,SOURCE,FSTYPE,OPTIONS 2>/dev/null || mount | grep "^/dev"
echo ""

# ============ 步骤 2：块设备信息 ============
info "步骤 2/7: 收集块设备信息"
echo ""
echo "--- 块设备列表 ---"
lsblk -o NAME,FSTYPE,SIZE,RO,TYPE,MOUNTPOINT 2>/dev/null
echo ""

echo "--- I/O 调度器 ---"
for dev in /sys/block/*/queue/scheduler; do
    devname=$(echo "$dev" | cut -d/ -f4)
    echo "$devname: $(cat "$dev" 2>/dev/null)"
done
echo ""

echo "--- 队列深度 ---"
for dev in /sys/block/*/queue/nr_requests; do
    devname=$(echo "$dev" | cut -d/ -f4)
    echo "$devname: $(cat "$dev" 2>/dev/null)"
done
echo ""

# ============ 步骤 3：iostat 采集 ============
info "步骤 3/7: 采集 I/O 性能数据（${DURATION}s）"
echo ""
if command -v iostat &>/dev/null; then
    echo "--- iostat 扩展信息 ---"
    iostat -x -t 1 "$DURATION"
    echo ""
else
    warning "iostat 未安装，请安装 sysstat 包: yum install -y sysstat"
fi

# ============ 步骤 4：脏页分析 ============
info "步骤 4/7: 分析脏页回写压力"
echo ""
echo "--- 脏页参数 ---"
sysctl vm.dirty_ratio vm.dirty_background_ratio vm.dirty_expire_centisecs vm.dirty_writeback_centisecs 2>/dev/null
echo ""

echo "--- 脏页变化趋势（5s） ---"
printf "%-10s %-12s %-12s\n" "时间" "dirty(pages)" "writeback(pages)"
for i in $(seq 1 5); do
    dirty=$(awk '/nr_dirty / {print $2}' /proc/vmstat)
    writeback=$(awk '/nr_writeback / {print $2}' /proc/vmstat)
    printf "%-10s %-12s %-12s\n" "$(date +%H:%M:%S)" "$dirty" "$writeback"
    sleep 1
done
echo ""

# ============ 步骤 5：文件系统错误检查 ============
info "步骤 5/7: 检查文件系统错误日志"
echo ""
echo "--- ext4 错误 ---"
dmesg | grep -i -E "ext4.*(error|warning|corrupt|abort|remount)" | tail -10 || echo "(无)"
echo ""

echo "--- xfs 错误 ---"
dmesg | grep -i -E "xfs.*(error|warning|corrupt|shutdown|force)" | tail -10 || echo "(无)"
echo ""

echo "--- I/O 错误 ---"
dmesg | grep -i -E "I/O error|buffer_io_error|blk_update_request.*error" | tail -10 || echo "(无)"
echo ""

echo "--- 文件系统只读重挂载 ---"
dmesg | grep -i "remount.*read-only" | tail -5 || echo "(无)"
echo ""

# ============ 步骤 6：碎片化检测 ============
info "步骤 6/7: 文件系统碎片化检测"
echo ""

# 检测 ext4 碎片化
for mp in $(findmnt -t ext4 -n -o TARGET 2>/dev/null); do
    if command -v e4defrag &>/dev/null; then
        echo "--- ext4 碎片化: $mp ---"
        e4defrag -c "$mp" 2>/dev/null | tail -5
        echo ""
    fi
done

# 检测 xfs 碎片化
for dev in $(findmnt -t xfs -n -o SOURCE 2>/dev/null); do
    if command -v xfs_db &>/dev/null; then
        echo "--- xfs 碎片化: $dev ---"
        xfs_db -r -c frag "$dev" 2>/dev/null
        echo ""
    fi
done

if ! command -v e4defrag &>/dev/null && ! command -v xfs_db &>/dev/null; then
    warning "碎片化检测工具不可用（e4defrag / xfs_db）"
fi

# ============ 步骤 7：进程级 I/O（可选） ============
info "步骤 7/7: 进程级 I/O 分析"
echo ""
if command -v pidstat &>/dev/null; then
    echo "--- pidstat I/O Top（3s 采样） ---"
    pidstat -d 1 3
    echo ""
elif command -v iotop &>/dev/null; then
    echo "--- iotop 快照 ---"
    iotop -o -b -n 3 2>/dev/null
    echo ""
else
    warning "pidstat/iotop 均不可用，跳过进程级分析"
fi

# ============ 深度分析（可选） ============
if [ "$DEEP_MODE" = true ]; then
    echo ""
    echo "========================================"
    echo "  深度分析模式"
    echo "========================================"
    echo ""

    # biolatency
    if command -v biolatency &>/dev/null || command -v biolatency-bpfcc &>/dev/null; then
        BIOLATENCY=$(command -v biolatency 2>/dev/null || command -v biolatency-bpfcc)
        info "采集块设备 I/O 延迟分布（${DURATION}s）"
        echo "--- biolatency ---"
        timeout "$DURATION" "$BIOLATENCY" "$DURATION" 1 2>/dev/null || true
        echo ""
    fi

    # ext4slower
    if command -v ext4slower &>/dev/null || command -v ext4slower-bpfcc &>/dev/null; then
        EXT4SLOWER=$(command -v ext4slower 2>/dev/null || command -v ext4slower-bpfcc)
        info "追踪 ext4 慢操作 >10ms（${DURATION}s）"
        echo "--- ext4slower ---"
        timeout "$DURATION" "$EXT4SLOWER" 10 2>/dev/null || true
        echo ""
    fi

    # fileslower
    if command -v fileslower &>/dev/null || command -v fileslower-bpfcc &>/dev/null; then
        FILESLOWER=$(command -v fileslower 2>/dev/null || command -v fileslower-bpfcc)
        info "追踪所有文件系统慢操作 >10ms（${DURATION}s）"
        echo "--- fileslower ---"
        timeout "$DURATION" "$FILESLOWER" 10 2>/dev/null || true
        echo ""
    fi

    # blktrace
    if command -v blktrace &>/dev/null && [ -n "$TARGET_DEVICE" ]; then
        info "采集 blktrace 数据: /dev/$TARGET_DEVICE（${DURATION}s）"
        TRACE_DIR="$OUTPUT_DIR/blktrace"
        mkdir -p "$TRACE_DIR"
        blktrace -d "/dev/$TARGET_DEVICE" -w "$DURATION" -o "$TRACE_DIR/trace" 2>/dev/null || true
        if command -v blkparse &>/dev/null; then
            blkparse -i "$TRACE_DIR/trace" -d "$TRACE_DIR/trace.bin" > "$TRACE_DIR/blkparse.txt" 2>/dev/null || true
            if command -v btt &>/dev/null; then
                btt -i "$TRACE_DIR/trace.bin" > "$TRACE_DIR/btt.txt" 2>/dev/null || true
                echo "--- btt 分析摘要 ---"
                head -50 "$TRACE_DIR/btt.txt" 2>/dev/null
            fi
        fi
        echo ""
    fi
fi

# ============ 摘要 ============
echo ""
echo "========================================"
echo "  采集完成"
echo "========================================"
echo ""
echo "报告已保存到: $OUTPUT_DIR/report.txt"
echo ""
echo "提示: 将此报告内容提供给 AI 进行分析，即可获得详细的诊断结果和优化建议。"
echo ""
echo "如需深度分析，请使用: $0 --deep --device <设备名>"
