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
        throw "mcporter is required to save the kdocs config. Default behavior will not auto-install globally. Install mcporter manually, or rerun with -AutoInstallMcporter."
    }
}

function Set-McporterConfig([string]$token, [string]$version) {
    Ensure-Mcporter
    try { & mcporter config remove kdocs 2>&1 | Out-Null } catch {}
    $mcArgs = @(
        "config", "add", "kdocs",
        "https://mcp-center.wps.cn/skill_hub/mcp",
        "--header", "Authorization=Bearer $token",
        "--header", "X-Skill-Version=$version",
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

# ---------- main ----------

$code      = [System.Guid]::NewGuid().ToString().ToLower()
$cb        = "https://api.wps.cn/office/v5/ai/skill_hub/users/callback?code=$code"
$encodedCb = [System.Uri]::EscapeDataString($cb)
$loginUrl  = "https://account.wps.cn/login?cb=$encodedCb"

Write-Host ""
Write-Host "Open the link below in your browser to sign in with your WPS account:"
Write-Host ""
Write-Host "  $loginUrl"
Write-Host ""

try   { Start-Process $loginUrl }
catch { Write-Host "[!] Cannot open browser automatically. Please copy the link above manually." }

Write-Host "Waiting for login..."

$timeout  = 300
$interval = 1
$start    = Get-Date
$token    = $null
$expires  = 0

while ($true) {
    $elapsed = [int]((Get-Date) - $start).TotalSeconds

    if ($elapsed -ge $timeout) {
        Write-Host ""
        Write-Host "[!] Timed out. Please run the script again."
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
        } elseif ($rc -eq "202") {
            if ($elapsed % 5 -eq 0) { Write-Host -NoNewline "." }
        }
    } catch {
        # network hiccup, keep polling
    }

    Start-Sleep -Seconds $interval
}

Write-Host ""
Write-Host "[OK] Login successful. kdocs Skill is ready."

try {
    Set-McporterConfig $token (Get-SkillVersion)
    Remove-LegacyEnvTokenKey
    Write-Host "[OK] Updated kdocs config in mcporter."
} catch {
    Write-Host "[!] Failed to update mcporter config."
    Write-Host $_.Exception.Message
    exit 1
}
