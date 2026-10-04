#!/bin/bash
# 金山文档 Skill — MCP 服务注册脚本

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_FILE="$SCRIPT_DIR/SKILL.md"
LEGACY_ENV_FILE="$SCRIPT_DIR/.env"
MCP_URL="https://mcp-center.wps.cn/skill_hub/mcp"
AUTO_INSTALL_MCPORTER=0

for arg in "$@"; do
    if [ "$arg" = "--auto-install-mcporter" ]; then
        AUTO_INSTALL_MCPORTER=1
    fi
done

echo "🚀 设置金山文档 Skill..."
echo ""

extract_header_value() {
    local json="$1"
    local key="$2"
    if command -v jq >/dev/null 2>&1; then
        jq -r --arg key "$key" '.headers[$key] // empty' <<<"$json" 2>/dev/null
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        JSON_INPUT="$json" JSON_KEY="$key" python3 - <<'PY'
import json
import os

try:
    data = json.loads(os.environ["JSON_INPUT"])
    value = data.get("headers", {}).get(os.environ["JSON_KEY"], "")
    if value is None:
        value = ""
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
    value = data.get("headers", {}).get(os.environ["JSON_KEY"], "")
    if value is None:
        value = ""
    print(value)
except Exception:
    pass
PY
        return
    fi
    sed -n "s/.*\"${key}\":[[:space:]]*\"\([^\"]*\)\".*/\1/p" <<<"$json" | head -n 1
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

get_legacy_env_file_token() {
    if [ ! -f "$LEGACY_ENV_FILE" ]; then
        return
    fi
    sed -n 's/^KINGSOFT_DOCS_TOKEN=//p' "$LEGACY_ENV_FILE" | head -n 1
}

normalize_token() {
    local auth_value="${1:-}"
    if [[ "$auth_value" =~ ^[Bb][Ee][Aa][Rr][Ee][Rr][[:space:]]+(.+)$ ]]; then
        echo "${BASH_REMATCH[1]}"
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

ensure_mcporter() {
    if command -v mcporter >/dev/null 2>&1; then
        return
    fi
    if [ "$AUTO_INSTALL_MCPORTER" -eq 1 ]; then
        if ! command -v npm >/dev/null 2>&1; then
            echo "❌ 未找到 mcporter，且当前环境没有 npm，无法自动安装"
            exit 1
        fi
        echo "⚠️  未找到 mcporter，已按参数要求自动安装..."
        npm install -g mcporter
        echo "✅ mcporter 安装完成"
    fi
    if ! command -v mcporter >/dev/null 2>&1; then
        echo "❌ 未找到 mcporter"
        echo "💡 默认不会自动修改系统环境。"
        echo "   - 手动安装后重试；或"
        echo "   - 追加参数 --auto-install-mcporter 允许脚本自动安装"
        exit 1
    fi
}

get_mcporter_config() {
    mcporter config get kdocs-workbuddy --json 2>/dev/null || true
}

validate_token() {
    local candidate="$1"
    local probe_name="kdocs-token-probe-$$-${RANDOM:-0}"
    local response=""

    if [ -z "$candidate" ]; then
        return 1
    fi

    local probe_args=(
        config add "$probe_name" "$MCP_URL"
        --header "Authorization=Bearer $candidate"
        --header "X-Skill-Version=$SKILL_VERSION"
        --header "X-Request-Source=workbuddy"
        --header "X-Client-Id=$CLIENT_ID"
        --transport http
        --scope home
    )

    mcporter config remove "$probe_name" >/dev/null 2>&1 || true
    mcporter "${probe_args[@]}" >/dev/null

    response=$(mcporter call "${probe_name}.search_files" keyword="__kdocs_token_probe__" type=all page_size=1 --output json 2>/dev/null || true)
    mcporter config remove "$probe_name" >/dev/null 2>&1 || true

    if [[ "$response" == *'"code": 400006'* ]]; then
        return 1
    fi
    return 0
}

write_mcporter_config() {
    local token="${1:-}"
    local client_id="$CLIENT_ID"
    local args=(
        config add kdocs-workbuddy "$MCP_URL"
        --header "X-Skill-Version=$SKILL_VERSION"
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

is_windows_host() {
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
    esac
    [ -n "${WINDIR:-}" ] || [ -n "${SystemRoot:-}" ]
}

print_get_token_manual_hint() {
    echo "❌ 获取 Token 失败。" >&2
    if command -v node >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/get-token.js" ]; then
        echo "💡 请切换到 WPS 个人账号后，再执行：node \"$SCRIPT_DIR/get-token.js\"" >&2
    elif is_windows_host && [ -f "$SCRIPT_DIR/get-token.ps1" ]; then
        echo "💡 请切换到 WPS 个人账号后，再执行：powershell -ExecutionPolicy Bypass -File \"$SCRIPT_DIR/get-token.ps1\"" >&2
    else
        echo "💡 请切换到 WPS 个人账号后，再执行：bash \"$SCRIPT_DIR/get-token.sh\"" >&2
    fi
}

run_get_token_script() {
    local args=()
    if [ "$AUTO_INSTALL_MCPORTER" -eq 1 ]; then
        args+=(--auto-install-mcporter)
    fi

    if command -v node >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/get-token.js" ]; then
        node "$SCRIPT_DIR/get-token.js" "${args[@]}"
        return $?
    fi

    if is_windows_host && [ -f "$SCRIPT_DIR/get-token.ps1" ]; then
        local ps_args=()
        local ps_file="$SCRIPT_DIR/get-token.ps1"
        if command -v cygpath >/dev/null 2>&1; then
            ps_file="$(cygpath -w "$ps_file")"
        fi
        if [ "$AUTO_INSTALL_MCPORTER" -eq 1 ]; then
            ps_args+=(-AutoInstallMcporter)
        fi
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps_file" "${ps_args[@]}"
        return $?
    fi

    bash "$SCRIPT_DIR/get-token.sh" "${args[@]}"
}

handle_get_token_result() {
    local rc="$1"
    case "$rc" in
        0) return 0 ;;
        3)
            # Enterprise denial tip already printed by get-token; do not urge immediate re-run.
            exit 3
            ;;
        4)
            # User cancellation is intentional; get-token already printed the retry command.
            exit 4
            ;;
        *)
            print_get_token_manual_hint
            exit 1
            ;;
    esac
}

refresh_token_via_login() {
    local reason="${1:-检测到 Token 不可用}"
    local refreshed_config=""
    local refreshed_auth=""
    local refreshed_token=""
    local rc=0

    echo "⚠️  ${reason}，正在重新获取授权..." >&2
    echo "" >&2
    set +e
    run_get_token_script >&2
    rc=$?
    set -e
    handle_get_token_result "$rc"

    refreshed_config="$(get_mcporter_config)"
    refreshed_auth="$(extract_header_value "$refreshed_config" "Authorization")"
    refreshed_token="$(normalize_token "$refreshed_auth")"

    if [ -z "$refreshed_token" ]; then
        print_get_token_manual_hint
        exit 1
    fi

    printf '%s\n' "$refreshed_token"
}

SKILL_VERSION="$(get_skill_version)"
if [ "$SKILL_VERSION" = "unknown" ]; then
    echo "⚠️  未能从 SKILL.md 提取版本号，将使用 'unknown'"
else
    echo "✅ Skill 版本：$SKILL_VERSION"
fi

ensure_mcporter

EXISTING_CONFIG="$(get_mcporter_config)"
EXISTING_VERSION="$(extract_header_value "$EXISTING_CONFIG" "X-Skill-Version")"
EXISTING_AUTH="$(extract_header_value "$EXISTING_CONFIG" "Authorization")"
EXISTING_TOKEN="$(normalize_token "$EXISTING_AUTH")"
EXISTING_CLIENT_ID="$(extract_header_value "$EXISTING_CONFIG" "X-Client-Id")"

if echo "$EXISTING_CLIENT_ID" | grep -qE '^[0-9a-f]{16}$'; then
    CLIENT_ID="$EXISTING_CLIENT_ID"
else
    CLIENT_ID="$(generate_client_id)"
fi

LEGACY_ENV_TOKEN="${KINGSOFT_DOCS_TOKEN:-}"
LEGACY_FILE_TOKEN="$(get_legacy_env_file_token)"

TOKEN_TO_SET="$EXISTING_TOKEN"
TOKEN_SOURCE="保留现有 mcporter 配置"

if [ -n "$LEGACY_ENV_TOKEN" ]; then
    echo "🔄 检测到旧环境变量 KINGSOFT_DOCS_TOKEN，正在迁移到 mcporter..."
    if validate_token "$LEGACY_ENV_TOKEN"; then
        TOKEN_TO_SET="$LEGACY_ENV_TOKEN"
        TOKEN_SOURCE="已迁移环境变量中的有效 Token"
    else
        TOKEN_TO_SET="$(refresh_token_via_login "环境变量中的 Token 已失效")"
        TOKEN_SOURCE="环境变量中的 Token 已失效，已重新登录并写入 mcporter"
    fi
elif [ -n "$LEGACY_FILE_TOKEN" ]; then
    echo "🔄 检测到旧版 .env Token，正在迁移到 mcporter..."
    if validate_token "$LEGACY_FILE_TOKEN"; then
        TOKEN_TO_SET="$LEGACY_FILE_TOKEN"
        TOKEN_SOURCE="已迁移 .env 中的有效 Token"
    else
        TOKEN_TO_SET="$(refresh_token_via_login ".env 中的 Token 已失效")"
        TOKEN_SOURCE=".env 中的 Token 已失效，已重新登录并写入 mcporter"
    fi
elif [ -n "$EXISTING_TOKEN" ]; then
    if validate_token "$EXISTING_TOKEN"; then
        if [ -n "$EXISTING_VERSION" ] && [ "$EXISTING_VERSION" != "$SKILL_VERSION" ]; then
            TOKEN_SOURCE="检测到版本更新，已沿用旧版 mcporter Token"
        fi
    else
        TOKEN_TO_SET="$(refresh_token_via_login "检测到 mcporter 中的 Token 已失效")"
        TOKEN_SOURCE="检测到 mcporter Token 已失效，已重新登录更新"
    fi
else
    echo "⚠️  未检测到可用 Token，正在拉起授权..."
    echo ""
    GET_TOKEN_RC=0
    set +e
    run_get_token_script
    GET_TOKEN_RC=$?
    set -e
    handle_get_token_result "$GET_TOKEN_RC"
    EXISTING_CONFIG="$(get_mcporter_config)"
    EXISTING_AUTH="$(extract_header_value "$EXISTING_CONFIG" "Authorization")"
    TOKEN_TO_SET="$(normalize_token "$EXISTING_AUTH")"
    if [ -z "$TOKEN_TO_SET" ]; then
        print_get_token_manual_hint
        exit 1
    fi
    TOKEN_SOURCE="已通过授权脚本写入 mcporter"
fi

write_mcporter_config "$TOKEN_TO_SET"
cleanup_legacy_env_file

echo ""
echo "✅ 配置完成：$TOKEN_SOURCE"
echo ""
echo "🧪 验证配置..."
if mcporter config get kdocs-workbuddy >/dev/null 2>&1; then
    echo "✅ 已成功写入 mcporter 配置"
else
    echo "⚠️  配置写入失败，请检查 mcporter 或网络环境"
fi
echo ""
echo "─────────────────────────────────────"
echo "🎉 设置完成！"
echo ""
echo "📖 使用方法："
echo "   mcporter call kdocs-workbuddy.scrape_url"
echo ""
echo "🏠 金山文档主页：https://www.kdocs.cn/latest"
echo ""
echo "📖 更多信息请查看 SKILL.md"
