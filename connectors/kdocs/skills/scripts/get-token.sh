#!/bin/bash
#
# WPS 授权工具 - 获取 skill_hub token
#
# 流程：
#   1. 生成 code，打开授权引导页
#   2. 用户在浏览器打开链接登录
#   3. WPS 登录成功后回调服务端，将 wps_sid 转为 skill_hub token
#   4. 本脚本轮询 exchange 接口获取 token
#   5. 将 token 仅写入 mcporter，不再写入 .env 或环境变量
#
# 用法：bash get-token.sh [--json] [--notify] [--auto-install-mcporter]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_FILE="$SCRIPT_DIR/SKILL.md"
LEGACY_ENV_FILE="$SCRIPT_DIR/.env"
MCP_URL="https://mcp-center.wps.cn/skill_hub/mcp"
OUTPUT_JSON=0
SHOULD_NOTIFY=0
AUTO_INSTALL_MCPORTER=0

for arg in "$@"; do
  if [ "$arg" = "--json" ]; then
    OUTPUT_JSON=1
  elif [ "$arg" = "--notify" ]; then
    SHOULD_NOTIFY=1
  elif [ "$arg" = "--auto-install-mcporter" ]; then
    AUTO_INSTALL_MCPORTER=1
  fi
done

generate_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr 'A-Z' 'a-z'
  elif [ -f /proc/sys/kernel/random/uuid ]; then
    cat /proc/sys/kernel/random/uuid
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c "import uuid; print(uuid.uuid4())"
  elif command -v python >/dev/null 2>&1; then
    python -c "import uuid; print(uuid.uuid4())"
  else
    echo "$(date +%s%N)-$$-$RANDOM" | md5sum | cut -c1-32 |
      sed 's/\(........\)\(....\)\(....\)\(....\)\(............\)/\1-\2-4\3-\4-\5/' | cut -c1-36
  fi
}

extract_json_value() {
  local json="$1"
  local key="$2"
  if command -v jq >/dev/null 2>&1; then
    local value
    value=$(jq -r ".data.$key // .$key // empty" <<<"$json" 2>/dev/null || true)
    if [ -n "$value" ] && [ "$value" != "null" ]; then
      echo "$value"
      return
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    JSON_INPUT="$json" JSON_KEY="$key" python3 - <<'PY'
import json
import os

try:
    data = json.loads(os.environ["JSON_INPUT"])
    value = data.get("data", {}).get(os.environ["JSON_KEY"])
    if value in (None, ""):
        value = data.get(os.environ["JSON_KEY"], "")
    if value not in (None, ""):
        print(value)
except Exception:
    pass
PY
    return
  fi
  if command -v python >/dev/null 2>&1; then
    JSON_INPUT="$json" JSON_KEY="$key" python - <<'PY'
import json
import os

try:
    data = json.loads(os.environ["JSON_INPUT"])
    value = data.get("data", {}).get(os.environ["JSON_KEY"])
    if value in (None, ""):
        value = data.get(os.environ["JSON_KEY"], "")
    if value not in (None, ""):
        print(value)
except Exception:
    pass
PY
    return
  fi
  sed -n "s/.*\"${key}\":[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" <<<"$json" | head -n 1
}

get_skill_version() {
  local version=""
  if [ -f "$SKILL_FILE" ]; then
    version=$(sed -n 's/^version:[[:space:]]*//p' "$SKILL_FILE" | head -n 1)
  fi
  if [ -z "$version" ]; then
    echo "unknown"
  else
    echo "$version"
  fi
}

generate_client_id() {
    local id=""
    if command -v openssl >/dev/null 2>&1; then
        id="$(openssl rand -hex 8 2>/dev/null)"
    fi
    if [ -z "$id" ] && [ -c /dev/urandom ]; then
        id="$(od -A n -t x1 -N 8 /dev/urandom 2>/dev/null | tr -d ' \n' | head -c 16)"
    fi
    if [ -z "$id" ]; then
        id="0000000000000000"
    fi
    echo "$id"
}

get_existing_client_id() {
    local config
    config="$(mcporter config get kdocs-workbuddy --json 2>/dev/null || true)"
    if [ -z "$config" ]; then
        return
    fi
    if command -v jq >/dev/null 2>&1; then
        jq -r '.headers["X-Client-Id"] // empty' <<<"$config" 2>/dev/null
        return
    fi
    sed -n 's/.*"X-Client-Id":[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$config" | head -n 1
}

ensure_mcporter() {
  if command -v mcporter >/dev/null 2>&1; then
    return
  fi
  if [ "$AUTO_INSTALL_MCPORTER" -eq 1 ]; then
    if command -v npm >/dev/null 2>&1; then
      echo "⚠️  未找到 mcporter，已按参数要求自动安装..."
      npm install -g mcporter >/dev/null
      echo "✅ mcporter 安装完成"
    else
      echo "❌ 未找到 mcporter，且当前环境没有 npm，无法自动安装"
      echo "💡 请先手动安装 mcporter，或在可用 npm 环境下重试"
      exit 1
    fi
  fi
  if ! command -v mcporter >/dev/null 2>&1; then
    echo "❌ 未找到 mcporter"
    echo "💡 默认不会自动修改系统环境。"
    echo "   - 手动安装后重试；或"
    echo "   - 追加参数 --auto-install-mcporter 允许脚本自动安装"
    exit 1
  fi
}

set_mcporter_config() {
  local token="$1"
  local version="$2"
  local client_id="${3:-}"
  local args=(
    config add kdocs-workbuddy "$MCP_URL"
    --header "X-Skill-Version=$version"
    --header "X-Request-Source=workbuddy"
    --header "X-Client-Id=$client_id"
    --transport http
    --scope home
  )

  if [ -n "$token" ]; then
    args+=(--header "Authorization=Bearer $token")
  fi

  mcporter config remove kdocs-workbuddy >/dev/null 2>&1 || true
  mcporter "${args[@]}" >/dev/null
}

cleanup_legacy_env_file() {
  if [ ! -f "$LEGACY_ENV_FILE" ]; then
    return
  fi
  if ! grep -q '^KINGSOFT_DOCS_TOKEN=' "$LEGACY_ENV_FILE"; then
    return
  fi

  local tmp_file="${LEGACY_ENV_FILE}.tmp.$$"
  awk '!/^KINGSOFT_DOCS_TOKEN=/' "$LEGACY_ENV_FILE" > "$tmp_file"

  if [ ! -s "$tmp_file" ]; then
    rm -f "$LEGACY_ENV_FILE" "$tmp_file"
    echo "🧹 已移除 .env 中的 KINGSOFT_DOCS_TOKEN，清理后为空，已删除空 .env 文件"
  else
    mv "$tmp_file" "$LEGACY_ENV_FILE"
    echo "🧹 已移除 .env 中的 KINGSOFT_DOCS_TOKEN，保留其他配置"
  fi
}

send_notify() {
  local message="$1"
  if [ "$SHOULD_NOTIFY" -ne 1 ]; then
    return
  fi
  if command -v openclaw >/dev/null 2>&1; then
    openclaw agent --message "WPS Token 获取成功：$message" 2>/dev/null || true
  fi
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"$message\" with title \"WPS Token 已获取\"" 2>/dev/null || true
  fi
}

open_login_url() {
  local url="$1"
  local ps_url=""

  if command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 && return 0
  fi
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 && return 0
  fi

  # Windows (Git Bash / MSYS): open via PowerShell or cmd
  if command -v powershell.exe >/dev/null 2>&1; then
    ps_url=$(printf '%s' "$url" | sed "s/'/''/g")
    powershell.exe -NoProfile -NonInteractive -Command "Start-Process '$ps_url'" >/dev/null 2>&1 && return 0
  fi
  if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "$url" >/dev/null 2>&1 && return 0
  fi
  return 1
}

print_enterprise_denied() {
  echo ""
  echo "❌ 授权结果：授权未通过"
  echo ""
  echo "原因：当前登录为 WPS 企业账号，本 Skill 暂不支持；mcporter 未写入 kdocs-workbuddy 配置。"
  echo ""
  echo "请引导用户："
  echo "  1. 切换到 WPS 个人账号后，再执行一次授权"
  echo "  2. 企业用户可改用 WPS365 CLI: https://github.com/wps365-open/cli"
  echo ""
  echo "（请勿在仍为企业账号登录状态时反复重跑授权脚本）"
}

print_authorization_cancelled() {
  echo ""
  echo "本次授权已取消，未写入 Token。"
  echo "金山文档 Skill 当前仅支持 WPS 个人账号。"
  echo "如需继续使用，请确认已登录 WPS 个人账号后重新执行："
  echo "  bash \"$SCRIPT_DIR/get-token.sh\""
}

CODE=$(generate_uuid)
AUTH_GUIDE_PAGE="https://mcp-center.wps.cn/kdocs-auth/auth-guide?auth_code=${CODE}"

echo ""
echo "======================================================================"
echo "  WPS 授权 - 获取 skill_hub token"
echo "======================================================================"
echo ""
echo "📱 请在浏览器中打开以下链接登录："
echo ""
echo "   ${AUTH_GUIDE_PAGE}"
echo ""
echo "🔑 auth_code: ${CODE}"
echo ""
echo "======================================================================"
echo ""

if open_login_url "$AUTH_GUIDE_PAGE"; then
  echo "🌐 已自动打开浏览器，请完成 WPS 登录授权"
else
  echo "⚠️  未能自动打开浏览器，请手动复制上方链接访问"
fi
echo ""

echo "⏳ 等待登录... (轮询间隔 1 秒，最长 5 分钟)"

TIMEOUT=300
INTERVAL=1
START=$(date +%s)
LAST_DOT=0
SKILL_VERSION="$(get_skill_version)"

while true; do
  NOW=$(date +%s)
  ELAPSED=$((NOW - START))

  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo ""
    echo ""
    echo "❌ 超时未登录（${TIMEOUT}秒）"
    exit 1
  fi

  RESPONSE=$(curl -s -X POST \
    "https://api.wps.cn/office/v5/ai/skill_hub/wps_auth/exchange" \
    -H "Content-Type: application/json" \
    -d "{\"code\": \"${CODE}\"}") || RESPONSE=""

  RESP_CODE=$(extract_json_value "$RESPONSE" "code")
  TOKEN=$(extract_json_value "$RESPONSE" "token")
  EXPIRES=$(extract_json_value "$RESPONSE" "expires_in")

  if [ "$RESP_CODE" = "200" ] && [ -n "$TOKEN" ]; then
    echo ""
    echo ""
    echo "✅ 登录成功！"
    echo ""

    ensure_mcporter
    EXISTING_CID="$(get_existing_client_id)"
    if echo "$EXISTING_CID" | grep -qE '^[0-9a-f]{16}$'; then
        CLIENT_ID="$EXISTING_CID"
    else
        CLIENT_ID="$(generate_client_id)"
    fi
    set_mcporter_config "$TOKEN" "$SKILL_VERSION" "$CLIENT_ID"
    cleanup_legacy_env_file

    TOKEN_SHORT="${TOKEN:0:8}..."
    EXPIRES_HOURS=$((EXPIRES / 3600))

    echo "📝 Token 已写入 mcporter（不再写入 .env 或环境变量）"
    echo "⏰ expires_in: ${EXPIRES}s (约 ${EXPIRES_HOURS} 小时)"

    send_notify "Token 已更新至 mcporter，有效期约 ${EXPIRES_HOURS} 小时"

    if [ "$OUTPUT_JSON" -eq 1 ]; then
      echo "{\"token\":\"${TOKEN}\",\"expires_in\":${EXPIRES}}"
    else
      echo "🔒 Token 摘要: ${TOKEN_SHORT}"
    fi
    exit 0
  elif [ "$RESP_CODE" = "403" ]; then
    print_enterprise_denied
    exit 3
  elif [ "$RESP_CODE" = "409" ]; then
    print_authorization_cancelled
    exit 4
  elif echo "$RESP_CODE" | grep -qE '^5[0-9][0-9]$'; then
    : # Temporary server error, keep polling.
  elif [ "$RESP_CODE" = "202" ]; then
    if [ $((ELAPSED % 5)) -eq 0 ] && [ "$ELAPSED" -ne "$LAST_DOT" ]; then
      printf "."
      LAST_DOT=$ELAPSED
    fi
  elif [ -n "$RESP_CODE" ]; then
    echo ""
    echo "授权失败（错误码：${RESP_CODE}）"
    exit 1
  fi

  sleep "$INTERVAL"
done
