#!/usr/bin/env bash
# common.sh — 云文件上传备份 skill 公共函数库
# 提供统一的端口获取、HTTP 请求发送、JSON 构造和标准化输出
# Token 由本地代理服务自动注入，无需手动传入

set -euo pipefail

# --------------------------------------------------------
# 操作系统检测
# --------------------------------------------------------

detect_os() {
  local uname_out
  uname_out="$(uname -s 2>/dev/null || echo "Unknown")"
  case "$uname_out" in
    Linux*)   echo "linux" ;;
    Darwin*)  echo "macos" ;;
    CYGWIN*|MINGW*|MSYS*|MINGW32*|MINGW64*)  echo "windows" ;;
    *)        echo "unknown" ;;
  esac
}

CURRENT_OS=$(detect_os)
echo "[QClaw] Detected OS: $CURRENT_OS" >&2

# --------------------------------------------------------
# 解析本地代理端口（跨平台兼容）
# --------------------------------------------------------

# 从环境变量 AUTH_GATEWAY_PORT 获取本地代理端口
# 该变量由 Electron 主进程在启动 Auth Gateway 时自动设置，子进程自动继承
# 若环境变量未设置，则回退到默认端口 19000
get_proxy_port() {
  local port="${AUTH_GATEWAY_PORT:-}"

  # 如果环境变量为空，且在 WSL 环境下，尝试从 Windows 侧读取
  if [[ -z "$port" && "$CURRENT_OS" == "linux" && -f /proc/version ]]; then
    if grep -qi microsoft /proc/version 2>/dev/null; then
      echo "[QClaw] WSL detected, trying to read AUTH_GATEWAY_PORT from Windows environment" >&2
      port=$(cmd.exe /C "echo %AUTH_GATEWAY_PORT%" 2>/dev/null | tr -d '\r' || true)
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
echo "[QClaw] AUTH_GATEWAY_PORT: $PROXY_PORT" >&2
PROXY_BASE_URL="http://localhost:${PROXY_PORT}"
UPLOAD_API_BASE="${PROXY_BASE_URL}/proxy/qclaw-cos"

# --------------------------------------------------------
# 父进程 ID
# --------------------------------------------------------

get_ppid() {
  if command -v python3 &>/dev/null; then
    python3 -c "import os; print(os.getppid())" 2>/dev/null || echo "unknown"
  elif command -v python &>/dev/null; then
    python -c "import os; print(os.getppid())" 2>/dev/null || echo "unknown"
  else
    echo "unknown"
  fi
}

PPID_VAL=$(get_ppid)
echo "[QClaw] Parent PID: $PPID_VAL" >&2

# --------------------------------------------------------
# 检测 Node.js 可用性
# --------------------------------------------------------
# 优先级:
#   1. 从 ~/.qclaw/qclaw.json 读取 QClaw 内嵌的 Node.js 路径 (cli.nodeBinary)
#   2. 回退到系统 PATH 中的 node
#   3. 都不可用则输出标准 JSON 错误并退出

NODE_EXEC=""
META_FILE="${HOME}/.qclaw/qclaw.json"

# 尝试从 QClaw 元信息文件读取内嵌 Node.js 路径
if [[ -f "$META_FILE" ]]; then
  # 优先用 python3 解析 JSON（macOS 自带），然后尝试 python，最后用 node
  if command -v python3 &>/dev/null; then
    NODE_EXEC=$(python3 -c "import sys,json; print(json.load(sys.stdin).get('cli',{}).get('nodeBinary',''))" < "$META_FILE" 2>/dev/null || true)
  elif command -v python &>/dev/null; then
    NODE_EXEC=$(python -c "import sys,json; print(json.load(sys.stdin).get('cli',{}).get('nodeBinary',''))" < "$META_FILE" 2>/dev/null || true)
  elif command -v node &>/dev/null; then
    NODE_EXEC=$(node -e "const d=require('$META_FILE');console.log(d?.cli?.nodeBinary||'')" 2>/dev/null || true)
  fi

  # 验证从 meta 读取的路径是否存在
  if [[ -n "$NODE_EXEC" && ! -f "$NODE_EXEC" ]]; then
    echo "[QClaw] Warning: nodeBinary from qclaw.json not found: $NODE_EXEC, falling back to system node" >&2
    NODE_EXEC=""
  fi
fi

# 回退到系统 PATH 中的 node
if [[ -z "$NODE_EXEC" ]]; then
  if command -v node &>/dev/null; then
    NODE_EXEC="node"
  fi
fi

# 最终校验
if [[ -z "$NODE_EXEC" ]]; then
  echo '{"success": false, "message": "❌ 环境依赖缺失：未找到 Node.js。\n\nQClaw 内嵌 Node.js 路径不可用，系统 PATH 中也未安装 Node.js。\n请尝试：\n1. 重启 QClaw 桌面应用\n2. 或安装 Node.js (https://nodejs.org)", "error": "node 不可用: 未在 qclaw.json 和系统 PATH 中找到 Node.js"}'
  exit 1
fi

echo "[QClaw] Using Node.js: $NODE_EXEC" >&2

# --------------------------------------------------------
# JSON 构造工具
# --------------------------------------------------------

# json_build 使用 node 安全构造 JSON 字符串
# 用法: json_build key1 val1 key2 val2 ...
json_build() {
  "$NODE_EXEC" -e "
const args = process.argv.slice(1);
const obj = {};
for (let i = 0; i < args.length; i += 2) {
  const key = args[i];
  const val = args[i + 1];
  // 尝试解析为 JSON 值（数字、布尔、数组、对象）
  try {
    obj[key] = JSON.parse(val);
  } catch {
    obj[key] = val;
  }
}
console.log(JSON.stringify(obj));
" "$@"
}

# --------------------------------------------------------
# HTTP 请求封装
# --------------------------------------------------------

# do_upload_post 向上传 API 发送 POST 请求
# 参数: $1=API路径(如 /upload) $2=请求体JSON
# 输出: 响应 JSON 到 stdout
# 副作用: 设置全局变量 HTTP_STATUS
# 注意: 调用方需区分 HTTP 状态码:
#   200 = 成功
#   409 = 同名文件冲突（响应体包含冲突详情 JSON，需透传给 QClaw）
#   其他 = 真正的请求失败
do_upload_post() {
  local path="$1"
  local body="$2"
  local url="${UPLOAD_API_BASE}${path}"

  local tmp_file
  tmp_file=$(mktemp)
  trap "rm -f '$tmp_file'" RETURN

  # 初始化 HTTP_STATUS，避免 unbound variable
  HTTP_STATUS=""

  HTTP_STATUS=$(curl -s -o "$tmp_file" -w "%{http_code}" \
    -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$body")

  cat "$tmp_file"
}

# --------------------------------------------------------
# 标准化输出
# --------------------------------------------------------

# output_json 直接输出 JSON 响应（上传 API 已返回标准 JSON）
output_json() {
  echo "$1"
}

# output_error 输出标准错误 JSON
# 参数: $1=message
output_error() {
  local message="${1:-未知错误}"
  "$NODE_EXEC" -e "
console.log(JSON.stringify({
  success: false,
  message: process.argv[2],
  error: process.argv[2]
}));
" "$message"
}

# --------------------------------------------------------
# 参数解析辅助
# --------------------------------------------------------

# require_param 检查必填参数
# 参数: $1=参数名 $2=参数值
require_param() {
  local name="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    output_error "缺少必填参数: ${name}"
    exit 1
  fi
}
