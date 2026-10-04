# get-token.ps1 - WPS Authorization Tool (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File get-token.ps1 [-AutoInstallMcporter]

param(
    [switch]$AutoInstallMcporter
)

# $PSScriptRoot is always the directory of the running script, regardless of how it was invoked
$ScriptDir = $PSScriptRoot
$LegacyEnvFile = Join-Path $ScriptDir ".env"

# ---------- helpers ----------

function Get-SkillVersion {
    $skillFile = Join-Path $ScriptDir "SKILL.md"
    if (Test-Path $skillFile) {
        foreach ($line in (Get-Content $skillFile -Encoding UTF8)) {
            if ($line -match "^version:\s*(.+)") {
                return $Matches[1].Trim()
            }
        }
    }
    return "unknown"
}

function Extract-Token([object]$resp) {
    if ($resp.data -and $resp.data.token) { return $resp.data.token }
    if ($resp.token)                      { return $resp.token }
    return $null
}

function Extract-Expires([object]$resp) {
    if ($resp.data -and $resp.data.expires_in) { return [int]$resp.data.expires_in }
    if ($resp.expires_in)                      { return [int]$resp.expires_in }
    return 0
}

function Extract-RespCode([object]$resp) {
    if ($resp.code) { return [string]$resp.code }
    return ""
}

function Write-AuthorizationCancelled {
    $scriptPath = Join-Path $ScriptDir "get-token.ps1"
    Write-Host ""
    Write-Host "本次授权已取消，未写入 Token。"
    Write-Host "金山文档 Skill 当前仅支持 WPS 个人账号。"
    Write-Host "如需继续使用，请确认已登录 WPS 个人账号后重新执行："
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$scriptPath`""
}

function Generate-ClientId {
    $bytes = New-Object byte[] 8
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return -join ($bytes | ForEach-Object { $_.ToString("x2") })
}

function Get-ExistingClientId {
    try {
        $json = & mcporter config get kdocs-workbuddy --json 2>$null
        if (-not $json) { return "" }
        $config = $json | ConvertFrom-Json
        if ($config.headers -and $config.headers."X-Client-Id") {
            return $config.headers."X-Client-Id"
        }
    } catch {}
    return ""
}

function Ensure-Mcporter {
    if (Get-Command mcporter -ErrorAction SilentlyContinue) { return }

    if ($AutoInstallMcporter) {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            try { & npm install -g mcporter 2>&1 | Out-Null } catch {}
        } else {
            throw "mcporter is missing and npm is unavailable. Install mcporter manually or rerun with -AutoInstallMcporter in an npm-enabled environment."
        }
    }

    if (-not (Get-Command mcporter -ErrorAction SilentlyContinue)) {
        throw "mcporter is required to save the kdocs-workbuddy config. Default behavior will not auto-install globally. Install mcporter manually, or rerun with -AutoInstallMcporter."
    }
}

function Set-McporterConfig([string]$token, [string]$version, [string]$clientId) {
    Ensure-Mcporter
    try { & mcporter config remove kdocs-workbuddy 2>&1 | Out-Null } catch {}
    $mcArgs = @(
        "config", "add", "kdocs-workbuddy",
        "https://mcp-center.wps.cn/skill_hub/mcp",
        "--header", "Authorization=Bearer $token",
        "--header", "X-Skill-Version=$version",
        "--header", "X-Request-Source=workbuddy",
        "--header", "X-Client-Id=$clientId",
        "--transport", "http",
        "--scope", "home"
    )
    & mcporter @mcArgs 2>&1 | Out-Null
}

function Remove-LegacyEnvTokenKey {
    if (-not (Test-Path $LegacyEnvFile)) { return }

    $lines = Get-Content $LegacyEnvFile -Encoding UTF8
    $kept = @()
    $hasToken = $false
    foreach ($line in $lines) {
        if ($line -match "^KINGSOFT_DOCS_TOKEN=") {
            $hasToken = $true
        } else {
            $kept += $line
        }
    }

    if (-not $hasToken) { return }

    if ($kept.Count -eq 0) {
        Remove-Item -Path $LegacyEnvFile -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Removed KINGSOFT_DOCS_TOKEN from .env and deleted empty .env file."
    } else {
        Set-Content -Path $LegacyEnvFile -Value $kept -Encoding UTF8
        Write-Host "[OK] Removed KINGSOFT_DOCS_TOKEN from .env while preserving other keys."
    }
}

function Write-EnterpriseDenied {
    Write-Host ""
    Write-Host "授权结果：授权未通过"
    Write-Host ""
    Write-Host "原因：当前登录为 WPS 企业账号，本 Skill 暂不支持；mcporter 未写入 kdocs-workbuddy 配置。"
    Write-Host ""
    Write-Host "请引导用户："
    Write-Host "  1. 切换到 WPS 个人账号后，再执行一次授权"
    Write-Host "  2. 企业用户可改用 WPS365 CLI: https://github.com/wps365-open/cli"
    Write-Host ""
    Write-Host "（请勿在仍为企业账号登录状态时反复重跑授权脚本）"
}

# ---------- main ----------

$code      = [System.Guid]::NewGuid().ToString().ToLower()
$authGuidePage = "https://mcp-center.wps.cn/kdocs-auth/auth-guide?auth_code=$([System.Uri]::EscapeDataString($code))"

Write-Host ""
Write-Host "请在浏览器中打开以下链接登录："
Write-Host ""
Write-Host "  $authGuidePage"
Write-Host ""

try   { Start-Process $authGuidePage }
catch { Write-Host "未能自动打开浏览器，请手动复制上方链接访问" }

Write-Host "等待登录...（轮询间隔 1 秒，最长 5 分钟）"

$timeout  = 300
$interval = 1
$start    = Get-Date
$token    = $null
$expires  = 0

while ($true) {
    $elapsed = [int]((Get-Date) - $start).TotalSeconds

    if ($elapsed -ge $timeout) {
        Write-Host ""
        Write-Host "超时未登录（300秒）"
        exit 1
    }

    try {
        $body = '{"code":"' + $code + '"}'
        $resp = Invoke-RestMethod -Method Post `
            -Uri "https://api.wps.cn/office/v5/ai/skill_hub/wps_auth/exchange" `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop

        $rc  = Extract-RespCode $resp
        $tok = Extract-Token    $resp
        $exp = Extract-Expires  $resp

        if ($rc -eq "200" -and $tok) {
            $token   = $tok
            $expires = $exp
            break
        } elseif ($rc -eq "403") {
            Write-EnterpriseDenied
            exit 3
        } elseif ($rc -eq "409") {
            Write-AuthorizationCancelled
            exit 4
        } elseif ($rc -match '^5\d\d$') {
            # Temporary server error, keep polling.
        } elseif ($rc -eq "202") {
            if ($elapsed % 5 -eq 0) { Write-Host -NoNewline "." }
        } elseif ($rc) {
            Write-Host ""
            Write-Host "授权失败（错误码：$rc）"
            exit 1
        }
    } catch {
        # network hiccup, keep polling
        # Invoke-RestMethod may throw on non-2xx; try parse enterprise denial from error response if present
        $errResp = $null
        try {
            if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
                $errResp = $_.ErrorDetails.Message | ConvertFrom-Json
            }
        } catch {}
        if ($errResp) {
            $errCode = Extract-RespCode $errResp
            if ($errCode -eq "403") {
                Write-EnterpriseDenied
                exit 3
            } elseif ($errCode -eq "409") {
                Write-AuthorizationCancelled
                exit 4
            } elseif ($errCode -and $errCode -notmatch '^5\d\d$') {
                Write-Host ""
                Write-Host "授权失败（错误码：$errCode）"
                exit 1
            }
        }
    }

    Start-Sleep -Seconds $interval
}

Write-Host ""
Write-Host "登录成功！"

try {
    $existingCid = Get-ExistingClientId
    if ($existingCid -match '^[0-9a-f]{16}$') {
        $clientId = $existingCid
    } else {
        $clientId = Generate-ClientId
    }
    Set-McporterConfig $token (Get-SkillVersion) $clientId
    Remove-LegacyEnvTokenKey
    Write-Host "已更新 mcporter 中的 kdocs-workbuddy 配置。"
} catch {
    Write-Host "更新 mcporter 配置失败。"
    Write-Host $_.Exception.Message
    exit 1
}
