#!/bin/bash
#
# sched-latency-monitor.sh — 进程调度延迟长期监控脚本
#
# 用法:
#   nohup bash sched-latency-monitor.sh &
#   # 或指定参数:
#   nohup bash sched-latency-monitor.sh -p <PID> -d 3 -t 5ms &
#
# 说明:
#   此脚本为模板文件，由 sched-latency skill 在步骤 5 中使用。
#   AI 需要根据以下规则定制后输出给用户：
#
#   1. 将 "默认参数" 区域的占位符替换为用户实际值：
#      - <PID>      → 目标进程 PID
#      - <进程名>   → 目标进程名（用于进程重启后自动重新发现）
#      - <天数>     → 监控持续天数（1/3/7）
#      - <阈值>     → 步骤 1.2 中确定的延迟阈值（如 10ms）
#
#   2. start_summary() 和 start_detail() 中的 perf-prof 命令
#      必须替换为步骤 5.2 中验证通过的命令（仅将 -p <PID> 改为 -p "$TARGET_PID"）。
#      如果验证时做了修复调整（如去掉 /stack/、去掉 --detail 等），
#      此处必须与验证通过的版本完全一致。
#

set -o pipefail

# ============================================================
# 默认参数（可通过命令行覆盖）
# ============================================================
TARGET_PID="${TARGET_PID:-}"      # 目标进程 PID（通过 -p 或环境变量传入）
TARGET_COMM="${TARGET_COMM:-}"    # 目标进程名（用于 PID 变化时自动发现）
DURATION_DAYS="${DURATION_DAYS:-1}" # 监控持续天数（1/3/7）
DELAY_THRESHOLD="${DELAY_THRESHOLD:-5}" # 延迟阈值（ms），超过才记录详细信息
LOG_DIR="/var/log/sched-latency-monitor"
INTERVAL=1000                  # 统计输出间隔（毫秒），默认每秒一次
RINGBUF_PAGES=256              # ringbuffer 页数，避免高频场景丢事件

# ============================================================
# 解析命令行参数
# ============================================================
while getopts "p:c:d:t:l:i:m:h" opt; do
    case $opt in
        p) TARGET_PID="$OPTARG" ;;
        c) TARGET_COMM="$OPTARG" ;;
        d) DURATION_DAYS="$OPTARG" ;;
        t) DELAY_THRESHOLD="$OPTARG" ;;
        l) LOG_DIR="$OPTARG" ;;
        i) INTERVAL="$OPTARG" ;;
        m) RINGBUF_PAGES="$OPTARG" ;;
        h)
            echo "用法: $0 [-p PID] [-c 进程名] [-d 天数] [-t 阈值] [-l 日志目录] [-i 间隔ms] [-m ringbuf页数]"
            exit 0
            ;;
        *) echo "未知参数: -$OPTARG"; exit 1 ;;
    esac
done

# ============================================================
# 初始化
# ============================================================
mkdir -p "${LOG_DIR}"

SUMMARY_LOG="${LOG_DIR}/summary.log"          # 每周期的统计摘要
DETAIL_LOG="${LOG_DIR}/detail.log"             # 超阈值的详细事件+调用栈
MONITOR_LOG="${LOG_DIR}/monitor.log"           # 脚本自身运行日志
PID_FILE="${LOG_DIR}/monitor.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${MONITOR_LOG}"
}

# 校验 DURATION_DAYS 为有效正整数
if ! [[ "$DURATION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
    log "错误: DURATION_DAYS 值无效: '${DURATION_DAYS}'（必须为正整数，如 1、3、7）"
    echo "错误: DURATION_DAYS 值无效: '${DURATION_DAYS}'（必须为正整数）" >&2
    echo "提示: 使用 -d 参数指定天数，如: $0 -d 3" >&2
    exit 1
fi

# 校验 DELAY_THRESHOLD 非空且非占位符
if [[ -z "$DELAY_THRESHOLD" || "$DELAY_THRESHOLD" == "<阈值>" ]]; then
    log "错误: DELAY_THRESHOLD 未设置或仍为占位符: '${DELAY_THRESHOLD}'"
    echo "错误: DELAY_THRESHOLD 未设置（必须指定延迟阈值，如 5ms、10ms）" >&2
    echo "提示: 使用 -t 参数指定阈值，如: $0 -t 10ms" >&2
    exit 1
fi

END_TIME=$(( $(date +%s) + DURATION_DAYS * 86400 ))

cleanup() {
    log "收到退出信号，正在停止监控..."
    [[ -n "$PERF_PROF_PID" ]] && kill "$PERF_PROF_PID" 2>/dev/null
    [[ -n "$PERF_PROF_DETAIL_PID" ]] && kill "$PERF_PROF_DETAIL_PID" 2>/dev/null
    rm -f "${PID_FILE}"
    log "监控已停止"
    exit 0
}
trap cleanup SIGTERM SIGINT SIGHUP

# 记录自身 PID，方便后续停止
echo $$ > "${PID_FILE}"

# ============================================================
# 前置检查
# ============================================================
if ! command -v perf-prof &>/dev/null; then
    log "错误: perf-prof 未安装，无法启动监控"
    echo "错误: perf-prof 未安装" >&2
    exit 1
fi

# 如果指定了进程名但没有 PID，自动查找
if [[ -z "$TARGET_PID" || "$TARGET_PID" == "<PID>" ]] && [[ -n "$TARGET_COMM" && "$TARGET_COMM" != "<进程名>" ]]; then
    TARGET_PID=$(pgrep -f "$TARGET_COMM" | head -1)
    if [[ -z "$TARGET_PID" ]]; then
        log "错误: 找不到进程 ${TARGET_COMM}"
        echo "错误: 找不到进程 ${TARGET_COMM}" >&2
        exit 1
    fi
    log "自动发现进程 ${TARGET_COMM} -> PID ${TARGET_PID}"
fi

if ! kill -0 "$TARGET_PID" 2>/dev/null; then
    log "错误: 进程 ${TARGET_PID} 不存在"
    echo "错误: 进程 ${TARGET_PID} 不存在" >&2
    exit 1
fi

TARGET_COMM_REAL=$(cat /proc/${TARGET_PID}/comm 2>/dev/null || echo "unknown")

log "=========================================="
log "调度延迟监控启动"
log "  目标进程: ${TARGET_COMM_REAL} (PID: ${TARGET_PID})"
log "  监控时长: ${DURATION_DAYS} 天 (截止 $(date -d @${END_TIME} '+%Y-%m-%d %H:%M:%S'))"
log "  延迟阈值: ${DELAY_THRESHOLD}"
log "  日志目录: ${LOG_DIR}"
log "  统计间隔: ${INTERVAL}ms"
log "=========================================="

# ============================================================
# 日志轮转：防止日志无限增长
# ============================================================
rotate_log() {
    local logfile="$1"
    local max_size=$((100 * 1024 * 1024))  # 100MB
    if [[ -f "$logfile" ]] && [[ $(stat -c%s "$logfile" 2>/dev/null || echo 0) -gt $max_size ]]; then
        mv "$logfile" "${logfile}.$(date '+%Y%m%d_%H%M%S').bak"
        log "日志轮转: ${logfile}"
    fi
}

# ============================================================
# 启动监控
# ============================================================

#
# 以下两条 perf-prof 命令来自步骤 5.2 的验证结果，已确认可正常工作。
# 如果步骤 5.2 中有修复调整（如去掉 /stack/、去掉 --detail 等），
# 此处的命令必须与验证通过的版本完全一致。
#

# 启动函数：封装命令便于重启
start_summary() {
    perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
        -e sched:sched_switch \
        -p "$TARGET_PID" -i "$INTERVAL" --perins -m "$RINGBUF_PAGES" \
        >> "${SUMMARY_LOG}" 2>> "${MONITOR_LOG}" &
    PERF_PROF_PID=$!
}

start_detail() {
    perf-prof rundelay -e 'sched:sched_wakeup*/stack/,sched:sched_switch//stack/' \
        -e 'sched:sched_switch//stack/' \
        -p "$TARGET_PID" -i "$INTERVAL" --perins -m "$RINGBUF_PAGES" \
        --than "$DELAY_THRESHOLD" --detail=samecpu \
        >> "${DETAIL_LOG}" 2>> "${MONITOR_LOG}" &
    PERF_PROF_DETAIL_PID=$!
}

#
# 通道 1: 统计摘要（持续输出，每 INTERVAL 毫秒一行）
#   使用 --perins 按线程统计，便于后续定位具体线程
#
log "启动统计摘要采集..."
start_summary
log "统计摘要进程 PID: ${PERF_PROF_PID}"

#
# 通道 2: 超阈值详细事件 + 调用栈
#   --than 过滤超阈值事件
#   stack 属性采集唤醒源/抢占源的调用栈
#   --detail=samecpu 输出延迟区间内同 CPU 的中间事件
#
log "启动详细事件采集（阈值: ${DELAY_THRESHOLD}）..."
start_detail
log "详细事件进程 PID: ${PERF_PROF_DETAIL_PID}"

# ============================================================
# 主循环：监控进程存活 + 日志轮转 + 到期退出
# ============================================================
while true; do
    NOW=$(date +%s)

    # 检查是否到期
    if [[ $NOW -ge $END_TIME ]]; then
        log "监控时长已达 ${DURATION_DAYS} 天，正常退出"
        break
    fi

    # 检查目标进程是否还存活
    if ! kill -0 "$TARGET_PID" 2>/dev/null; then
        log "警告: 目标进程 ${TARGET_PID} 已退出"
        # 尝试通过进程名重新发现
        if [[ -n "$TARGET_COMM" && "$TARGET_COMM" != "<进程名>" ]]; then
            NEW_PID=$(pgrep -f "$TARGET_COMM" | head -1)
            if [[ -n "$NEW_PID" ]]; then
                log "重新发现进程 ${TARGET_COMM} -> PID ${NEW_PID}，重启监控..."
                TARGET_PID="$NEW_PID"
                kill "$PERF_PROF_PID" 2>/dev/null
                kill "$PERF_PROF_DETAIL_PID" 2>/dev/null
                sleep 1
                start_summary
                start_detail
                log "监控已用新 PID ${TARGET_PID} 重启"
            else
                log "无法重新发现进程 ${TARGET_COMM}，等待重试..."
            fi
        else
            log "目标进程已退出且无法自动重新发现，继续等待..."
        fi
    fi

    # 检查 perf-prof 进程是否意外退出
    if ! kill -0 "$PERF_PROF_PID" 2>/dev/null; then
        log "警告: 统计摘要采集进程已退出，尝试重启..."
        if kill -0 "$TARGET_PID" 2>/dev/null; then
            start_summary
            log "统计摘要采集已重启 PID: ${PERF_PROF_PID}"
        fi
    fi

    if ! kill -0 "$PERF_PROF_DETAIL_PID" 2>/dev/null; then
        log "警告: 详细事件采集进程已退出，尝试重启..."
        if kill -0 "$TARGET_PID" 2>/dev/null; then
            start_detail
            log "详细事件采集已重启 PID: ${PERF_PROF_DETAIL_PID}"
        fi
    fi

    # 日志轮转检查
    rotate_log "${SUMMARY_LOG}"
    rotate_log "${DETAIL_LOG}"

    sleep 60
done

cleanup
