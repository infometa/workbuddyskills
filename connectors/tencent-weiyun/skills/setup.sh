#!/bin/bash
#
# Setup script for 微云网盘 MCP Skill 一体化配置与授权脚本
#
# 功能：
#   1. 检查 mcporter 是否已配置 weiyun（含 WyHeader 可用）
#   2. 未配置或 Token 失效时，展示授权链接并等待用户主动确认已完成授权
#   3. 用户确认后主动查询一次 Token 并写入 mcporter 配置
#   4. 对过期、错误等场景给出友好提示
#
# 用法（供 AI Agent 调用）：
#   第一步：检查状态（立即返回，不阻塞）
#     bash ./setup.sh weiyun_check_and_start_auth
#     输出：
#       READY                  → 服务已就绪，直接执行用户任务，无需后续步骤
#       AUTH_REQUIRED:<url>    → 向用户展示授权链接，等待用户确认已完成授权后执行第二步
#       ERROR:*                → 告知用户对应错误
#
#   第二步：用户确认授权后，主动查询 Token（立即返回）
#     bash ./setup.sh weiyun_fetch_token
#     输出：
#       TOKEN_READY            → 授权成功，继续执行用户任务
#       ERROR:not_authorized   → 用户尚未完成授权，请稍后重试
#       ERROR:expired          → 授权码已过期，请重新发起请求
#       ERROR:token_invalid    → Token 已失效，请重新授权
#       ERROR:*                → 告知用户对应错误
#
#   可选：直接带 Token 设置服务（跳过 OAuth 流程，适合已有 Token 的场景）
#     bash ./setup.sh weiyun_set_token <token>
#     输出：
#       TOKEN_READY            → Token 写入成功，可直接执行用户任务
#       ERROR:missing_token    → 未提供 token 参数
#       ERROR:*                → 告知用户对应错误
#
# 直接执行（排查问题）：
#   bash ./setup.sh
#

# ── 全局配置 ──────────────────────────────────────────────────────────────────
_WY_API_BASE="${WEIYUN_API_BASE_URL:-https://www.weiyun.com}"
_WY_AUTH_URL_TEMPLATE="${_WY_API_BASE}/authorize/token?code="
_WY_TOKEN_API="${_WY_API_BASE}/api/v3/mcp/token/code"
_WY_MCP_URL="${WEIYUN_MCP_URL:-https://www.weiyun.com/api/v3/mcpserver}"
_WY_SERVICE_NAME="weiyun"
_WY_ENV_ID="${WEIYUN_ENV_ID:-}"

# 临时文件
_WY_CODE_FILE="${TMPDIR:-/tmp}/.weiyun_auth_code"
_WY_URL_FILE="${TMPDIR:-/tmp}/.weiyun_auth_url"

# ── 清理函数 ──────────────────────────────────────────────────────────────────
_wy_cleanup() {
    rm -f "$_WY_CODE_FILE" "$_WY_URL_FILE"
}

# ── 检查 mcporter 是否已安装 ──────────────────────────────────────────────────
_wy_check_mcporter() {
    if ! command -v mcporter &> /dev/null; then
        echo "⚠️  未找到 mcporter，正在安装..."
        if command -v npm &>/dev/null; then
            npm install -g mcporter@0.8.1 2>&1 | tail -3
            echo "✅ mcporter 安装完成"
        else
            echo "ERROR:no_npm"
            return 1
        fi
    fi
    return 0
}

# ── 检查 Python requests 库（上传脚本需要）───────────────────────────────────
_wy_check_python_deps() {
    if python3 -c "import requests" 2>/dev/null; then
        return 0
    else
        echo "⚠️  requests 库未安装，正在安装..."
        pip3 install requests 2>/dev/null || pip install requests 2>/dev/null || {
            echo "⚠️  requests 库安装失败，上传功能需要此库"
            echo "   请手动执行：pip install requests"
            return 1
        }
    fi
    return 0
}

# ── 从 mcporter config get 读取当前 WyHeader Token ───────────────────────────
# 输出：token 字符串（空则表示服务未注册或 Token 未配置）
_wy_get_token() {
    local output
    output=$(mcporter config get "$_WY_SERVICE_NAME" 2>/dev/null) || return 1

    # 从输出中提取 WyHeader 头的 mcp_token 值
    local token
    token=$(echo "$output" | grep -i '^\s*WyHeader:' | sed 's/.*mcp_token=//' | tr -d '[:space:]')
    echo "$token"
}

# ── 将 Token 写入 mcporter 配置 ───────────────────────────────────────────────
# 用法：_wy_save_token <token>
_wy_save_token() {
    echo "🔧 配置 mcporter..."

    local token="$1"
    [[ -z "$token" ]] && return 1

    # 构建 mcporter config add 命令
    local cmd=(
        mcporter config add "$_WY_SERVICE_NAME" "$_WY_MCP_URL"
        --transport http
        --header "WyHeader=mcp_token=$token"
        --scope home
    )

    # 仅当 WEIYUN_ENV_ID 存在时才添加 Cookie header
    if [[ -n "$_WY_ENV_ID" ]]; then
        cmd+=(--header "Cookie=env_id=$_WY_ENV_ID")
    fi

    # 执行配置命令
    "${cmd[@]}"

    echo ""
    echo "✅ 配置完成！"
    echo ""

    echo "🧪 验证配置..."
    if mcporter list 2>&1 | grep -q "$_WY_SERVICE_NAME"; then
        echo "✅ weiyun 配置验证成功！"
        echo ""
        mcporter list | grep -A 1 "$_WY_SERVICE_NAME" || true
    else
        echo "⚠️  weiyun 配置验证失败，请检查网络或 Token 是否有效"
    fi

    echo ""
    echo "如有问题，请访问 https://www.weiyun.com/act/openclaw 获取 Token"

    echo ""
    echo "─────────────────────────────────────"
    echo "🎉 设置完成！"
    echo ""
    echo "📖 配置详情："
    echo "   URL:         $_WY_MCP_URL"
    echo "   传输协议:    streamable-http (mcporter --transport http)"
    [[ -n "$_WY_ENV_ID" ]] && echo "   环境标识:    $_WY_ENV_ID"
    echo ""
    echo "📖 MCP Tools 调用示例："
    echo ""
    echo "   # 查询文件列表"
    echo "   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json"
    echo ""
    echo "   # 获取下载链接"
    echo "   mcporter call --server weiyun --tool weiyun.download items='[{\"file_id\":\"xxx\",\"pdir_key\":\"yyy\"}]' --output json"
    echo ""
    echo "   # 删除文件"
    echo "   mcporter call --server weiyun --tool weiyun.delete file_list='[{\"file_id\":\"xxx\",\"pdir_key\":\"yyy\"}]' --output json"
    echo ""
    echo "   # 上传文件（推荐使用一键脚本）"
    echo "   python3 scripts/upload_to_weiyun.py /path/to/file"
    echo ""
    echo "⚠️  注意：mcporter 调用时必须使用 --server weiyun --tool weiyun.xxx 格式，"
    echo "   不要直接写 mcporter call weiyun.list（会导致 server/tool 名称拆分错误）"
    echo ""
    echo "☁️ 微云网盘主页：https://www.weiyun.com"
    echo "📖 更多信息请查看 SKILL.md"
    echo ""

    # 检查 Python 依赖（非阻塞，仅提示）
    _wy_check_python_deps

    return 0
}

# ── 检查 weiyun 服务状态 ──────────────────────────────────────────────────────
# 返回值：
#   0 = 服务正常可用（有 Token）
#   1 = 服务未注册（mcporter list 中找不到）
#   2 = Token 为空或未配置
_wy_check_service() {
    if ! mcporter list 2>/dev/null | grep -q "$_WY_SERVICE_NAME"; then
        return 1
    fi

    local token
    token=$(_wy_get_token)
    local rc=$?

    # mcporter config get 返回非 0 表示服务未注册
    if [[ $rc -ne 0 ]]; then
        return 1
    fi

    # Token 为空表示服务已注册但未配置 WyHeader
    if [[ -z "$token" ]]; then
        return 2
    fi

    return 0
}

# ── 生成授权链接 ──────────────────────────────────────────────────────────────
# 输出：auth_url 字符串，同时将 code 写入 $_WY_CODE_FILE
_wy_generate_auth_url() {
    local code
    code=$(openssl rand -hex 8 2>/dev/null || \
           cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' 2>/dev/null | head -c 16 || \
           date +%s%N 2>/dev/null | sha256sum 2>/dev/null | head -c 16 || \
           echo "$(date +%s)$$")

    echo "$code" > "$_WY_CODE_FILE"
    echo "${_WY_AUTH_URL_TEMPLATE}${code}"
}

# ── 主入口函数 A：检查状态 / 生成授权链接（立即返回，不阻塞）────────────────
#
# AI Agent 第一步调用此函数，命令执行完毕后立即拿到输出：
#   READY                  服务已就绪，直接执行用户任务，无需后续步骤
#   AUTH_REQUIRED:<url>    需要授权：向用户展示链接，等用户确认后执行第二步
#   ERROR:*                错误信息
#
weiyun_check_and_start_auth() {
    _wy_check_mcporter || {
        echo "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    _wy_check_service
    local status=$?

    case $status in
        0)
            echo "READY"
            return 0
            ;;
        1|2)
            _wy_cleanup

            # 生成授权链接（同时写入 code 文件）
            local auth_url
            auth_url=$(_wy_generate_auth_url)

            # 将 URL 写入文件，供后续阶段读取
            echo "$auth_url" > "$_WY_URL_FILE"

            echo "AUTH_REQUIRED:$auth_url"
            return 0
            ;;
    esac
}

# ── 主入口函数 B：用户确认授权后，主动查询 Token 并写入配置（立即返回）────────
#
# AI Agent 在用户确认已完成授权后调用此函数，主动查询一次 Token：
#   TOKEN_READY            授权成功，Token 已写入配置，直接执行用户任务
#   ERROR:not_authorized   用户尚未完成授权，请稍后重试或重新发起请求
#   ERROR:expired          授权码已过期，告知用户重新发起请求
#   ERROR:token_invalid    Token 鉴权失败，告知用户重新授权
#   ERROR:*                错误信息
#
weiyun_fetch_token() {
    # 读取 code 文件
    if [[ ! -f "$_WY_CODE_FILE" ]]; then
        echo "ERROR:no_code - 未找到授权码，请先执行 weiyun_check_and_start_auth"
        return 1
    fi

    local code
    code=$(cat "$_WY_CODE_FILE")
    if [[ -z "$code" ]]; then
        echo "ERROR:empty_code - 授权码为空，请重新发起请求"
        return 1
    fi

    # POST 请求轮询 Token，入参 code，返回 token
    local response
    # 构建 curl 命令参数
    local curl_args=(-s -f -L -X POST "$_WY_TOKEN_API"
        -H "Content-Type: application/json"
        -d "{\"code\":\"${code}\"}")

    # 携带环境标识 Cookie
    if [[ -n "$_WY_ENV_ID" ]]; then
        curl_args+=(-b "env_id=$_WY_ENV_ID")
    fi

    response=$(curl "${curl_args[@]}" 2>/dev/null)
    if [[ $? -ne 0 || -z "$response" ]]; then
        echo "ERROR:network - 网络请求失败，请检查网络连接后重试"
        return 1
    fi

    # 提取 token（顶层字段 .token）
    local token
    token=$(echo "$response" | jq -r '.token // empty' 2>/dev/null || echo "")
    if [[ -n "$token" ]]; then
        if _wy_save_token "$token"; then
            _wy_cleanup
            echo "TOKEN_READY"
            return 0
        else
            _wy_cleanup
            echo "ERROR:save_token_failed"
            return 1
        fi
    fi

    # 提取错误码（顶层字段 .code）和错误信息（.message）
    local err_code
    err_code=$(echo "$response" | jq -r '.code // empty' 2>/dev/null || echo "")
    local err_msg
    err_msg=$(echo "$response" | jq -r '.message // empty' 2>/dev/null || echo "")

    case "$err_code" in
        "11510")
            # code not found or expired — 用户还未完成授权或授权码已过期
            echo "ERROR:not_authorized - 您尚未完成授权，请在浏览器中完成授权后重试"
            return 1
            ;;
        "117402")
            # Token 无效
            _wy_cleanup
            echo "ERROR:token_invalid - Token 鉴权失败，请重新授权"
            return 1
            ;;
        *)
            echo "ERROR:unknown(code=${err_code}, message=${err_msg}) - 授权失败，请尝试手动设置 Token"
            return 1
            ;;
    esac
}

# ── 主入口函数 C：直接带 token 参数设置 mcporter 服务 ────────────────────────
#
# AI Agent 在已知 token 的情况下可直接调用此函数，跳过 OAuth 授权流程：
#   TOKEN_READY            Token 写入成功，可直接执行用户任务
#   ERROR:missing_token    未提供 token 参数
#   ERROR:save_token_failed  写入配置失败
#
# 用法：
#   bash ./setup.sh weiyun_set_token <token>
#
weiyun_set_token() {
    local token="$1"
    if [[ -z "$token" ]]; then
        echo "ERROR:missing_token - 请提供 token 参数，用法：bash ./setup.sh weiyun_set_token <token>"
        return 1
    fi

    _wy_check_mcporter || {
        echo "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    if _wy_save_token "$token"; then
        echo "TOKEN_READY"
        return 0
    else
        echo "ERROR:save_token_failed - Token 写入配置失败"
        return 1
    fi
}

# ── 直接执行时的交互式安装流程 ───────────────────────────────────────────────
_wy_interactive_setup() {
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║     微云网盘 MCP Skill 配置向导              ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""

    # 检查 mcporter
    echo "🔍 检查 mcporter..."
    if ! _wy_check_mcporter; then
        echo "❌ mcporter 安装失败，请先安装 Node.js (https://nodejs.org) 后重试"
        exit 1
    fi
    echo "✅ mcporter 已就绪"
    echo ""

    # 检查服务状态
    echo "🔍 检查 weiyun 服务配置..."
    _wy_check_service
    local status=$?

    case $status in
        0)
            echo "✅ weiyun 服务已配置且运行正常！"
            echo ""
            echo "🎉 无需重新配置，您可以直接使用微云功能。"
            echo ""
            echo "📖 使用示例："
            echo "   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json"
            return 0
            ;;
        1|2)
            echo "⚠️  Token 未配置，需要授权..."
            ;;
    esac

    echo ""
    echo "🔐 需要完成微云授权"
    echo ""

    # 清理旧状态
    _wy_cleanup

    # 生成授权链接（同时写入 code 文件）
    local auth_url
    auth_url=$(_wy_generate_auth_url)

    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│  请在浏览器中打开以下链接完成授权：                      │"
    echo "│                                                         │"
    printf "│  %s\n" "$auth_url"
    echo "│                                                         │"
    echo "│  ⚠️  请使用 QQ 或微信 扫码 / 登录授权                   │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
    echo "完成授权后，请按回车键继续..."
    read -r

    # 用户确认后主动查询 Token
    echo "⏳ 正在查询授权结果..."
    local result
    result=$(weiyun_fetch_token)

    case "$result" in
        TOKEN_READY)
            echo ""
            echo "🎉 配置完成！现在可以直接使用微云功能了。"
            echo ""
            echo "📖 使用示例："
            echo "   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json"
            echo ""
            echo "☁️ 微云网盘主页：https://www.weiyun.com"
            ;;
        ERROR:not_authorized*)
            echo ""
            echo "⚠️  您似乎尚未完成授权，请在浏览器中完成授权后重新运行：bash ./setup.sh setup"
            exit 1
            ;;
        ERROR:expired*)
            echo ""
            echo "❌ Token 已过期，请访问 https://www.weiyun.com/act/openclaw 重新获取 Token，然后重新授权"
            exit 1
            ;;
        ERROR:token_invalid*)
            echo ""
            echo "❌ Token 鉴权失败，请重新运行：bash ./setup.sh setup"
            exit 1
            ;;
        ERROR:*)
            echo ""
            echo "❌ 授权失败：$result"
            echo "   如问题持续，请联系微云客服"
            exit 1
            ;;
    esac

    return 0
}

# ── 脚本入口 ──────────────────────────────────────────────────────────────────
# 直接执行时：
#   bash ./setup.sh weiyun_check_and_start_auth  → 第一步：检查状态 / 生成授权链接
#   bash ./setup.sh weiyun_fetch_token           → 第二步：用户确认后主动查询 Token
#   bash ./setup.sh weiyun_set_token <token>     → 直接设置 Token（跳过 OAuth 流程）
#   bash ./setup.sh setup                        → 交互式配置向导
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ -n "$1" ]]; then
        # 参数分发：将第一个参数作为函数名执行
        case "$1" in
            weiyun_check_and_start_auth|weiyun_fetch_token)
                "$1"
                exit $?
                ;;
            weiyun_set_token)
                weiyun_set_token "$2"
                exit $?
                ;;
            setup)
                echo "🚀 微云网盘 MCP Skill 人工配置向导"
                echo ""
                _wy_interactive_setup
                ;;
            *)
                echo "ERROR:unknown_command - 未知命令: $1"
                echo "可用命令: weiyun_check_and_start_auth, weiyun_fetch_token, weiyun_set_token, setup"
                exit 1
                ;;
        esac
    else
        echo "用法："
        echo "  bash ./setup.sh weiyun_check_and_start_auth      # 第一步：检查状态 / 生成授权链接"
        echo "  bash ./setup.sh weiyun_fetch_token               # 第二步：用户确认后主动查询 Token"
        echo "  bash ./setup.sh weiyun_set_token <token>         # 直接设置 Token（跳过 OAuth 流程）"
        echo "  bash ./setup.sh setup                            # 交互式配置向导"
    fi
fi
