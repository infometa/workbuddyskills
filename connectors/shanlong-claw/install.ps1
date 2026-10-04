#Requires -Version 5.1
<#
.SYNOPSIS
    商龙 CLI 连接器安装脚本 (Windows)
    从 OSS/CDN 按平台下载 SEA 二进制并安装到 %USERPROFILE%\.slclaw
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
$SeaName = "sl-sea.exe"

function Write-Log($msg) { [Console]::Error.WriteLine($msg) }
function Write-OK($msg) { Write-Log "✓ $msg" }
function Write-Err($msg) { Write-Log "✗ $msg" }
function Write-Warn($msg) { Write-Log "→ $msg" }

function Assert-SafeHome {
    $resolved = [System.IO.Path]::GetFullPath($SL_HOME).TrimEnd('\')
    $userRoot = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\')
    $driveRoot = [System.IO.Path]::GetPathRoot($resolved).TrimEnd('\')
    if (-not $resolved -or $resolved -eq $userRoot -or $resolved -eq $driveRoot) {
        throw "拒绝使用危险的 SL_CLI_HOME: $resolved"
    }
    if (Test-Path $SL_HOME) {
        $item = Get-Item -Force $SL_HOME
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "SL_CLI_HOME 不允许是符号链接或重解析点: $SL_HOME"
        }
    }
}

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

function Normalize-BaseUrl([string]$base) {
    if (-not $base.EndsWith('/')) { return "$base/" }
    return $base
}

function Get-SeaArtifactName {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    switch ($arch) {
        'x64' { return 'sl-win-x64.exe' }
        'arm64' { return 'sl-win-arm64.exe' }
        'x86' { return 'sl-win-x86.exe' }
        default {
            # Fallback for older PowerShell / PROCESSOR_ARCHITECTURE
            $pa = ($env:PROCESSOR_ARCHITECTURE + '').ToUpperInvariant()
            if ($pa -eq 'AMD64') { return 'sl-win-x64.exe' }
            if ($pa -eq 'ARM64') { return 'sl-win-arm64.exe' }
            if ($pa -eq 'X86') { return 'sl-win-x86.exe' }
            throw "不支持的 Windows 架构: $arch / $pa"
        }
    }
}

function Get-BaseUrl {
    if ($env:SL_CLI_BASE_URL) { return (Normalize-BaseUrl $env:SL_CLI_BASE_URL) }
    $url = Get-ConfValue "SL_CLI_BASE_URL"
    if (-not $url) {
        $legacy = Get-ConfValue "SL_CLI_TGZ_URL"
        if ($legacy) {
            Write-Err "install-url.conf 仍使用已废弃的 SL_CLI_TGZ_URL，请改为 SL_CLI_BASE_URL"
            exit 1
        }
        Write-Err "缺少 install-url.conf 或未设置 SL_CLI_BASE_URL"
        exit 1
    }
    return (Normalize-BaseUrl $url)
}

function Get-VersionUrl([string]$baseUrl) {
    if ($env:SL_CLI_VERSION_URL) { return $env:SL_CLI_VERSION_URL }
    $fromConf = Get-ConfValue "SL_CLI_VERSION_URL"
    if ($fromConf) { return $fromConf }
    return "${baseUrl}slclaw-cli.version"
}

function Get-ManifestUrl([string]$baseUrl) {
    if ($env:SL_CLI_MANIFEST_URL) { return $env:SL_CLI_MANIFEST_URL }
    if (-not $env:SL_CLI_BASE_URL) {
        $fromConf = Get-ConfValue "SL_CLI_MANIFEST_URL"
        if ($fromConf) { return $fromConf }
    }
    return "${baseUrl}slclaw-cli.manifest.json"
}

function Assert-BaseUrl([string]$url) {
    if ($url -match 'REPLACE_WITH_YOUR_OSS_HOST') {
        Write-Err "尚未配置真实 OSS/CDN 地址"
        Write-Log "  请编辑: $URL_CONF"
        Write-Log "  或设置环境变量 SL_CLI_BASE_URL 后重试"
        exit 1
    }
}

function Read-LocalVersion {
    $verFile = Join-Path $INSTALL_DIR "version"
    if (Test-Path $verFile) {
        return ((Get-Content -Raw -Path $verFile) -replace '\s', '')
    }
    $pkg = Join-Path $INSTALL_DIR "dist\package.json"
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

function ConvertFrom-FileUrl([string]$url) {
    $uri = [Uri]$url
    if ($uri.IsFile) {
        return $uri.LocalPath
    }
    return $null
}

function Download-UrlToFile([string]$url, [string]$dest) {
    $local = ConvertFrom-FileUrl $url
    if ($local) {
        Copy-Item -Force $local $dest
        return
    }
    try {
        & curl.exe -fsSL --connect-timeout 5 --max-time 300 $url -o $dest
        if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
    } catch {
        $req = [System.Net.HttpWebRequest]::Create($url)
        $req.Timeout = 300000
        $req.ReadWriteTimeout = 300000
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
    $local = ConvertFrom-FileUrl $url
    if ($local) {
        return [string](Get-Content -Raw -Path $local)
    }
    try {
        $text = & curl.exe -fsSL --connect-timeout 5 --max-time 30 $url
        if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
        return [string]$text
    } catch {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
        return [string]$resp.Content
    }
}

function Download-Sea([string]$url, [string]$dest) {
    Write-Warn "下载 CLI 二进制 ..."
    Write-Log "  $url"
    Download-UrlToFile $url $dest
    if (-not (Test-Path $dest) -or ((Get-Item $dest).Length -le 0)) {
        Write-Err "下载失败或文件为空"
        exit 1
    }
    Write-OK "下载完成"
}

function Assert-SeaRunnable([string]$seaPath, [string]$expectedVersion) {
    $previousSkipUpdate = $env:SL_CLI_SKIP_UPDATE
    $validationError = $null
    try {
        $env:SL_CLI_SKIP_UPDATE = "1"
        $output = @(& $seaPath --sl-sea-self-check 2>$null)
        if ($LASTEXITCODE -ne 0) {
            throw "SEA self-check 退出码为 $LASTEXITCODE"
        }
        $raw = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
        if (-not $raw) {
            throw "SEA self-check 未返回结果"
        }
        $check = $raw | ConvertFrom-Json
        if ($check.ok -ne $true) {
            throw "SEA self-check 未通过"
        }
        if ($expectedVersion -and ([string]$check.version) -ne $expectedVersion.Trim()) {
            throw "SEA 版本不匹配: expected=$($expectedVersion.Trim()), actual=$($check.version)"
        }
    } catch {
        $validationError = "SEA 二进制验证失败: $($_.Exception.Message)"
    } finally {
        if ($null -eq $previousSkipUpdate) {
            Remove-Item Env:SL_CLI_SKIP_UPDATE -ErrorAction SilentlyContinue
        } else {
            $env:SL_CLI_SKIP_UPDATE = $previousSkipUpdate
        }
    }
    if ($validationError) { throw $validationError }
    return [string]$check.version
}

function Remove-LegacyProgramAssets {
    foreach ($target in @(
        (Join-Path $SL_HOME "sea"),
        (Join-Path $INSTALL_DIR ".sea-cache"),
        (Join-Path $INSTALL_DIR "dist"),
        (Join-Path $INSTALL_DIR "node_modules")
    )) {
        if (Test-Path -LiteralPath $target) {
            try {
                Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
            } catch {
                Write-Warn "旧程序资产清理失败，将在后续安装时重试: $target"
            }
        }
    }
}

function Get-Sha256Hex([string]$filePath) {
    $stream = [System.IO.File]::OpenRead($filePath)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash($stream)
        return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Assert-SeaMatchesManifest(
    [string]$seaPath,
    [string]$artifactName,
    [string]$expectedVersion,
    $manifest
) {
    if (-not $manifest -or [int]$manifest.schemaVersion -ne 1) {
        throw "SEA manifest schemaVersion 无效"
    }
    if ([string]$manifest.scope -ne "S1-only") {
        throw "SEA manifest scope 必须为 S1-only"
    }
    if ([string]$manifest.version -ne $expectedVersion) {
        throw "SEA manifest 版本不匹配: manifest=$($manifest.version), version=$expectedVersion"
    }
    $artifactProperty = $manifest.artifacts.PSObject.Properties[$artifactName]
    if (-not $artifactProperty) {
        throw "SEA manifest 缺少当前平台产物: $artifactName"
    }
    $artifact = $artifactProperty.Value
    $actualSize = (Get-Item -LiteralPath $seaPath).Length
    if ([Int64]$artifact.size -ne $actualSize) {
        throw "SEA 文件大小不匹配: expected=$($artifact.size), actual=$actualSize"
    }
    $actualHash = Get-Sha256Hex $seaPath
    $expectedHash = ([string]$artifact.sha256).ToLowerInvariant()
    if (-not $expectedHash -or $actualHash -ne $expectedHash) {
        throw "SEA SHA-256 校验失败: expected=$expectedHash, actual=$actualHash"
    }
}

function Write-WindowsWrappers([string]$targetDir = $INSTALL_DIR) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $bat = @'
@echo off
setlocal EnableExtensions
set "BIN=%~dp0"
set "SL_HOME=%BIN%.."
set "PENDING=%SL_HOME%\pending-update"
set "SEA=%BIN%sl-sea.exe"
set "SL_MAX_SECURITY_LEVEL=S1"

if not exist "%PENDING%\ready" goto :run
if not exist "%PENDING%\sl-sea.exe" goto :discard_pending
for %%A in ("%PENDING%\sl-sea.exe") do if %%~zA==0 goto :discard_pending

del /f /q "%SEA%.new" 2>nul
del /f /q "%SEA%.bak" 2>nul
copy /y "%PENDING%\sl-sea.exe" "%SEA%.new" >nul
if errorlevel 1 goto :discard_pending
if exist "%SEA%" (
  ren "%SEA%" "sl-sea.exe.bak"
  if errorlevel 1 (
    del /f /q "%SEA%.new" 2>nul
    goto :run
  )
)
ren "%SEA%.new" "sl-sea.exe"
if errorlevel 1 (
  if exist "%BIN%sl-sea.exe.bak" ren "%BIN%sl-sea.exe.bak" "sl-sea.exe"
  del /f /q "%SEA%.new" 2>nul
  goto :run
)

set "EXPECTED_VERSION="
set /p EXPECTED_VERSION=<"%PENDING%\ready"
set "SELF_CHECK_FILE=%PENDING%\self-check.json"
set "SL_CLI_SKIP_UPDATE=1"
"%SEA%" --sl-sea-self-check >"%SELF_CHECK_FILE%" 2>nul
if errorlevel 1 goto :rollback_pending
findstr /C:"\"ok\":true" "%SELF_CHECK_FILE%" >nul || goto :rollback_pending
findstr /C:"\"version\":\"%EXPECTED_VERSION%\"" "%SELF_CHECK_FILE%" >nul || goto :rollback_pending

"%SEA%" --sl-config-migrate --home "%SL_HOME%" >"%PENDING%\config-result.json" 2>nul
if errorlevel 1 goto :rollback_pending
findstr /C:"\"ok\":true" "%PENDING%\config-result.json" >nul || goto :rollback_pending
findstr /C:"\"status\":\"conflict\"" "%PENDING%\config-result.json" >nul && type "%PENDING%\config-result.json" 1>&2

if exist "%PENDING%\ready" copy /y "%PENDING%\ready" "%BIN%version" >nul
if exist "%BIN%sl-sea.exe.bak" del /f /q "%BIN%sl-sea.exe.bak" 2>nul
rd /s /q "%PENDING%" 2>nul
rd /s /q "%SL_HOME%\sea" 2>nul
rd /s /q "%BIN%.sea-cache" 2>nul
rd /s /q "%BIN%dist" 2>nul
rd /s /q "%BIN%node_modules" 2>nul
goto :run

:rollback_pending
del /f /q "%SEA%" 2>nul
if exist "%BIN%sl-sea.exe.bak" ren "%BIN%sl-sea.exe.bak" "sl-sea.exe"
rd /s /q "%PENDING%" 2>nul
goto :run

:discard_pending
rd /s /q "%PENDING%" 2>nul
del /f /q "%SEA%.new" 2>nul

:run
if not exist "%SEA%" (
  echo sl-sea.exe missing: %SEA% 1>&2
  exit /b 1
)
"%SEA%" %*
'@
    [System.IO.File]::WriteAllText((Join-Path $targetDir "sl.cmd"), ($bat.TrimEnd() + "`r`n"), $utf8NoBom)

    # 兼容可能直接调用 bin/sl 的场景
    $shim = @'
#!/usr/bin/env node
console.error('Use sl.cmd on Windows');
process.exit(1);
'@
    [System.IO.File]::WriteAllText((Join-Path $targetDir "sl"), ($shim.TrimEnd() + "`n"), $utf8NoBom)
}

function Restore-InstallDirFromBackup([string]$installDir, [string]$backupDir) {
    if ((Test-Path $backupDir) -and -not (Test-Path $installDir)) {
        [System.IO.Directory]::Move($backupDir, $installDir)
    }
}

function Restore-InPlaceInstallBackup([string]$installDir) {
    $sea = Join-Path $installDir $SeaName
    $seaBackup = "$sea.bak"
    if (-not (Test-Path -LiteralPath $seaBackup)) { return }

    if (Test-Path -LiteralPath $sea) { Remove-Item -LiteralPath $sea -Force -ErrorAction SilentlyContinue }
    Rename-Item -LiteralPath $seaBackup -NewName $SeaName

    $version = Join-Path $installDir "version"
    $versionBackup = "$version.bak"
    if (Test-Path -LiteralPath $version) { Remove-Item -LiteralPath $version -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $versionBackup) {
        Rename-Item -LiteralPath $versionBackup -NewName "version"
    }
}

function Remove-InPlaceInstallBackup([string]$installDir) {
    foreach ($backup in @(
        ((Join-Path $installDir $SeaName) + ".bak"),
        ((Join-Path $installDir "version") + ".bak")
    )) {
        if (Test-Path -LiteralPath $backup) {
            Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
        }
    }
}

function Install-InPlaceFromStaged([string]$newDir, [string]$installDir) {
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }

    $seaSrc = Join-Path $newDir $SeaName
    $seaDst = Join-Path $installDir $SeaName
    $seaNew = "$seaDst.new"
    $seaBak = "$seaDst.bak"
    $verSrc = Join-Path $newDir "version"
    $replacedSea = $false

    if (Test-Path $seaNew) { Remove-Item -Force $seaNew }
    Copy-Item -Force $seaSrc $seaNew
    try {
        if (Test-Path $seaBak) { Remove-Item -Force $seaBak }
        if (Test-Path $seaDst) {
            Rename-Item -Path $seaDst -NewName "$SeaName.bak"
        }
        Rename-Item -Path $seaNew -NewName $SeaName
        $replacedSea = $true
    } catch {
        if ((-not (Test-Path $seaDst)) -and (Test-Path $seaBak)) {
            try { Rename-Item -Path $seaBak -NewName $SeaName } catch {}
        }
        if (Test-Path $seaNew) { Remove-Item -Force $seaNew -ErrorAction SilentlyContinue }

        $pending = Join-Path $SL_HOME "pending-update"
        if (Test-Path $pending) { Remove-Item -Recurse -Force $pending }
        New-Item -ItemType Directory -Path $pending -Force | Out-Null
        Copy-Item -Force $seaSrc (Join-Path $pending $SeaName)
        if (Test-Path $verSrc) {
            Copy-Item -Force $verSrc (Join-Path $pending "ready")
        } else {
            [System.IO.File]::WriteAllText((Join-Path $pending "ready"), "unknown`n")
        }
        Write-Warn "sl-sea.exe is locked; staged pending-update for next sl.cmd start"
    }

    if ($replacedSea -and (Test-Path $verSrc)) {
        $verDst = Join-Path $installDir "version"
        $verBak = "$verDst.bak"
        if (Test-Path -LiteralPath $verBak) { Remove-Item -LiteralPath $verBak -Force }
        if (Test-Path -LiteralPath $verDst) { Copy-Item -LiteralPath $verDst -Destination $verBak -Force }
        Copy-Item -Force $verSrc (Join-Path $installDir "version")
    }
    foreach ($name in @('sl.cmd', 'sl')) {
        $src = Join-Path $newDir $name
        if (Test-Path $src) { Copy-Item -Force $src (Join-Path $installDir $name) }
    }
    Remove-Item -Recurse -Force $newDir -ErrorAction SilentlyContinue
}

function Switch-InstallDir([string]$newDir, [string]$installDir, [string]$backupDir) {
    $attempts = 6
    $lastError = $null
    for ($i = 1; $i -le $attempts; $i++) {
        try {
            if (Test-Path $backupDir) { Remove-Item -Recurse -Force $backupDir }
            if (Test-Path $installDir) {
                [System.IO.Directory]::Move($installDir, $backupDir)
            }
            if (Test-Path $installDir) {
                throw "install dir still present after move: $installDir"
            }
            [System.IO.Directory]::Move($newDir, $installDir)
            return
        } catch {
            $lastError = $_
            try { Restore-InstallDirFromBackup $installDir $backupDir } catch {}
            Start-Sleep -Milliseconds (300 * $i)
        }
    }

    Write-Warn ("directory swap failed after retries: {0}; falling back to in-place install" -f $lastError.Exception.Message)
    try {
        Install-InPlaceFromStaged $newDir $installDir
    } catch {
        if (Test-Path $newDir) { Remove-Item -Recurse -Force $newDir -ErrorAction SilentlyContinue }
        try { Restore-InPlaceInstallBackup $installDir } catch {}
        try { Restore-InstallDirFromBackup $installDir $backupDir } catch {}
        throw ("CLI install swap failed (Windows file lock?). Close WorkBuddy/sl processes and retry. Detail: {0}" -f $_.Exception.Message)
    }
}

function Install-FromSea([string]$seaPath, [string]$remoteVersion) {
    Write-Warn "安装到 $INSTALL_DIR ..."
    $newDir = "$INSTALL_DIR.new"
    $backupDir = "$INSTALL_DIR.bak"

    if (-not (Test-Path $SL_HOME)) { New-Item -ItemType Directory -Path $SL_HOME -Force | Out-Null }
    foreach ($stale in @(
        (Join-Path $SL_HOME "pending-update"),
        (Join-Path $SL_HOME "update-stage.lock")
    )) {
        if (Test-Path $stale) { Remove-Item -Recurse -Force $stale }
    }
    Get-ChildItem -Path $SL_HOME -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'tmp-update-*' -or $_.Name -like 'pending-update.staging-*' } |
        ForEach-Object { Remove-Item -Recurse -Force $_.FullName }

    if (Test-Path $newDir) { Remove-Item -Recurse -Force $newDir }
    if (Test-Path $backupDir) { Remove-Item -Recurse -Force $backupDir }
    New-Item -ItemType Directory -Path $newDir -Force | Out-Null

    Copy-Item -Force $seaPath (Join-Path $newDir $SeaName)
    if ($remoteVersion) {
        [System.IO.File]::WriteAllText((Join-Path $newDir "version"), ($remoteVersion.Trim() + "`n"))
    }

    Write-WindowsWrappers $newDir
    Switch-InstallDir $newDir $INSTALL_DIR $backupDir

    if (Test-Path $URL_CONF) {
        Copy-Item $URL_CONF $HomeUrlConf -Force
    }

    # Skills 由 WorkBuddy 从连接器 zip 加载；始终清理旧 tgz 布局。
    $legacySkills = Join-Path $SL_HOME "skills"
    if (Test-Path $legacySkills) { Remove-Item -Recurse -Force $legacySkills }

    if (Test-Path (Join-Path $SL_HOME ".DS_Store")) { Remove-Item -Force (Join-Path $SL_HOME ".DS_Store") }

    Write-OK "文件安装完成"
}

function Init-Env {
    if (Test-Path -LiteralPath (Join-Path $SL_HOME 'pending-update/ready')) {
        Write-Warn '配置迁移随 pending-update 激活执行，当前配置保持不变'
        return
    }
    $sea = Join-Path $INSTALL_DIR $SeaName
    $resultText = & $sea --sl-config-migrate --home $SL_HOME
    if ($LASTEXITCODE -ne 0) { throw 'config-migration-failed' }
    try { $result = ($resultText -join "`n") | ConvertFrom-Json } catch { throw 'config-migration-invalid-result' }
    if ($result.ok -ne $true) { throw 'config-migration-failed' }
    if ($result.status -eq 'conflict') {
        Write-Warn ('配置已同步；保留需确认的自定义字段: ' + ($result.fields -join ', '))
    } else { Write-OK ('配置迁移: ' + $result.status) }
}

function Setup-Path {
    $env:Path = "$INSTALL_DIR;$env:Path"
    Write-Warn "未自动修改用户 PATH；WorkBuddy 将通过 cli.json 中的绝对路径调用 sl.cmd"
    Write-Log "  如需在普通终端直接使用，请手动将 $INSTALL_DIR 添加到用户 PATH。"
}

function Verify-Install {
    $entry = Join-Path $INSTALL_DIR 'sl.cmd'
    if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) {
        throw '安装验证失败: sl.cmd 缺失'
    }
    $pendingReady = Join-Path (Join-Path $SL_HOME "pending-update") "ready"
    if (Test-Path $pendingReady) {
        Write-Warn "新版本已暂存，等待下次 sl.cmd 启动时应用"
        return
    }
    $version = Read-LocalVersion
    if (-not $version) { $version = "unknown" }
    $sea = Join-Path $INSTALL_DIR $SeaName
    if (Test-Path $sea) {
        try {
            Assert-SeaRunnable $sea $version | Out-Null
            $previousSkipUpdate = $env:SL_CLI_SKIP_UPDATE
            try {
                $env:SL_CLI_SKIP_UPDATE = '1'
                $entryVersion = ((@(& $entry --version) | ForEach-Object { [string]$_ }) -join "`n").Trim()
                if ($LASTEXITCODE -ne 0 -or $entryVersion -ne $version) {
                    throw 'sl.cmd 版本验证失败'
                }
            } finally {
                if ($null -eq $previousSkipUpdate) { Remove-Item Env:SL_CLI_SKIP_UPDATE -ErrorAction SilentlyContinue }
                else { $env:SL_CLI_SKIP_UPDATE = $previousSkipUpdate }
            }
            Write-OK "安装成功: sl v$version"
            return
        } catch {}
    }
    throw "安装验证失败: SEA self-check 未通过"
}

function Invoke-FullInstall([string]$baseUrl, [string]$versionUrl) {
    $artifact = Get-SeaArtifactName
    $artifactUrl = "$baseUrl$artifact"
    $manifestUrl = Get-ManifestUrl $baseUrl
    $tmpSea = Join-Path ([System.IO.Path]::GetTempPath()) ("slclaw-cli-" + [guid]::NewGuid().ToString("n") + ".exe")
    try {
        Download-Sea $artifactUrl $tmpSea
        $remote = ""
        try { $remote = (Download-UrlText $versionUrl).Trim() } catch {}
        if (-not $remote) {
            throw "无法读取远端版本: $versionUrl"
        }
        $manifest = (Download-UrlText $manifestUrl) | ConvertFrom-Json
        Assert-SeaMatchesManifest $tmpSea $artifact $remote $manifest
        Assert-SeaRunnable $tmpSea $remote | Out-Null
        try {
            Install-FromSea $tmpSea $remote
            Setup-Path
            Verify-Install
            Init-Env
        } catch {
            $backupDir = "$INSTALL_DIR.bak"
            try { Restore-InPlaceInstallBackup $INSTALL_DIR } catch {}
            if (Test-Path $backupDir) {
                if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
                Move-Item $backupDir $INSTALL_DIR
            }
            throw
        }
        # Configuration is committed. Cleanup must never roll back only the binary.
        try {
            $pendingReady = Join-Path (Join-Path $SL_HOME "pending-update") "ready"
            if (-not (Test-Path -LiteralPath $pendingReady)) { Remove-LegacyProgramAssets }
            Remove-InPlaceInstallBackup $INSTALL_DIR
            $backupDir = "$INSTALL_DIR.bak"
            if (Test-Path $backupDir) { Remove-Item -Recurse -Force $backupDir }
        } catch { Write-Warn '安装已完成；旧版本备份清理失败，保留供后续清理' }
    } finally {
        if (Test-Path $tmpSea) { Remove-Item -Force $tmpSea -ErrorAction SilentlyContinue }
    }
}

function Invoke-EnsureLatest {
    $baseUrl = Get-BaseUrl
    Assert-BaseUrl $baseUrl
    $versionUrl = Get-VersionUrl $baseUrl

    $remote = (Download-UrlText $versionUrl).Trim()
    if (-not $remote) {
        Write-Err "无法读取远端版本: $versionUrl"
        exit 1
    }
    $local = Read-LocalVersion
    $seaPath = Join-Path $INSTALL_DIR $SeaName
    $hasOldDist = Test-Path (Join-Path $INSTALL_DIR "dist")

    if (-not (Test-Path $seaPath) -or $hasOldDist -or (Test-VersionGreater $remote $local)) {
        $localLabel = if ($local) { $local } else { "无" }
        Write-Warn "检测到更新: 本地 $localLabel → 远端 $remote"
        Invoke-FullInstall $baseUrl $versionUrl
        $local = Read-LocalVersion
    } else {
        if (-not (Test-Path -LiteralPath (Join-Path $INSTALL_DIR 'sl.cmd') -PathType Leaf)) {
            Write-WindowsWrappers
        }
        Verify-Install
        Init-Env
        Write-OK "已是最新: v$local"
    }

    if (-not $local) { $local = "unknown" }
    Write-Output $local
}

# === Main ===
Assert-SafeHome
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

$baseUrl = Get-BaseUrl
Assert-BaseUrl $baseUrl
$versionUrl = Get-VersionUrl $baseUrl
Invoke-FullInstall $baseUrl $versionUrl

Write-Log ""
Write-Log "下一步："
Write-Log "  1. 在 WorkBuddy 中完成连接器授权，或编辑 $SL_HOME\.env 填入 SL_API_KEY"
Write-Log ("  2. 执行 & `"{0}\sl.cmd`" connector status 验证" -f $INSTALL_DIR)
