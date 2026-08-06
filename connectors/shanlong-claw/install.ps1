#Requires -Version 5.1
<#
.SYNOPSIS
    商龙 CLI 连接器安装脚本 (Windows)
    从 OSS/CDN 下载 slclaw-cli.tgz 并安装到 %USERPROFILE%\.slclaw
.PARAMETER EnsureLatest
    对比 OSS 版本，有更新则覆盖安装；stdout 仅输出当前版本号（供 CLI 层自检）
.PARAMETER Uninstall
    完全卸载
.PARAMETER Reset
    重置安装（清除所有数据后重新安装）
#>
param(
    [switch]$EnsureLatest,
    [switch]$Uninstall,
    [switch]$Reset
)

$ErrorActionPreference = "Stop"
$SL_HOME = if ($env:SL_CLI_HOME) { $env:SL_CLI_HOME } else { "$env:USERPROFILE\.slclaw" }
$INSTALL_DIR = "$SL_HOME\bin"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$URL_CONF = Join-Path $SCRIPT_DIR "install-url.conf"
$HomeUrlConf = Join-Path $SL_HOME "install-url.conf"

function Write-Log($msg) { [Console]::Error.WriteLine($msg) }
function Write-OK($msg) { Write-Log "✓ $msg" }
function Write-Err($msg) { Write-Log "✗ $msg" }
function Write-Warn($msg) { Write-Log "→ $msg" }

function Do-Uninstall {
    Write-Warn "卸载商龙 CLI ..."
    if (Test-Path $SL_HOME) { Remove-Item -Recurse -Force $SL_HOME }
    Write-OK "卸载完成"
    Write-Log ""
    Write-Log "提示：如果之前手动将 PATH 添加了 .slclaw\bin，请自行移除。"
    exit 0
}

function Get-ConfValue([string]$key) {
    foreach ($conf in @($URL_CONF, $HomeUrlConf)) {
        if (-not (Test-Path $conf)) { continue }
        $line = Get-Content -Path $conf | Where-Object { $_ -match "^\s*$key\s*=" } | Select-Object -First 1
        if ($line) {
            return ($line -replace "^\s*$key\s*=\s*", "").Trim()
        }
    }
    return $null
}

function Get-TgzUrl {
    if ($env:SL_CLI_TGZ_URL) { return $env:SL_CLI_TGZ_URL }
    $url = Get-ConfValue "SL_CLI_TGZ_URL"
    if (-not $url) {
        Write-Err "缺少 install-url.conf 或未设置 SL_CLI_TGZ_URL"
        exit 1
    }
    return $url
}

function Get-VersionUrl([string]$tgzUrl) {
    if ($env:SL_CLI_VERSION_URL) { return $env:SL_CLI_VERSION_URL }
    $fromConf = Get-ConfValue "SL_CLI_VERSION_URL"
    if ($fromConf) { return $fromConf }
    if ($tgzUrl -match '\.tgz$') {
        return ($tgzUrl -replace '\.tgz$', '.version')
    }
    return "$tgzUrl.version"
}

function Assert-TgzUrl([string]$url) {
    if ($url -match 'REPLACE_WITH_YOUR_OSS_HOST') {
        Write-Err "尚未配置真实 OSS/CDN 地址"
        Write-Log "  请编辑: $URL_CONF"
        Write-Log "  或设置环境变量 SL_CLI_TGZ_URL 后重试"
        exit 1
    }
}

function Check-Node {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Err "未检测到 Node.js，请先安装 Node.js >= 18"
        exit 1
    }
    $ver = (node -v) -replace 'v', ''
    $major = [int]($ver.Split('.')[0])
    if ($major -lt 18) {
        Write-Err "Node.js 版本过低: v$ver，需要 >= 18"
        exit 1
    }
    if (-not $EnsureLatest) {
        Write-OK "Node.js v$ver"
    }
}

function Read-LocalVersion {
    $pkg = Join-Path $INSTALL_DIR "package.json"
    if (-not (Test-Path $pkg)) { return "" }
    try {
        $json = Get-Content -Raw -Path $pkg | ConvertFrom-Json
        if ($json.version) { return [string]$json.version }
    } catch {}
    return ""
}

function Test-VersionGreater([string]$a, [string]$b) {
    if (-not $b) { return $true }
    if (-not $a) { return $false }
    if ($a -eq $b) { return $false }
    $va = [version](($a -split '-')[0])
    $vb = [version](($b -split '-')[0])
    return ($va -gt $vb)
}

function Download-UrlToFile([string]$url, [string]$dest) {
    try {
        & curl.exe -fsSL --connect-timeout 5 --max-time 60 $url -o $dest
        if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
    } catch {
        $req = [System.Net.HttpWebRequest]::Create($url)
        $req.Timeout = 60000
        $req.ReadWriteTimeout = 60000
        $resp = $req.GetResponse()
        try {
            $stream = $resp.GetResponseStream()
            $file = [System.IO.File]::Create($dest)
            try { $stream.CopyTo($file) } finally { $file.Dispose() }
        } finally {
            $resp.Dispose()
        }
    }
}

function Download-UrlText([string]$url) {
    try {
        $text = & curl.exe -fsSL --connect-timeout 5 --max-time 30 $url
        if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
        return [string]$text
    } catch {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
        return [string]$resp.Content
    }
}

function Download-Tgz([string]$url, [string]$dest) {
    Write-Warn "下载 CLI 包 ..."
    Write-Log "  $url"
    Download-UrlToFile $url $dest
    if (-not (Test-Path $dest) -or ((Get-Item $dest).Length -le 0)) {
        Write-Err "下载失败或文件为空"
        exit 1
    }
    Write-OK "下载完成"
}

function Install-FromTgz([string]$tgzPath) {
    $tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("slclaw-install-" + [guid]::NewGuid().ToString("n"))
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    try {
        Write-Warn "解压并安装到 $INSTALL_DIR ..."
        & tar.exe -xzf $tgzPath -C $tmpDir
        if ($LASTEXITCODE -ne 0) {
            Write-Err "解压 tgz 失败（需要 Windows 自带 tar）"
            exit 1
        }

        $pkgJson = Get-ChildItem -Path $tmpDir -Filter package.json -Recurse -File |
            Where-Object { $_.Directory.Name -eq 'package' } |
            Select-Object -First 1
        if (-not $pkgJson) {
            $pkgJson = Get-ChildItem -Path $tmpDir -Filter package.json -Recurse -File | Select-Object -First 1
        }
        if (-not $pkgJson) {
            Write-Err "tgz 内容无效：未找到 package.json"
            exit 1
        }
        $pkgDir = $pkgJson.Directory.FullName
        if (-not (Test-Path (Join-Path $pkgDir "dist"))) {
            Write-Err "tgz 内容无效：未找到 dist/"
            exit 1
        }

        if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
        if (-not (Test-Path $SL_HOME)) { New-Item -ItemType Directory -Path $SL_HOME -Force | Out-Null }
        # 全量安装已写入最新 bin，丢弃陈旧 pending/锁，避免下次启动降级
        foreach ($stale in @(
            (Join-Path $SL_HOME "pending-update"),
            (Join-Path $SL_HOME "update-stage.lock")
        )) {
            if (Test-Path $stale) { Remove-Item -Recurse -Force $stale }
        }
        Get-ChildItem -Path $SL_HOME -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'tmp-update-*' -or $_.Name -like 'pending-update.staging-*' } |
            ForEach-Object { Remove-Item -Recurse -Force $_.FullName }

        Copy-Item -Recurse (Join-Path $pkgDir "dist") (Join-Path $INSTALL_DIR "dist")
        Copy-Item (Join-Path $pkgDir "package.json") (Join-Path $INSTALL_DIR "package.json")
        if (Test-Path (Join-Path $SCRIPT_DIR "default.env")) {
            Copy-Item (Join-Path $SCRIPT_DIR "default.env") (Join-Path $INSTALL_DIR "default.env")
            Copy-Item (Join-Path $SCRIPT_DIR "default.env") (Join-Path $SL_HOME "default.env")
        }
        if (Test-Path $URL_CONF) {
            Copy-Item $URL_CONF $HomeUrlConf -Force
        }

        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        $wrapper = @'
#!/usr/bin/env node
require('./dist/cli/src/index.js');
'@
        [System.IO.File]::WriteAllText((Join-Path $INSTALL_DIR "sl"), ($wrapper.TrimEnd() + "`n"), $utf8NoBom)

        # 单引号 here-string，避免批处理里的 % / & / " 被 PowerShell 解析
        $bat = @'
@echo off
setlocal EnableExtensions
set "BIN=%~dp0"
set "SL_HOME=%BIN%.."
set "PENDING=%SL_HOME%\pending-update"
if not exist "%PENDING%\ready" goto :run
if not exist "%PENDING%\dist" goto :discard_pending
if not exist "%PENDING%\package.json" goto :discard_pending
rd /s /q "%BIN%dist.new" 2>nul
rd /s /q "%BIN%dist.bak" 2>nul
del /f /q "%BIN%package.json.new" 2>nul
del /f /q "%BIN%package.json.bak" 2>nul
xcopy /e /i /y "%PENDING%\dist" "%BIN%dist.new\" >nul
if errorlevel 1 (
  rd /s /q "%BIN%dist.new" 2>nul
  goto :discard_pending
)
copy /y "%PENDING%\package.json" "%BIN%package.json.new" >nul
if errorlevel 1 (
  rd /s /q "%BIN%dist.new" 2>nul
  del /f /q "%BIN%package.json.new" 2>nul
  goto :discard_pending
)
if exist "%BIN%dist" (
  ren "%BIN%dist" dist.bak
  if errorlevel 1 (
    rd /s /q "%BIN%dist.new" 2>nul
    del /f /q "%BIN%package.json.new" 2>nul
    goto :discard_pending
  )
)
ren "%BIN%dist.new" dist
if errorlevel 1 (
  if exist "%BIN%dist.bak" ren "%BIN%dist.bak" dist
  rd /s /q "%BIN%dist.new" 2>nul
  del /f /q "%BIN%package.json.new" 2>nul
  goto :discard_pending
)
if exist "%BIN%package.json" (
  ren "%BIN%package.json" package.json.bak
)
ren "%BIN%package.json.new" package.json
if errorlevel 1 (
  if exist "%BIN%package.json.bak" ren "%BIN%package.json.bak" package.json
  goto :discard_pending
)
rd /s /q "%BIN%dist.bak" 2>nul
del /f /q "%BIN%package.json.bak" 2>nul
rd /s /q "%PENDING%" 2>nul
goto :run
:discard_pending
rd /s /q "%PENDING%" 2>nul
:run
node "%BIN%dist\cli\src\index.js" %*
'@
        [System.IO.File]::WriteAllText((Join-Path $INSTALL_DIR "sl.cmd"), ($bat.TrimEnd() + "`r`n"), $utf8NoBom)

        if (Test-Path (Join-Path $SCRIPT_DIR "skills")) {
            if (Test-Path (Join-Path $SL_HOME "skills")) { Remove-Item -Recurse -Force (Join-Path $SL_HOME "skills") }
            Copy-Item -Recurse (Join-Path $SCRIPT_DIR "skills") (Join-Path $SL_HOME "skills")
        }

        Write-OK "文件安装完成"
    } finally {
        if (Test-Path $tmpDir) { Remove-Item -Recurse -Force $tmpDir }
    }
}

function Init-Env {
    $env_file = "$SL_HOME\.env"
    $default_env_file = "$SCRIPT_DIR\default.env"
    $needs_init = $false
    $saved_key = $null

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
    Write-Log "  如需在普通终端直接使用，请手动将 $INSTALL_DIR 添加到用户 PATH。"
}

function Verify-Install {
    $version = Read-LocalVersion
    if (-not $version) { $version = "unknown" }
    Write-OK "安装成功: sl v$version"
}

function Invoke-FullInstall([string]$tgzUrl) {
    Check-Node
    $tmpTgz = Join-Path ([System.IO.Path]::GetTempPath()) ("slclaw-cli-" + [guid]::NewGuid().ToString("n") + ".tgz")
    try {
        Download-Tgz $tgzUrl $tmpTgz
        Install-FromTgz $tmpTgz
        Init-Env
        Setup-Path
        Verify-Install
    } finally {
        if (Test-Path $tmpTgz) { Remove-Item -Force $tmpTgz }
    }
}

function Invoke-EnsureLatest {
    $tgzUrl = Get-TgzUrl
    Assert-TgzUrl $tgzUrl
    $versionUrl = Get-VersionUrl $tgzUrl
    Check-Node

    $remote = (Download-UrlText $versionUrl).Trim()
    if (-not $remote) {
        Write-Err "无法读取远端版本: $versionUrl"
        exit 1
    }
    $local = Read-LocalVersion

    if (-not (Test-Path (Join-Path $INSTALL_DIR "package.json")) -or (Test-VersionGreater $remote $local)) {
        $localLabel = if ($local) { $local } else { "无" }
        Write-Warn "检测到更新: 本地 $localLabel → 远端 $remote"
        Invoke-FullInstall $tgzUrl
        $local = Read-LocalVersion
    } else {
        Write-OK "已是最新: v$local"
    }

    if (-not $local) { $local = "unknown" }
    Write-Output $local
}

# === Main ===
if ($Uninstall) { Do-Uninstall }

if ($EnsureLatest) {
    Invoke-EnsureLatest
    exit 0
}

if ($Reset) {
    Write-Warn "重置模式：清除所有数据后重新安装"
    if (Test-Path $SL_HOME) { Remove-Item -Recurse -Force $SL_HOME }
}

Write-Log ""
Write-Log "╔═══════════════════════════════════════╗"
Write-Log "║  商龙 CLI 连接器安装 (Windows)        ║"
Write-Log "╚═══════════════════════════════════════╝"
Write-Log ""

$tgzUrl = Get-TgzUrl
Assert-TgzUrl $tgzUrl
Invoke-FullInstall $tgzUrl

Write-Log ""
Write-Log "下一步："
Write-Log "  1. 在 WorkBuddy 中完成连接器授权，或编辑 $SL_HOME\.env 填入 SL_API_KEY"
Write-Log ("  2. 执行 & `"{0}\sl.cmd`" connector status 验证" -f $INSTALL_DIR)
