#!/usr/bin/env bash
# collect_memory_leak.sh — Linux 用户态内存泄漏数据采集
#
# 用法:
#   bash collect_memory_leak.sh [选项]
#
# 选项:
#   -p <pid>          目标进程 PID（优先于 -n）
#   -n <name>         目标进程名，模糊匹配（如 java、nginx）
#   -c <count>        采样次数（默认 6）
#   -i <interval>     采样间隔秒数（默认 10）
#   -t <top_n>        全局扫描显示 Top N 进程（默认 5）
#   -o <log_dir>      日志输出目录（默认 /tmp/memory-leak-<timestamp>）
#   -j <task_id>      任务 ID，写入 summary.json（默认自动生成）
#   -h                显示帮助
#
# 示例:
#   bash collect_memory_leak.sh -p 1234
#   bash collect_memory_leak.sh -n java -c 10 -i 30
#   bash collect_memory_leak.sh -o /var/log/memleak -j task_001
#
set -euo pipefail

# ── 参数解析（命令行优先，环境变量兜底，最后取默认值）────────────────────────

usage() {
    grep '^#' "$0" | grep -v '#!/' | sed 's/^# \{0,2\}//'
    exit 0
}

TARGET_PID=""
PROCESS_NAME=""
MONITOR_COUNT=""
MONITOR_INTERVAL=""
TOP_N=""
LOG_DIR=""
TASK_ID=""

while getopts ":p:n:c:i:t:o:j:h" opt; do
    case "${opt}" in
        p) TARGET_PID="${OPTARG}" ;;
        n) PROCESS_NAME="${OPTARG}" ;;
        c) MONITOR_COUNT="${OPTARG}" ;;
        i) MONITOR_INTERVAL="${OPTARG}" ;;
        t) TOP_N="${OPTARG}" ;;
        o) LOG_DIR="${OPTARG}" ;;
        j) TASK_ID="${OPTARG}" ;;
        h) usage ;;
        :) echo "错误: 选项 -${OPTARG} 需要参数" >&2; exit 1 ;;
        \?) echo "错误: 未知选项 -${OPTARG}" >&2; exit 1 ;;
    esac
done

TARGET_PID="${TARGET_PID:-}"
PROCESS_NAME="${PROCESS_NAME:-}"
MONITOR_COUNT="${MONITOR_COUNT:-6}"
MONITOR_INTERVAL="${MONITOR_INTERVAL:-10}"
TOP_N="${TOP_N:-5}"
LOG_DIR="${LOG_DIR:-/tmp/memory-leak-$(date +%Y%m%d_%H%M%S)}"
TASK_ID="${TASK_ID:-$(date +%Y%m%d_%H%M%S)}"

# 参数合法性校验
if [[ "${MONITOR_INTERVAL}" -lt 1 ]]; then
    warning "monitor_interval < 1，已修正为 1s"
    MONITOR_INTERVAL=1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 引入公共函数库 ────────────────────────────────────────────────────────────
COMMON_SH="${SCRIPT_DIR}/../../../shared/utils/common.sh"
if [ -f "${COMMON_SH}" ]; then
    source "${COMMON_SH}"
else
    echo "[ERROR] 公共函数库不存在: ${COMMON_SH}" >&2
    exit 1
fi

mkdir -p "${LOG_DIR}/raw" || { error "无法创建日志目录: ${LOG_DIR}/raw"; exit 1; }

info "开始内存泄漏诊断, task=${TASK_ID}"

# ── 步骤 1：确定监控模式和目标 PID ──────────────────────────────────────────

MODE="global"  # global | process

if [ -n "${TARGET_PID}" ]; then
    MODE="process"
    info "模式: 单进程监控 (PID=${TARGET_PID})"
elif [ -n "${PROCESS_NAME}" ]; then
    MODE="process"
    # 根据进程名查找 PID（取 RSS 最大的那个，排除 grep/awk 自身）
    TARGET_PID=$(ps -eo pid,rss,comm --no-headers 2>/dev/null \
        | awk -v name="${PROCESS_NAME}" '$3 ~ name && $3 !~ /^(awk|grep|ps)$/ {print $1, $2}' \
        | sort -k2 -rn \
        | awk '{print $1; exit}')
    if [ -z "${TARGET_PID}" ]; then
        warning "未找到进程: ${PROCESS_NAME}，切换为全局扫描模式"
        MODE="global"
    else
        info "模式: 单进程监控 (process_name=${PROCESS_NAME}, PID=${TARGET_PID})"
    fi
else
    info "模式: 全局扫描 (Top ${TOP_N})"
fi

# ── 步骤 2：写入本次运行的元信息 ──────────────────────────────────────────────

cat > "${LOG_DIR}/raw/config.json" <<CONFIGEOF
{
  "mode": "${MODE}",
  "target_pid": "${TARGET_PID}",
  "process_name": "${PROCESS_NAME}",
  "monitor_count": ${MONITOR_COUNT},
  "monitor_interval": ${MONITOR_INTERVAL},
  "top_n": ${TOP_N},
  "task_id": "${TASK_ID}"
}
CONFIGEOF

# ── 步骤 3：采集一次性数据（slab、dmesg）──────────────────────────────────────

info "采集内核 slab 信息..."
{
    echo "=== /proc/slabinfo (前30行) ==="
    head -30 /proc/slabinfo 2>/dev/null || echo "(不可读)"
} > "${LOG_DIR}/raw/slabinfo.log"

info "采集 dmesg OOM 信息..."
{
    dmesg 2>/dev/null \
        | grep -i -E "oom|out of memory|killed process|memory cgroup" \
        | tail -50 \
        || echo "(未发现 OOM 关键字)"
} > "${LOG_DIR}/raw/dmesg_oom.log" 2>/dev/null || true

# 采集全局 meminfo（用于 OOM 预测基线）
cat /proc/meminfo > "${LOG_DIR}/raw/meminfo_baseline.log" 2>/dev/null || true

# ── 步骤 4：函数：采集单个进程快照 ───────────────────────────────────────────

collect_process_snapshot() {
    local pid="$1"
    local out_file="$2"
    local ts
    ts=$(date +%s)

    # 从 /proc/<pid>/status 读取关键字段
    local vm_rss=0 vm_anon=0 vm_peak=0 vm_size=0 proc_name="unknown"
    if [ -r "/proc/${pid}/status" ]; then
        while IFS=: read -r key val; do
            # 清除 tab、空格和 "kB" 单位（/proc/status 值字段带 tab 前缀）
            val="${val//$'\t'/}"
            val="${val// /}"
            val="${val//kB/}"
            case "${key}" in
                Name)    proc_name="${val}" ;;
                VmRSS)   vm_rss="${val:-0}" ;;
                VmPeak)  vm_peak="${val:-0}" ;;
                VmSize)  vm_size="${val:-0}" ;;
                RssAnon) vm_anon="${val:-0}" ;;
            esac
        done < "/proc/${pid}/status"
    else
        echo "{\"error\": \"pid ${pid} 不存在或无权限\", \"ts\": ${ts}}" > "${out_file}"
        return 1
    fi

    # 从 /proc/<pid>/smaps_rollup 读取 Pss 和 Private_Dirty（优先）
    # 降级到 smaps 累加（内核 < 4.14 不支持 smaps_rollup）
    local pss=0 private_dirty=0
    if [ -r "/proc/${pid}/smaps_rollup" ]; then
        while IFS=: read -r key val; do
            val="${val//$'\t'/}"
            val="${val// /}"
            val="${val//kB/}"
            case "${key}" in
                Pss)           pss="${val:-0}" ;;
                Private_Dirty) private_dirty="${val:-0}" ;;
            esac
        done < "/proc/${pid}/smaps_rollup"
    elif [ -r "/proc/${pid}/smaps" ]; then
        pss=$(awk '/^Pss:/{sum+=$2} END{print sum+0}' "/proc/${pid}/smaps" 2>/dev/null || echo 0)
        private_dirty=$(awk '/^Private_Dirty:/{sum+=$2} END{print sum+0}' "/proc/${pid}/smaps" 2>/dev/null || echo 0)
    fi

    # 统计文件描述符数量
    local fd_count=0
    if [ -d "/proc/${pid}/fd" ]; then
        fd_count=$(ls -1 "/proc/${pid}/fd" 2>/dev/null | wc -l || echo 0)
    fi

    # 输出 JSON 快照
    cat > "${out_file}" <<SNAPEOF
{
  "pid": ${pid},
  "name": "${proc_name}",
  "ts": ${ts},
  "vm_rss_kb": ${vm_rss:-0},
  "vm_anon_kb": ${vm_anon:-0},
  "vm_peak_kb": ${vm_peak:-0},
  "vm_size_kb": ${vm_size:-0},
  "pss_kb": ${pss:-0},
  "private_dirty_kb": ${private_dirty:-0},
  "fd_count": ${fd_count}
}
SNAPEOF
}

# ── 步骤 5：函数：采集全局进程 RSS 快照 ──────────────────────────────────────
# 用 Python 生成 JSON，避免 shell while 管道子进程变量作用域导致格式错误

collect_global_snapshot() {
    local out_file="$1"
    local ts
    ts=$(date +%s)

    # 采集进程列表（RSS > 1MB），用制表符分隔，输出到临时文件
    local tmp_procs
    tmp_procs=$(mktemp)
    ps -eo pid,rss,comm --no-headers 2>/dev/null \
        | awk '$2 > 1024 {print $1"\t"$2"\t"$3}' \
        | sort -k2 -rn \
        | head -100 > "${tmp_procs}" || true

    # 用 Python 将 TSV 转为合法 JSON
    python3 - "${tmp_procs}" "${ts}" "${out_file}" <<'PYEOF'
import sys, json
procs_file, ts_str, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
processes = []
with open(procs_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t', 2)
        if len(parts) == 3:
            try:
                processes.append({"pid": int(parts[0]), "rss_kb": int(parts[1]), "name": parts[2]})
            except ValueError:
                pass
result = {"ts": int(ts_str), "processes": processes}
with open(out_file, 'w') as f:
    json.dump(result, f, ensure_ascii=False)
PYEOF
    rm -f "${tmp_procs}"
}

# ── 步骤 6：查找 eBPF memleak 并在采样开始前并行启动 ─────────────────────────

MEMLEAK_BIN=""
for candidate in \
    /usr/share/bcc/tools/memleak \
    /usr/bin/memleak \
    /usr/local/bin/memleak \
    /usr/share/bcc/tools/memleak-bpfcc; do
    if [ -x "${candidate}" ]; then
        MEMLEAK_BIN="${candidate}"
        break
    fi
done

# 实际 elapsed = (count-1) * interval（最后一次采样后不 sleep）
ELAPSED_SEC=$(( (MONITOR_COUNT - 1) * MONITOR_INTERVAL ))
# eBPF 追踪时长覆盖整个采样窗口，最少 30s
EBPF_DURATION=$(( ELAPSED_SEC > 30 ? ELAPSED_SEC : 30 ))

MEMLEAK_PID=""
if [ -n "${MEMLEAK_BIN}" ] && [ "${MODE}" = "process" ] && [ -n "${TARGET_PID}" ]; then
    info "并行启动 eBPF memleak（追踪 ${EBPF_DURATION}s，与采样同步）..."
    timeout $(( EBPF_DURATION + 5 )) "${MEMLEAK_BIN}" \
        -p "${TARGET_PID}" --top 10 "${EBPF_DURATION}" \
        > "${LOG_DIR}/raw/memleak_stack.log" 2>&1 &
    MEMLEAK_PID=$!
elif [ "${MODE}" = "process" ]; then
    warning "memleak 未安装，跳过 eBPF 调用栈采集（基础诊断仍有效）"
fi

# ── 步骤 7：多次采样循环 ──────────────────────────────────────────────────────

info "开始采样: ${MONITOR_COUNT} 次，间隔 ${MONITOR_INTERVAL}s（预计 ${ELAPSED_SEC}s）"

for i in $(seq 1 "${MONITOR_COUNT}"); do
    info "采样 ${i}/${MONITOR_COUNT}..."

    if [ "${MODE}" = "process" ] && [ -n "${TARGET_PID}" ]; then
        SNAP_FILE="${LOG_DIR}/raw/sample_${i}.json"
        if ! collect_process_snapshot "${TARGET_PID}" "${SNAP_FILE}"; then
            warning "进程 ${TARGET_PID} 已消失，停止采样"
            break
        fi
    else
        collect_global_snapshot "${LOG_DIR}/raw/global_sample_${i}.json"
    fi

    # 同步采集全局 meminfo（供 OOM 预测用）
    cat /proc/meminfo > "${LOG_DIR}/raw/meminfo_${i}.log" 2>/dev/null || true

    if [ "${i}" -lt "${MONITOR_COUNT}" ]; then
        sleep "${MONITOR_INTERVAL}"
    fi
done

info "采样完成"

# ── 步骤 8：等待 eBPF memleak 完成 ──────────────────────────────────────────

if [ -n "${MEMLEAK_PID}" ]; then
    info "等待 eBPF memleak 结束..."
    wait "${MEMLEAK_PID}" 2>/dev/null || true
    if [ -s "${LOG_DIR}/raw/memleak_stack.log" ] && \
       [ "$(wc -c < "${LOG_DIR}/raw/memleak_stack.log")" -ge 50 ]; then
        info "eBPF 调用栈采集完成"
    else
        rm -f "${LOG_DIR}/raw/memleak_stack.log"
        info "eBPF 无有效输出，已跳过"
    fi
fi

# ── 步骤 9：调用解析脚本生成 summary.json ────────────────────────────────────

info "开始解析数据..."
PARSE_SCRIPT="${SCRIPT_DIR}/parse_memory_leak.py"
if [ -f "${PARSE_SCRIPT}" ]; then
    python3 "${PARSE_SCRIPT}" \
        --log-dir "${LOG_DIR}" \
        --task-id "${TASK_ID}" \
        --top-n "${TOP_N}" \
        --elapsed-sec "${ELAPSED_SEC}" \
        && info "summary.json 已生成: ${LOG_DIR}/summary.json" \
        || warning "解析脚本执行失败"
else
    warning "parse_memory_leak.py 不存在，跳过解析"
fi

info "全部完成"
