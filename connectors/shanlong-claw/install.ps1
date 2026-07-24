#Requires -Version 5.1
<#
.SYNOPSIS
    商龙 CLI 连接器安装脚本 (Windows)
.PARAMETER Uninstall
    完全卸载
.PARAMETER Reset
    重置安装（清除所有数据后重新安装）
#>
param(
    [switch]$Uninstall,
    [switch]$Reset
)

$ErrorActionPreference = "Stop"
$SL_HOME = "$env:USERPROFILE\.slclaw"
$INSTALL_DIR = "$SL_HOME\bin"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-OK($msg) { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Warn($msg) { Write-Host "→ $msg" -ForegroundColor Yellow }

function Do-Uninstall {
    Write-Warn "卸载商龙 CLI ..."
    if (Test-Path $SL_HOME) { Remove-Item -Recurse -Force $SL_HOME }
    Write-OK "卸载完成"
    Write-Host ""
    Write-Host "提示：如果之前手动将 PATH 添加了 .slclaw\bin，请自行移除。"
    exit 0
}

function Check-Node {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Err "未检测到 Node.js，请先安装 Node.js >= 18"
        Write-Host "  下载地址: https://nodejs.org/"
        exit 1
    }
    $ver = (node -v) -replace 'v', ''
    $major = [int]($ver.Split('.')[0])
    if ($major -lt 18) {
        Write-Err "Node.js 版本过低: v$ver，需要 >= 18"
        exit 1
    }
    Write-OK "Node.js v$ver"
}

function Install-Local {
    Write-Warn "安装到 $INSTALL_DIR ..."

    if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
    if (-not (Test-Path $SL_HOME)) { New-Item -ItemType Directory -Path $SL_HOME -Force | Out-Null }

    Copy-Item -Recurse "$SCRIPT_DIR\dist" "$INSTALL_DIR\dist"
    Copy-Item "$SCRIPT_DIR\package.json" "$INSTALL_DIR\package.json"
    if (Test-Path "$SCRIPT_DIR\default.env") {
        Copy-Item "$SCRIPT_DIR\default.env" "$INSTALL_DIR\default.env"
        Copy-Item "$SCRIPT_DIR\default.env" "$SL_HOME\default.env"
    }

    # Windows PowerShell 5.1 的 -Encoding UTF8 会写入 BOM，
    # 导致 sl.cmd 首行变成 "﻿@echo" 而无法执行；统一无 BOM 写入。
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $wrapper = @"
#!/usr/bin/env node
require('./dist/cli/src/index.js');
"@
    [System.IO.File]::WriteAllText("$INSTALL_DIR\sl", ($wrapper.TrimEnd() + "`n"), $utf8NoBom)

    $bat = @"
@echo off
node "%~dp0dist\cli\src\index.js" %*
"@
    [System.IO.File]::WriteAllText("$INSTALL_DIR\sl.cmd", ($bat.TrimEnd() + "`r`n"), $utf8NoBom)

    if (Test-Path "$SCRIPT_DIR\skills") {
        if (Test-Path "$SL_HOME\skills") { Remove-Item -Recurse -Force "$SL_HOME\skills" }
        Copy-Item -Recurse "$SCRIPT_DIR\skills" "$SL_HOME\skills"
    }

    Write-OK "文件安装完成"
}

function Init-Env {
    $env_file = "$SL_HOME\.env"
    $default_env_file = "$SCRIPT_DIR\default.env"
    $needs_init = $false

    if (-not (Test-Path $env_file)) {
        $needs_init = $true
    } elseif (-not (Select-String -Path $env_file -Pattern 'SL_SLY_BASEURL' -Quiet)) {
        $needs_init = $true
        $saved_key = (Select-String -Path $env_file -Pattern '^SL_API_KEY=(.*)' | ForEach-Object { $_.Matches.Groups[1].Value }) | Select-Object -First 1
    }

    if ($needs_init) {
        if (-not (Test-Path $default_env_file)) {
            Write-Err "缺少 default.env，无法初始化连接器配置"
            exit 1
        }
        Copy-Item $default_env_file $env_file
        if ($saved_key) {
            (Get-Content $env_file) -replace '^SL_API_KEY=.*', "SL_API_KEY=$saved_key" | Set-Content $env_file
            Write-OK "配置已修复（保留原 API Key）"
        } else {
            Write-OK "默认配置已初始化"
        }
    } else {
        Write-OK "配置文件完整，保留原配置"
    }
}

function Setup-Path {
    $env:Path = "$INSTALL_DIR;$env:Path"
    Write-Warn "未自动修改用户 PATH；WorkBuddy 将通过 cli.json 中的绝对路径调用 sl.cmd"
    Write-Host "  如需在普通终端直接使用，请手动将 $INSTALL_DIR 添加到用户 PATH。"
}

function Verify-Install {
    $version = & node "$INSTALL_DIR\dist\cli\src\index.js" --version 2>$null
    if (-not $version) { $version = "unknown" }
    Write-OK "安装成功: sl v$version"
}

# === Main ===
if ($Uninstall) { Do-Uninstall }
if ($Reset) {
    Write-Warn "重置模式：清除所有数据后重新安装"
    if (Test-Path $SL_HOME) { Remove-Item -Recurse -Force $SL_HOME }
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════╗"
Write-Host "║  商龙 CLI 连接器安装 (Windows)        ║"
Write-Host "╚═══════════════════════════════════════╝"
Write-Host ""

Check-Node
Install-Local
Init-Env
Setup-Path
Verify-Install

Write-Host ""
Write-Host "下一步："
Write-Host "  1. 编辑 $SL_HOME\.env，填入 SL_API_KEY"
Write-Host "  2. 执行 & `"$INSTALL_DIR\sl.cmd`" connector status 验证"
