#!/usr/bin/env bash
# NeoData 金融数据查询 - curl 封装
#
# Usage:
#   bash query.sh "腾讯最新财报"
#
# 环境变量:
#   NEODATA_SUB_CHANNEL - 子渠道名称 (默认: qclaw)
#   NEODATA_DATA_TYPE   - 数据类型 all/api/doc (默认: all)
#   AUTH_GATEWAY_PORT   - 本地代理端口 (默认: 19000)

set -euo pipefail

# --------------------------------------------------------
# 解析本地代理端口（跨平台兼容）
# --------------------------------------------------------

# 检测当前操作系统
case "$(uname -s)" in
    Linux*)  CURRENT_OS="linux" ;;
    Darwin*) CURRENT_OS="macos" ;;
    MINGW*|MSYS*|CYGWIN*) CURRENT_OS="windows" ;;
    *)       CURRENT_OS="unknown" ;;
esac

# 从环境变量 AUTH_GATEWAY_PORT 获取本地代理端口
# 该变量由 Electron 主进程在启动 Auth Gateway 时自动设置，子进程自动继承
# 若环境变量未设置，则回退到默认端口 19000
get_proxy_port() {
  local port="${AUTH_GATEWAY_PORT:-}"

  # 如果环境变量为空，且在 WSL 环境下，尝试从 Windows 注册表或 cmd 获取
  if [[ -z "$port" && "$CURRENT_OS" == "linux" && -f /proc/version ]]; then
    if grep -qi microsoft /proc/version 2>/dev/null; then
      echo "[QClaw] WSL detected, trying to read AUTH_GATEWAY_PORT from Windows environment" >&2
      port=$(cmd.exe /C "echo %AUTH_GATEWAY_PORT%" 2>/dev/null | tr -d '\r' || true)
      # cmd.exe 中未设置的变量会原样返回 %AUTH_GATEWAY_PORT%
      if [[ "$port" == "%AUTH_GATEWAY_PORT%" || -z "$port" ]]; then
        port=""
      fi
    fi
  fi

  # 最终回退到默认端口 19000
  if [[ -z "$port" ]]; then
    port="19000"
    echo "[QClaw] AUTH_GATEWAY_PORT not set, falling back to default port: $port" >&2
  fi

  echo "$port"
}

PROXY_PORT=$(get_proxy_port)
BASE_URL="http://localhost:${PROXY_PORT}/proxy/api"
REMOTE_URL="https://jprx.m.qq.com/aizone/skillserver/v1/proxy/teamrouter_neodata/query"

QUERY="${1:?用法: bash query.sh <query>}"
SUB_CHANNEL="${NEODATA_SUB_CHANNEL:-qclaw}"
DATA_TYPE="${NEODATA_DATA_TYPE:-all}"

REQUEST_ID=$(python3 -c "import uuid; print(uuid.uuid4().hex)" 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null | tr -d '-' || echo "req-$$-$(date +%s)")

RESPONSE=$(curl --silent --show-error --location --max-time 30 --connect-timeout 10 \
    --write-out "\n%{http_code}" \
    "${BASE_URL}" \
    --header "Content-Type: application/json" \
    --header "Remote-URL: ${REMOTE_URL}" \
    --data "$(cat <<EOF
{
    "channel": "neodata",
    "sub_channel": "${SUB_CHANNEL}",
    "query": "${QUERY}",
    "request_id": "${REQUEST_ID}",
    "data_type": "${DATA_TYPE}",
    "se_params": {},
    "extra_params": {}
}
EOF
)")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" -ne 200 ]]; then
    echo "请求失败: HTTP ${HTTP_CODE}" >&2
    [[ -n "$BODY" ]] && echo "$BODY" >&2
    exit 1
fi

echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
