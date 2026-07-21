#!/bin/bash
#
# network-latency-monitor.sh — 网络丢包和延迟长期监控脚本
#
# 用法:
#   nohup bash network-latency-monitor.sh &
#   # 或指定参数:
#   nohup bash network-latency-monitor.sh -t <目标地址> -d 3 -L 1 -R 50 &
#
# 说明:
#   此脚本为模板文件，由 network-latency skill 在步骤 5 中使用。
#   AI 需要根据以下规则定制后输出给用户：
#
#   1. 将 "默认参数" 区域的占位符替换为用户实际值：
#      - <目标地址>   → 目标 IP 或域名
#      - <天数>       → 监控持续天数（1/3/7）
#      - <丢包阈值>   → 触发告警的丢包率百分比（如 1）
#      - <RTT阈值>    → 触发告警的 RTT 毫秒值（如 50）
#
#   2. collect_ping() 和 trigger_capture() 中的命令
#      必须替换为步骤 5.2 中验证通过的命令。
#

set -o pipefail

# ============================================================
# 默认参数（可通过命令行覆盖）
# ============================================================
TARGET="${TARGET:-}"              # 目标 IP 或域名（必填，通过 -t 或环境变量传入）
DURATION_DAYS="${DURATION_DAYS:-1}"   # 监控持续天数（1/3/7）
LOSS_THRESHOLD="${LOSS_THRESHOLD:-1}" # 丢包率告警阈值（百分比，如 1 表示 1%）
RTT_THRESHOLD="${RTT_THRESHOLD:-50}"  # RTT 告警阈值（毫秒，如 50）
LOG_DIR="/var/log/network-latency-monitor"
PING_INTERVAL=30                 # 主循环间隔（秒）
PING_COUNT=20                    # 每轮 ping 包数
TCP_STATS_INTERVAL=300           # TCP 统计采集间隔（秒，默认 5 分钟）
NIC_STATS_INTERVAL=300           # 网卡统计采集间隔（秒，默认 5 分钟）
CAPTURE_DURATION=30              # 超阈值时 tcpdump 抓包时长（秒）
CAPTURE_MAX_SIZE=$((500 * 1024 * 1024))  # capture 目录最大大小（500MB）
NIC=""                           # 网卡名（留空则自动检测出口网卡）

# ============================================================
# 解析命令行参数
# ============================================================
while getopts "t:d:L:R:l:i:c:n:h" opt; do
    case $opt in
        t) TARGET="$OPTARG" ;;
        d) DURATION_DAYS="$OPTARG" ;;
        L) LOSS_THRESHOLD="$OPTARG" ;;
        R) RTT_THRESHOLD="$OPTARG" ;;
        l) LOG_DIR="$OPTARG" ;;
        i) PING_INTERVAL="$OPTARG" ;;
        c) PING_COUNT="$OPTARG" ;;
        n) NIC="$OPTARG" ;;
        h)
            echo "用法: $0 [-t 目标地址] [-d 天数] [-L 丢包阈值%] [-R RTT阈值ms] [-l 日志目录] [-i 间隔秒] [-c ping包数] [-n 网卡名]"
            exit 0
            ;;
        *) echo "未知参数: -$OPTARG"; exit 1 ;;
    esac
done

# ============================================================
# 初始化
# ============================================================
mkdir -p "${LOG_DIR}/capture"

PING_LOG="${LOG_DIR}/ping_stats.log"
TCP_LOG="${LOG_DIR}/tcp_stats.log"
NIC_LOG="${LOG_DIR}/nic_stats.log"
ALERT_LOG="${LOG_DIR}/alerts.log"
MONITOR_LOG="${LOG_DIR}/monitor.log"
PID_FILE="${LOG_DIR}/monitor.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${MONITOR_LOG}"
}

# 校验 TARGET 非空且非占位符
if [[ -z "$TARGET" || "$TARGET" == "<目标地址>" ]]; then
    log "错误: TARGET 未设置或仍为占位符: '${TARGET}'"
    echo "错误: TARGET 未设置（必须指定目标地址）" >&2
    echo "提示: 使用 -t 参数指定目标，如: $0 -t 10.0.0.1" >&2
    exit 1
fi

# 校验 DURATION_DAYS 为有效正整数
if ! [[ "$DURATION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
    log "错误: DURATION_DAYS 值无效: '${DURATION_DAYS}'（必须为正整数，如 1、3、7）"
    echo "错误: DURATION_DAYS 值无效: '${DURATION_DAYS}'（必须为正整数）" >&2
    echo "提示: 使用 -d 参数指定天数，如: $0 -d 3" >&2
    exit 1
fi

# 校验阈值为有效数字
if ! [[ "$LOSS_THRESHOLD" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    log "错误: LOSS_THRESHOLD 值无效: '${LOSS_THRESHOLD}'"
    echo "错误: LOSS_THRESHOLD 值无效（必须为数字，如 1 表示 1%）" >&2
    exit 1
fi

if ! [[ "$RTT_THRESHOLD" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    log "错误: RTT_THRESHOLD 值无效: '${RTT_THRESHOLD}'"
    echo "错误: RTT_THRESHOLD 值无效（必须为数字，单位毫秒）" >&2
    exit 1
fi

END_TIME=$(( $(date +%s) + DURATION_DAYS * 86400 ))

# 自动检测出口网卡
if [[ -z "$NIC" ]]; then
    NIC=$(ip route get "$TARGET" 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
    if [[ -z "$NIC" ]]; then
        NIC=$(ip route show default 2>/dev/null | awk '/default/ {print $5}' | head -1)
    fi
fi

cleanup() {
    log "收到退出信号，正在停止监控..."
    rm -f "${PID_FILE}"
    log "监控已停止"
    exit 0
}
trap cleanup SIGTERM SIGINT SIGHUP

# 记录自身 PID
echo $$ > "${PID_FILE}"

# ============================================================
# 前置检查
# ============================================================
if ! command -v ping &>/dev/null; then
    log "错误: ping 未安装，无法启动监控"
    echo "错误: ping 未安装" >&2
    exit 1
fi

log "=========================================="
log "网络延迟监控启动"
log "  目标地址: ${TARGET}"
log "  出口网卡: ${NIC:-未检测到}"
log "  监控时长: ${DURATION_DAYS} 天 (截止 $(date -d @${END_TIME} '+%Y-%m-%d %H:%M:%S'))"
log "  丢包阈值: ${LOSS_THRESHOLD}%"
log "  RTT 阈值: ${RTT_THRESHOLD}ms"
log "  日志目录: ${LOG_DIR}"
log "  Ping 间隔: ${PING_INTERVAL}s, 每轮 ${PING_COUNT} 包"
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

# 清理 capture 目录，保持总大小在限制内
cleanup_captures() {
    local total_size
    total_size=$(du -sb "${LOG_DIR}/capture" 2>/dev/null | awk '{print $1}')
    if [[ -n "$total_size" ]] && [[ "$total_size" -gt "$CAPTURE_MAX_SIZE" ]]; then
        log "capture 目录超过 ${CAPTURE_MAX_SIZE} 字节，清理最旧的抓包文件..."
        ls -1t "${LOG_DIR}/capture"/*.pcap 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
        log "capture 清理完成"
    fi
}

# ============================================================
# 数据采集函数
# ============================================================

# 采集 ping 统计，返回丢包率和平均 RTT
collect_ping() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')

    local ping_output
    ping_output=$(ping -c "$PING_COUNT" -i 0.2 -W 3 "$TARGET" 2>&1)
    local rc=$?

    # 解析丢包率
    local loss
    loss=$(echo "$ping_output" | grep -oP '[0-9.]+(?=% packet loss)' || echo "100")

    # 解析 RTT（min/avg/max/mdev）
    local rtt_line
    rtt_line=$(echo "$ping_output" | grep -oP 'rtt min/avg/max/mdev = \K[0-9./]+' || echo "0/0/0/0")
    local rtt_min rtt_avg rtt_max rtt_mdev
    IFS='/' read -r rtt_min rtt_avg rtt_max rtt_mdev <<< "$rtt_line"

    # 写入 ping_stats.log
    echo "${ts} loss=${loss}% min=${rtt_min}ms avg=${rtt_avg}ms max=${rtt_max}ms mdev=${rtt_mdev}ms" >> "${PING_LOG}"

    # 返回丢包率和平均 RTT（供主循环判断阈值）
    echo "${loss} ${rtt_avg}"
}

# 超阈值时触发 tcpdump 短时抓包
trigger_capture() {
    local reason="$1"
    local ts
    ts=$(date '+%Y%m%d_%H%M%S')

    # 记录告警
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: ${reason}" >> "${ALERT_LOG}"
    log "告警触发: ${reason}"

    # 如果 tcpdump 可用，启动短时抓包
    if command -v tcpdump &>/dev/null && [[ -n "$NIC" ]]; then
        local pcap_file="${LOG_DIR}/capture/${ts}.pcap"
        timeout "$CAPTURE_DURATION" tcpdump -i "$NIC" host "$TARGET" -c 10000 -w "$pcap_file" &>/dev/null &
        log "已触发 tcpdump 抓包: ${pcap_file} (${CAPTURE_DURATION}s)"
        cleanup_captures
    fi
}

# 采集 TCP 统计
collect_tcp_stats() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')

    echo "=== ${ts} ===" >> "${TCP_LOG}"

    # ss -tin 到目标地址的连接
    if command -v ss &>/dev/null; then
        ss -tin dst "$TARGET" >> "${TCP_LOG}" 2>/dev/null
    fi

    # /proc/net/snmp TCP 行
    if [[ -f /proc/net/snmp ]]; then
        grep "^Tcp:" /proc/net/snmp >> "${TCP_LOG}" 2>/dev/null
    fi

    echo "" >> "${TCP_LOG}"
}

# 采集网卡统计
collect_nic_stats() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')

    if [[ -z "$NIC" ]]; then
        return
    fi

    echo "=== ${ts} ===" >> "${NIC_LOG}"

    # ethtool -S 非零错误计数
    if command -v ethtool &>/dev/null; then
        ethtool -S "$NIC" 2>/dev/null | grep -iE "error|drop|miss|fifo|crc" | grep -v ": 0$" >> "${NIC_LOG}" 2>/dev/null
    fi

    # ip -s link
    ip -s link show "$NIC" >> "${NIC_LOG}" 2>/dev/null

    echo "" >> "${NIC_LOG}"
}

# ============================================================
# 主循环：ping 测量 + 按需触发 + 定期采集 + 到期退出
# ============================================================
LAST_TCP_COLLECT=0
LAST_NIC_COLLECT=0

while true; do
    NOW=$(date +%s)

    # 检查是否到期
    if [[ $NOW -ge $END_TIME ]]; then
        log "监控时长已达 ${DURATION_DAYS} 天，正常退出"
        break
    fi

    # 1. 采集 ping 统计
    read -r LOSS AVG_RTT <<< "$(collect_ping)"

    # 2. 判断是否超阈值，触发抓包
    if [[ -n "$LOSS" ]] && (( $(echo "$LOSS > $LOSS_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
        trigger_capture "丢包率 ${LOSS}% 超过阈值 ${LOSS_THRESHOLD}%"
    fi

    if [[ -n "$AVG_RTT" ]] && [[ "$AVG_RTT" != "0" ]] && (( $(echo "$AVG_RTT > $RTT_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
        trigger_capture "平均 RTT ${AVG_RTT}ms 超过阈值 ${RTT_THRESHOLD}ms"
    fi

    # 3. 定期采集 TCP 统计
    if [[ $((NOW - LAST_TCP_COLLECT)) -ge $TCP_STATS_INTERVAL ]]; then
        collect_tcp_stats
        LAST_TCP_COLLECT=$NOW
    fi

    # 4. 定期采集网卡统计
    if [[ $((NOW - LAST_NIC_COLLECT)) -ge $NIC_STATS_INTERVAL ]]; then
        collect_nic_stats
        LAST_NIC_COLLECT=$NOW
    fi

    # 5. 日志轮转检查
    rotate_log "${PING_LOG}"
    rotate_log "${TCP_LOG}"
    rotate_log "${NIC_LOG}"
    rotate_log "${ALERT_LOG}"

    sleep "$PING_INTERVAL"
done

cleanup
