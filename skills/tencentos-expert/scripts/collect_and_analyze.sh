#!/usr/bin/env bash
# collect_and_analyze.sh — OOM Killer 事件排查入口脚本
#
# 用法:
#   bash collect_and_analyze.sh [选项]
#   bash collect_and_analyze.sh -f /var/log/messages
#   bash collect_and_analyze.sh -f /var/log/messages -o /tmp/oom-report
#
# 选项:
#   -f <path>   日志文件路径（可选，默认自动查找本机系统日志）
#   -o <dir>    输出目录（可选，默认当前目录）
#   -t <id>     任务 ID（可选，默认 unknown）
#   -h          显示帮助信息
#
set -uo pipefail

# ============================================================
# 引入公共函数库
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMON_SH="${SCRIPT_DIR}/../../../shared/utils/common.sh"
OUTPUT_SH="${SCRIPT_DIR}/../../../shared/utils/output.sh"

if [ -f "$COMMON_SH" ]; then
    source "$COMMON_SH"
else
    # 内置基础函数（独立运行时使用）
    info()    { echo "[INFO] $*"; }
    success() { echo "[SUCCESS] $*"; }
    warning() { echo "[WARNING] $*" >&2; }
    error()   { echo "[ERROR] $*" >&2; }
fi

if [ -f "$OUTPUT_SH" ]; then
    source "$OUTPUT_SH"
fi

# ============================================================
# 默认参数
# ============================================================
LOG_FILE=""
LOG_DIR="."
TASK_ID="unknown"

# ============================================================
# 使用说明
# ============================================================
usage() {
    cat << 'EOF'
用法: collect_and_analyze.sh [选项]

OOM Killer 事件排查 — 分析系统日志中的 OOM 事件，输出结构化诊断报告。

选项:
  -f <path>   日志文件路径（可选，默认自动查找本机系统日志）
              支持 /var/log/messages、/var/log/syslog、/var/log/kern.log
  -o <dir>    输出目录（可选，默认当前目录）
              分析结果将写入该目录下的 summary.json 和 raw/ 子目录
  -t <id>     任务 ID（可选，默认 unknown）
  -h          显示此帮助信息

示例:
  # 自动查找本机系统日志进行分析
  bash collect_and_analyze.sh

  # 指定日志文件
  bash collect_and_analyze.sh -f /var/log/messages

  # 指定日志文件和输出目录
  bash collect_and_analyze.sh -f /var/log/messages -o /tmp/oom-report

  # 完整参数
  bash collect_and_analyze.sh -f /var/log/messages -o /tmp/oom-report -t task-001
EOF
}

# ============================================================
# 解析命令行参数
# ============================================================
while getopts "f:o:t:h" opt; do
    case $opt in
        f) LOG_FILE="$OPTARG" ;;
        o) LOG_DIR="$OPTARG" ;;
        t) TASK_ID="$OPTARG" ;;
        h) usage; exit 0 ;;
        *) usage; exit 1 ;;
    esac
done

mkdir -p "${LOG_DIR}/raw"

echo "=== oom-killer 开始（任务: ${TASK_ID}）==="

# ============================================================
# 确定日志文件路径
# ============================================================
if [ -z "${LOG_FILE}" ]; then
    info "未指定 -f <log_file>，自动查找本机系统日志..."
    for candidate in /var/log/messages /var/log/syslog /var/log/kern.log; do
        if [ -f "${candidate}" ] && [ -s "${candidate}" ]; then
            LOG_FILE="${candidate}"
            info "使用本机日志: ${LOG_FILE}"
            break
        fi
    done

    if [ -z "${LOG_FILE}" ]; then
        error "未找到可用的系统日志文件（已检查: /var/log/messages, /var/log/syslog, /var/log/kern.log）"
        error "请通过 -f <路径> 指定日志文件"
        python3 - "${TASK_ID}" "${LOG_DIR}" <<'PYEOF'
import json, datetime, sys
summary = {
    "task_id": sys.argv[1],
    "status": "failed",
    "finished_at": datetime.datetime.now().isoformat(),
    "key_findings": ["未找到系统日志文件，请通过 -f <路径> 指定"],
    "oom_event_count": 0,
}
with open(f"{sys.argv[2]}/summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
PYEOF
        exit 1
    fi
fi

# 校验日志文件存在
if [ ! -f "${LOG_FILE}" ]; then
    error "日志文件不存在: ${LOG_FILE}"
    exit 1
fi

info "分析日志文件: ${LOG_FILE}"

# ============================================================
# 快速检查 & 解析
# ============================================================

# 快速检查文件是否含 OOM 关键词
OOM_LINES=$(grep -c -iE "oom.killer|out of memory|Killed process|Memory cgroup" "${LOG_FILE}" 2>/dev/null) || OOM_LINES=0
info "OOM 相关行数: ${OOM_LINES}"

# 复制原始日志到归档目录
cp "${LOG_FILE}" "${LOG_DIR}/raw/input.log"

# 执行解析
info "执行 OOM 事件解析..."
python3 "${SCRIPT_DIR}/parse_oom_events.py" \
    --log-file "${LOG_FILE}" \
    --output "${LOG_DIR}/raw/oom_events.json" \
    --pretty \
    2>&1 | tee "${LOG_DIR}/raw/parse.log"
PARSE_EXIT=${PIPESTATUS[0]}

# ============================================================
# 生成 summary.json
# ============================================================
python3 - "${LOG_DIR}" "${TASK_ID}" "${LOG_FILE}" "${OOM_LINES:-0}" "${PARSE_EXIT:-1}" <<'PYEOF'
import json, datetime, os, sys
from pathlib import Path

log_dir = Path(sys.argv[1])
task_id = sys.argv[2]
log_file = sys.argv[3]
try:
    oom_lines = int(sys.argv[4].strip().splitlines()[0])
except (ValueError, IndexError):
    oom_lines = 0
try:
    parse_exit = int(sys.argv[5].strip())
except (ValueError, IndexError):
    parse_exit = 1

events_path = log_dir / "raw" / "oom_events.json"
oom_events = []
oom_count = 0

if events_path.exists():
    try:
        data = json.loads(events_path.read_text())
        oom_events = data.get("oom_events", [])
        oom_count = len(oom_events)
    except Exception:
        pass

key_findings = []
if oom_count == 0 and oom_lines == 0:
    key_findings.append("未发现 OOM 事件，系统内存状态正常")
elif oom_count == 0 and oom_lines > 0:
    key_findings.append(f"检测到 {oom_lines} 行 OOM 相关日志，但结构化解析未提取到完整事件（可能是日志不完整）")
else:
    for ev in oom_events[:3]:
        killed = ev.get("killed_name", "未知")
        rss_mb = ev.get("killed_rss_kb", 0) // 1024
        trigger_time = ev.get("trigger_time", "未知时间")
        key_findings.append(f"OOM 事件: {trigger_time} - 进程 {killed} 被 Kill（RSS {rss_mb}MB）")
    if oom_count > 3:
        key_findings.append(f"共发现 {oom_count} 次 OOM 事件，详情见 raw/oom_events.json")

summary = {
    "task_id": task_id,
    "status": "completed" if parse_exit == 0 else "failed",
    "finished_at": datetime.datetime.now().isoformat(),
    "log_file": log_file,
    "oom_event_count": oom_count,
    "oom_related_lines": oom_lines,
    "key_findings": key_findings,
    "events_file": str(events_path) if events_path.exists() else None,
}

(log_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(f"summary.json 已生成: {log_dir}/summary.json")
PYEOF

echo "=== oom-killer 完成 ==="
