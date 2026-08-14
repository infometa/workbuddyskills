#!/usr/bin/env bash
# ============================================================
# agent-boost prod-deploy — 生产环境部署脚本
#
# 在生产容器内执行，完成：
#   1. 启动 MCP Bridge（固定端口 9999）
#   2. 注册 Agent 到生产 agent-server（通过 X-Staff-Name header 认证）
#
# 生产环境 MCP 域名规则：
#   http://{project_id}-internal-mcp-service.prod.hrainative.woa.com/mcp
#   该域名预先配置，固定指向容器 9999 端口，无需 register-mcp-svr。
#
# 用法:
#   bash prod-deploy.sh
#
# 环境变量:
#   PROJECT_DIR       (可选) 项目根目录，默认当前目录
#   APP_PORT          (可选) 应用端口，默认 3000
#   PROD_AGENT_SERVER (可选) 生产 agent-server 地址，默认 http://agent-server.prod.hrainative.woa.com
#
# 前置条件:
#   - .agent/boost-state.json 存在（含 agentName, projectId, staffName）
#   - mcp_server/ 目录存在（含 mcp_bridge.py）
#   - 容器内已安装 python3, pm2
# ============================================================
set -euo pipefail
source "$(dirname "$0")/_env.sh"   # PROD_AGENT_SERVER_URL 默认值

# ============================================================
# Docker ENTRYPOINT 模式：后台 fork 部署逻辑，主进程立即 exec CMD
#
# 这样做的原因：
#   - prod-deploy.sh 同步执行会阻塞 node server.js 启动 30s+
#   - 期间 readiness probe 失败 → pod NotReady
#   - 后台化后，主进程立即 exec node，readiness 秒过；部署逻辑在后台跑完
#
# 行为：
#   - 主进程（PROD_DEPLOY_FORKED != 1）：fork 自己到后台，exec "$@"（即 node server.js）
#   - 后台子进程（PROD_DEPLOY_FORKED = 1）：跑完 Bridge + Agent 注册后正常退出
#
# 跳过后台化（调试场景）：SKIP_PROD_DEPLOY=1
# ============================================================
if [ "${SKIP_PROD_DEPLOY:-0}" = "1" ]; then
    echo "[prod-deploy] SKIP_PROD_DEPLOY=1, skip deploy, exec main process"
    exec "$@"
fi

if [ "${PROD_DEPLOY_FORKED:-0}" != "1" ]; then
    echo "[prod-deploy] Forking deploy logic to background, main process execs CMD: $*"
    # nohup 忽略 SIGHUP，确保 exec 替换父进程后子进程继续运行
    # 容器内无终端会话问题，不需要 setsid
    PROD_DEPLOY_FORKED=1 nohup bash "$0" "$@" &
    FORK_PID=$!
    echo "[prod-deploy] Background PID: ${FORK_PID}"
    sleep 0.5
    if kill -0 "${FORK_PID}" 2>/dev/null; then
        echo "[prod-deploy] Background process confirmed running (PID ${FORK_PID})"
    else
        echo "[prod-deploy] WARNING: Background process exited immediately" >&2
    fi
    exec "$@"
fi

# 以下为后台子进程执行的部署逻辑
echo "[prod-deploy] Background deploy started at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
STATE_FILE="${PROJECT_DIR}/.agent/boost-state.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- 检查 boost-state.json ----
if [ ! -f "${STATE_FILE}" ]; then
    echo "ERROR: boost-state.json not found at ${STATE_FILE}" >&2
    echo "  请确保已通过 /agent-boost 生成 .agent/ 目录" >&2
    exit 1
fi

# ---- 读取配置（从 boost-state.json）----
AGENT_NAME=$(python3 -c "import json; print(json.load(open('${STATE_FILE}'))['agentName'])")
PROJECT_ID=$(python3 -c "import json; print(json.load(open('${STATE_FILE}'))['projectId'])")
STAFF_NAME=$(python3 -c "import json; print(json.load(open('${STATE_FILE}')).get('staffName',''))")

if [ -z "${STAFF_NAME}" ]; then
    echo "ERROR: staffName not found in boost-state.json" >&2
    exit 1
fi

# ---- 固定配置 ----
APP_PORT="${APP_PORT:-3000}"
BRIDGE_PORT="9999"
PROD_AGENT_SERVER="${PROD_AGENT_SERVER:-${PROD_AGENT_SERVER_URL}}"
MCP_SVC_SUFFIX="prod.hrainative.woa.com"   # 覆盖为 prod 域名后缀

BRIDGE_NAME="${PROJECT_ID}-bridge"
MCP_DIR="${PROJECT_DIR}/mcp_server"
MCP_URL=$(mcp_url "${PROJECT_ID}")   # 使用 _env.sh 的 mcp_url() 构造

echo "========================================"
echo "Agent Boost Production Deploy"
echo "  Agent:     ${AGENT_NAME}"
echo "  Project:   ${PROJECT_ID}"
echo "  Staff:     ${STAFF_NAME}"
echo "  Bridge:    0.0.0.0:${BRIDGE_PORT}"
echo "  App:       127.0.0.1:${APP_PORT}"
echo "  MCP URL:   ${MCP_URL}"
echo "  Server:    ${PROD_AGENT_SERVER}"
echo "========================================"

# ---- 检查 mcp_server 目录 ----
if [ ! -f "${MCP_DIR}/mcp_bridge.py" ]; then
    echo "ERROR: mcp_bridge.py not found at ${MCP_DIR}/mcp_bridge.py" >&2
    exit 1
fi

# ============================================================
# Step 1: 启动 MCP Bridge（固定端口 9999）
# ============================================================
echo ""
echo "[1/2] Starting MCP Bridge on port ${BRIDGE_PORT}..."

# 安装 Python 依赖
echo "  Installing Python dependencies..."
pip3 install -q -r "${MCP_DIR}/requirements.txt" 2>&1 || {
    echo "ERROR: failed to install Python dependencies from requirements.txt" >&2
    exit 1
}

# 清理旧 Bridge 进程
pm2 stop "${BRIDGE_NAME}" 2>/dev/null || true
pm2 delete "${BRIDGE_NAME}" 2>/dev/null || true
rm -f "${MCP_DIR}/.bridge-port"

# 启动 Bridge（固定端口，不走自动探测）
APP_BASE_URL="http://127.0.0.1:${APP_PORT}" \
BRIDGE_HOST="0.0.0.0" \
BRIDGE_PORT="${BRIDGE_PORT}" \
BRIDGE_NAME="${BRIDGE_NAME}" \
pm2 start "${MCP_DIR}/mcp_bridge.py" \
    --name "${BRIDGE_NAME}" \
    --interpreter python3 \
    --cwd "${MCP_DIR}" \
    --update-env

pm2 save
sleep 3

# 健康检查（tools/list）
# 响应可能是 SSE 格式（event: message\ndata: {...}）或纯 JSON，兼容两种
HEALTH=$(curl -s -X POST "http://127.0.0.1:${BRIDGE_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null || echo "")

TOOL_COUNT=$(echo "${HEALTH}" | python3 -c "
import sys, json
raw = sys.stdin.read()
# 兼容 SSE（data: {...}）和纯 JSON
data_line = next((l for l in raw.splitlines() if l.startswith('data:')), None)
payload = data_line[5:].strip() if data_line else raw.strip()
try:
    data = json.loads(payload)
    print(len(data.get('result', {}).get('tools', [])))
except Exception:
    print(0)
" 2>/dev/null || echo "0")

if [ "${TOOL_COUNT}" = "0" ]; then
    echo "  WARNING: Bridge started but tools/list returned 0 tools"
    echo "  Health check response: ${HEALTH:0:200}"
else
    echo "  OK: Bridge started, ${TOOL_COUNT} tools available"
fi

# ============================================================
# Step 2: 注册 Agent 到生产 agent-server
# ============================================================
echo ""
echo "[2/2] Registering Agent to ${PROD_AGENT_SERVER}..."

AGENT_NAME="${AGENT_NAME}" \
PROJECT_ID="${PROJECT_ID}" \
PROJECT_DIR="${PROJECT_DIR}" \
AGENT_SERVER_URL="${PROD_AGENT_SERVER}" \
STAFF_NAME="${STAFF_NAME}" \
MCP_URL="${MCP_URL}" \
DW_MCP_URL="http://ntsgw.woa.com/api/esb/mcp-host-server/mcp/DataViewMCP" \
BRIDGE_PORT="${BRIDGE_PORT}" \
bash "${SCRIPT_DIR}/register-agent.sh"

echo ""
echo "========================================"
echo "Production deploy complete!"
echo "  Agent:   ${AGENT_NAME}"
echo "  MCP URL: ${MCP_URL}"
echo "  Manage:  ${PROD_AGENT_SERVER}"
echo "========================================"
echo "[prod-deploy] Background deploy finished at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ============================================================
# 后台子进程到此结束，不 exec 主进程（主进程已在 fork 前 exec 了 CMD）
# ============================================================
