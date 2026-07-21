# setup.ps1 - 微云网盘 MCP Skill 一体化配置与授权脚本 (Windows PowerShell)
#
# 功能：
#   1. 检查 mcporter 是否已配置 weiyun（含 WyHeader 可用）
#   2. 未配置或 Token 失效时，展示授权链接并等待用户主动确认已完成授权
#   3. 用户确认后主动查询一次 Token 并写入 mcporter 配置
#   4. 对过期、错误等场景给出友好提示
#
# 用法（供 AI Agent 调用）：
#   第一步：检查状态（立即返回，不阻塞）
#     powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_check_and_start_auth
#     输出：
#       READY                  → 服务已就绪，直接执行用户任务，无需后续步骤
#       AUTH_REQUIRED:<url>    → 向用户展示授权链接，等待用户确认已完成授权后执行第二步
#       ERROR:*                → 告知用户对应错误
#
#   第二步：用户确认授权后，主动查询 Token（立即返回）
#     powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_fetch_token
#     输出：
#       TOKEN_READY            → 授权成功，继续执行用户任务
#       ERROR:not_authorized   → 用户尚未完成授权，请稍后重试
#       ERROR:expired          → 授权码已过期，请重新发起请求
#       ERROR:token_invalid    → Token 已失效，请重新授权
#       ERROR:*                → 告知用户对应错误
#
#   可选：直接带 Token 设置服务（跳过 OAuth 流程，适合已有 Token 的场景）
#     powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_set_token <token>
#     输出：
#       TOKEN_READY            → Token 写入成功，可直接执行用户任务
#       ERROR:missing_token    → 未提供 token 参数
#       ERROR:*                → 告知用户对应错误
#
# 直接执行（排查问题）：
#   powershell -ExecutionPolicy Bypass -File setup.ps1

param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1)]
    [string]$TokenArg
)

# ── 全局配置 ──────────────────────────────────────────────────────────────────
$WY_API_BASE = if ($env:WEIYUN_API_BASE_URL) { $env:WEIYUN_API_BASE_URL } else { "https://www.weiyun.com" }
$WY_AUTH_URL_TEMPLATE = "$WY_API_BASE/authorize/token?code="
$WY_TOKEN_API = "$WY_API_BASE/api/v3/mcp/token/code"
$WY_MCP_URL = if ($env:WEIYUN_MCP_URL) { $env:WEIYUN_MCP_URL } else { "https://www.weiyun.com/api/v3/mcpserver" }
$WY_SERVICE_NAME = "weiyun"
$WY_ENV_ID = if ($env:WEIYUN_ENV_ID) { $env:WEIYUN_ENV_ID } else { "" }

# 临时文件
$TempDir = if ($env:TEMP) { $env:TEMP } else { [System.IO.Path]::GetTempPath() }
$WY_CODE_FILE = Join-Path $TempDir ".weiyun_auth_code"
$WY_URL_FILE = Join-Path $TempDir ".weiyun_auth_url"

# ── 清理函数 ──────────────────────────────────────────────────────────────────
function Invoke-Cleanup {
    Remove-Item -Path $WY_CODE_FILE -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $WY_URL_FILE -Force -ErrorAction SilentlyContinue
}

# ── 检查 mcporter 是否已安装 ──────────────────────────────────────────────────
function Test-Mcporter {
    if (Get-Command mcporter -ErrorAction SilentlyContinue) {
        return $true
    }

    Write-Host "⚠️  未找到 mcporter，正在安装..."
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        try {
            & npm install -g mcporter@0.8.1 2>&1 | Select-Object -Last 3
            Write-Host "✅ mcporter 安装完成"
            return $true
        }
        catch {
            Write-Host "ERROR:npm_install_failed"
            return $false
        }
    }
    else {
        Write-Host "ERROR:no_npm"
        return $false
    }
}

# ── 检查 Python requests 库（上传脚本需要）───────────────────────────────────
function Test-PythonDeps {
    try {
        $null = & python3 -c "import requests" 2>&1
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    catch {}

    # 尝试 python（Windows 上 python3 可能不存在）
    try {
        $null = & python -c "import requests" 2>&1
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    catch {}

    Write-Host "⚠️  requests 库未安装，正在安装..."
    try {
        & pip3 install requests 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    catch {}

    try {
        & pip install requests 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    catch {}

    Write-Host "⚠️  requests 库安装失败，上传功能需要此库"
    Write-Host "   请手动执行：pip install requests"
    return $false
}

# ── 从 mcporter config get 读取当前 WyHeader Token ───────────────────────────
function Get-WeiyunToken {
    try {
        $output = & mcporter config get $WY_SERVICE_NAME 2>&1
        if ($LASTEXITCODE -ne 0) { return "" }
    }
    catch {
        return ""
    }

    # 从输出中提取 WyHeader 头的 mcp_token 值
    foreach ($line in ($output -split "`n")) {
        if ($line -match '(?i)^\s*WyHeader:\s*mcp_token=(.+)$') {
            return $Matches[1].Trim()
        }
    }
    return ""
}

# ── 将 Token 写入 mcporter 配置 ───────────────────────────────────────────────
function Save-WeiyunToken {
    param([string]$Token)

    Write-Host "🔧 配置 mcporter..."

    if ([string]::IsNullOrWhiteSpace($Token)) { return $false }

    # 构建 mcporter config add 命令参数
    $mcArgs = @(
        "config", "add", $WY_SERVICE_NAME, $WY_MCP_URL,
        "--transport", "http",
        "--header", "WyHeader=mcp_token=$Token",
        "--scope", "home"
    )

    # 仅当 WEIYUN_ENV_ID 存在时才添加 Cookie header
    if (-not [string]::IsNullOrWhiteSpace($WY_ENV_ID)) {
        $mcArgs += @("--header", "Cookie=env_id=$WY_ENV_ID")
    }

    # 执行配置命令
    & mcporter @mcArgs

    Write-Host ""
    Write-Host "✅ 配置完成！"
    Write-Host ""

    Write-Host "🧪 验证配置..."
    $listOutput = & mcporter list 2>&1 | Out-String
    if ($listOutput -match $WY_SERVICE_NAME) {
        Write-Host "✅ weiyun 配置验证成功！"
        Write-Host ""
        & mcporter list 2>&1 | Select-String -Pattern $WY_SERVICE_NAME -Context 0, 1
    }
    else {
        Write-Host "⚠️  weiyun 配置验证失败，请检查网络或 Token 是否有效"
    }

    Write-Host ""
    Write-Host "如有问题，请访问 https://www.weiyun.com/act/openclaw 获取 Token"

    Write-Host ""
    Write-Host "─────────────────────────────────────"
    Write-Host "🎉 设置完成！"
    Write-Host ""
    Write-Host "📖 配置详情："
    Write-Host "   URL:         $WY_MCP_URL"
    Write-Host "   传输协议:    streamable-http (mcporter --transport http)"
    if (-not [string]::IsNullOrWhiteSpace($WY_ENV_ID)) {
        Write-Host "   环境标识:    $WY_ENV_ID"
    }
    Write-Host ""
    Write-Host "📖 MCP Tools 调用示例："
    Write-Host ""
    Write-Host '   # 查询文件列表'
    Write-Host '   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json'
    Write-Host ""
    Write-Host '   # 获取下载链接'
    Write-Host '   mcporter call --server weiyun --tool weiyun.download items=''[{"file_id":"xxx","pdir_key":"yyy"}]'' --output json'
    Write-Host ""
    Write-Host '   # 删除文件'
    Write-Host '   mcporter call --server weiyun --tool weiyun.delete file_list=''[{"file_id":"xxx","pdir_key":"yyy"}]'' --output json'
    Write-Host ""
    Write-Host '   # 上传文件（推荐使用一键脚本）'
    Write-Host '   python scripts/upload_to_weiyun.py /path/to/file'
    Write-Host ""
    Write-Host "⚠️  注意：mcporter 调用时必须使用 --server weiyun --tool weiyun.xxx 格式，"
    Write-Host "   不要直接写 mcporter call weiyun.list（会导致 server/tool 名称拆分错误）"
    Write-Host ""
    Write-Host "☁️ 微云网盘主页：https://www.weiyun.com"
    Write-Host "📖 更多信息请查看 SKILL.md"
    Write-Host ""

    # 检查 Python 依赖（非阻塞，仅提示）
    $null = Test-PythonDeps

    return $true
}

# ── 检查 weiyun 服务状态 ──────────────────────────────────────────────────────
# 返回值：0 = 正常, 1 = 未注册, 2 = Token 为空
function Get-ServiceStatus {
    $listOutput = & mcporter list 2>&1 | Out-String
    if ($listOutput -notmatch $WY_SERVICE_NAME) {
        return 1
    }

    $token = Get-WeiyunToken
    if ([string]::IsNullOrWhiteSpace($token)) {
        return 2
    }

    return 0
}

# ── 生成授权链接 ──────────────────────────────────────────────────────────────
function New-AuthUrl {
    # 生成 16 字符十六进制随机码（等价 openssl rand -hex 8）
    $bytes = New-Object byte[] 8
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $code = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""

    # 写入临时文件
    $code | Out-File -FilePath $WY_CODE_FILE -Encoding UTF8 -NoNewline

    $url = "${WY_AUTH_URL_TEMPLATE}${code}"
    return $url
}

# ── 主入口函数 A：检查状态 / 生成授权链接 ────────────────────────────────────
function Invoke-CheckAndStartAuth {
    if (-not (Test-Mcporter)) {
        Write-Output "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return
    }

    $status = Get-ServiceStatus

    switch ($status) {
        0 {
            Write-Output "READY"
            return
        }
        default {
            Invoke-Cleanup

            # 生成授权链接（同时写入 code 文件）
            $authUrl = New-AuthUrl

            # 将 URL 写入文件
            $authUrl | Out-File -FilePath $WY_URL_FILE -Encoding UTF8 -NoNewline

            Write-Output "AUTH_REQUIRED:$authUrl"
            return
        }
    }
}

# ── 主入口函数 B：用户确认授权后，主动查询 Token ────────────────────────────
function Invoke-FetchToken {
    # 读取 code 文件
    if (-not (Test-Path $WY_CODE_FILE)) {
        Write-Output "ERROR:no_code - 未找到授权码，请先执行 weiyun_check_and_start_auth"
        return
    }

    $code = (Get-Content -Path $WY_CODE_FILE -Raw -Encoding UTF8).Trim()
    if ([string]::IsNullOrWhiteSpace($code)) {
        Write-Output "ERROR:empty_code - 授权码为空，请重新发起请求"
        return
    }

    # POST 请求查询 Token
    $body = "{`"code`":`"$code`"}"
    $headers = @{ "Content-Type" = "application/json" }

    # 携带环境标识 Cookie
    $session = $null
    if (-not [string]::IsNullOrWhiteSpace($WY_ENV_ID)) {
        $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
        $cookie = New-Object System.Net.Cookie("env_id", $WY_ENV_ID, "/", ".weiyun.com")
        $session.Cookies.Add($cookie)
    }

    try {
        $invokeArgs = @{
            Method      = "Post"
            Uri         = $WY_TOKEN_API
            ContentType = "application/json"
            Body        = $body
            ErrorAction = "Stop"
        }
        if ($session) {
            $invokeArgs["WebSession"] = $session
        }

        $resp = Invoke-RestMethod @invokeArgs
    }
    catch {
        Write-Output "ERROR:network - 网络请求失败，请检查网络连接后重试"
        return
    }

    # 提取 token（顶层字段 .token）
    $token = $null
    if ($resp.token) {
        $token = [string]$resp.token
    }

    if (-not [string]::IsNullOrWhiteSpace($token)) {
        if (Save-WeiyunToken -Token $token) {
            Invoke-Cleanup
            Write-Output "TOKEN_READY"
            return
        }
        else {
            Invoke-Cleanup
            Write-Output "ERROR:save_token_failed"
            return
        }
    }

    # 提取错误码和错误信息
    $errCode = ""
    $errMsg = ""
    if ($resp.code) { $errCode = [string]$resp.code }
    if ($resp.message) { $errMsg = [string]$resp.message }

    switch ($errCode) {
        "11510" {
            Write-Output "ERROR:not_authorized - 您尚未完成授权，请在浏览器中完成授权后重试"
            return
        }
        "117402" {
            Invoke-Cleanup
            Write-Output "ERROR:token_invalid - Token 鉴权失败，请重新授权"
            return
        }
        default {
            Write-Output "ERROR:unknown(code=$errCode, message=$errMsg) - 授权失败，请尝试手动设置 Token"
            return
        }
    }
}

# ── 主入口函数 C：直接带 token 参数设置 mcporter 服务 ────────────────────────
function Invoke-SetToken {
    param([string]$Token)

    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Output "ERROR:missing_token - 请提供 token 参数，用法：powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_set_token <token>"
        return
    }

    if (-not (Test-Mcporter)) {
        Write-Output "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return
    }

    if (Save-WeiyunToken -Token $Token) {
        Write-Output "TOKEN_READY"
    }
    else {
        Write-Output "ERROR:save_token_failed - Token 写入配置失败"
    }
}

# ── 直接执行时的交互式安装流程 ───────────────────────────────────────────────
function Invoke-InteractiveSetup {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗"
    Write-Host "║     微云网盘 MCP Skill 配置向导              ║"
    Write-Host "╚══════════════════════════════════════════════╝"
    Write-Host ""

    # 检查 mcporter
    Write-Host "🔍 检查 mcporter..."
    if (-not (Test-Mcporter)) {
        Write-Host "❌ mcporter 安装失败，请先安装 Node.js (https://nodejs.org) 后重试"
        exit 1
    }
    Write-Host "✅ mcporter 已就绪"
    Write-Host ""

    # 检查服务状态
    Write-Host "🔍 检查 weiyun 服务配置..."
    $status = Get-ServiceStatus

    switch ($status) {
        0 {
            Write-Host "✅ weiyun 服务已配置且运行正常！"
            Write-Host ""
            Write-Host "🎉 无需重新配置，您可以直接使用微云功能。"
            Write-Host ""
            Write-Host "📖 使用示例："
            Write-Host '   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json'
            return
        }
        default {
            Write-Host "⚠️  Token 未配置，需要授权..."
        }
    }

    Write-Host ""
    Write-Host "🔐 需要完成微云授权"
    Write-Host ""

    # 清理旧状态
    Invoke-Cleanup

    # 生成授权链接
    $authUrl = New-AuthUrl

    Write-Host "┌─────────────────────────────────────────────────────────┐"
    Write-Host "│  请在浏览器中打开以下链接完成授权：                      │"
    Write-Host "│                                                         │"
    Write-Host "│  $authUrl"
    Write-Host "│                                                         │"
    Write-Host "│  ⚠️  请使用 QQ 或微信 扫码 / 登录授权                   │"
    Write-Host "└─────────────────────────────────────────────────────────┘"
    Write-Host ""

    # 尝试打开浏览器
    try { Start-Process $authUrl } catch {}

    Write-Host "完成授权后，请按回车键继续..."
    $null = Read-Host

    # 用户确认后主动查询 Token
    Write-Host "⏳ 正在查询授权结果..."
    Invoke-FetchToken | ForEach-Object {
        $result = $_
        switch -Wildcard ($result) {
            "TOKEN_READY" {
                Write-Host ""
                Write-Host "🎉 配置完成！现在可以直接使用微云功能了。"
                Write-Host ""
                Write-Host "📖 使用示例："
                Write-Host '   mcporter call --server weiyun --tool weiyun.list limit=50 order_by=2 --output json'
                Write-Host ""
                Write-Host "☁️ 微云网盘主页：https://www.weiyun.com"
            }
            "ERROR:not_authorized*" {
                Write-Host ""
                Write-Host "⚠️  您似乎尚未完成授权，请在浏览器中完成授权后重新运行："
                Write-Host "    powershell -ExecutionPolicy Bypass -File setup.ps1 setup"
                exit 1
            }
            "ERROR:expired*" {
                Write-Host ""
                Write-Host "❌ Token 已过期，请访问 https://www.weiyun.com/act/openclaw 重新获取 Token，然后重新授权"
                exit 1
            }
            "ERROR:token_invalid*" {
                Write-Host ""
                Write-Host "❌ Token 鉴权失败，请重新运行："
                Write-Host "    powershell -ExecutionPolicy Bypass -File setup.ps1 setup"
                exit 1
            }
            "ERROR:*" {
                Write-Host ""
                Write-Host "❌ 授权失败：$result"
                Write-Host "   如问题持续，请联系微云客服"
                exit 1
            }
        }
    }
}

# ── 脚本入口 ──────────────────────────────────────────────────────────────────
switch ($Command) {
    "weiyun_check_and_start_auth" {
        Invoke-CheckAndStartAuth
    }
    "weiyun_fetch_token" {
        Invoke-FetchToken
    }
    "weiyun_set_token" {
        Invoke-SetToken -Token $TokenArg
    }
    "setup" {
        Write-Host "🚀 微云网盘 MCP Skill 人工配置向导"
        Write-Host ""
        Invoke-InteractiveSetup
    }
    "" {
        Write-Host "用法："
        Write-Host '  powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_check_and_start_auth      # 第一步：检查状态 / 生成授权链接'
        Write-Host '  powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_fetch_token               # 第二步：用户确认后主动查询 Token'
        Write-Host '  powershell -ExecutionPolicy Bypass -File setup.ps1 weiyun_set_token <token>         # 直接设置 Token（跳过 OAuth 流程）'
        Write-Host '  powershell -ExecutionPolicy Bypass -File setup.ps1 setup                            # 交互式配置向导'
    }
    default {
        Write-Host "ERROR:unknown_command - 未知命令: $Command"
        Write-Host "可用命令: weiyun_check_and_start_auth, weiyun_fetch_token, weiyun_set_token, setup"
        exit 1
    }
}
