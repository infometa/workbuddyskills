# 版本检测脚本（Futu OpenD）

## 获取线上最新版本号

通过 `fetch-lasted-link` API 的重定向 URL 提取最新版本号（`{platform}` 根据 `detected_os` 替换为 `windows`、`macos`、`centos` 或 `ubuntu`）。

### macOS / Linux

```bash
LATEST_URL=$(curl -sI "https://www.futunn.com/download/fetch-lasted-link?name=opend-{platform}" | grep -i "^location:" | awk '{print $2}' | tr -d '\r')
LATEST_VER=$(echo "$LATEST_URL" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
echo "Latest version: $LATEST_VER"
```

### Windows

生成 PowerShell 脚本获取（避免 Bash 中 `$` 转义问题）：

```powershell
$response = Invoke-WebRequest -Uri "https://www.futunn.com/download/fetch-lasted-link?name=opend-windows" -MaximumRedirection 0 -ErrorAction SilentlyContinue
$redirectUrl = $response.Headers.Location
if ($redirectUrl -match '(\d+\.\d+\.\d+)') { Write-Host "LATEST_VER=$($Matches[1])" }
```

## 检测本地已安装版本

### Windows

生成 PowerShell 脚本，依次通过以下方式检测本地已安装版本。检测目标为富途版：`Futu_OpenD`。

1. 从注册表卸载信息中读取 `DisplayVersion`（最可靠，GUI 版安装后会写入注册表）
2. 检测当前运行中的 Futu_OpenD GUI 版进程
3. 在常见安装路径下搜索 GUI 版可执行文件

**注意（仅 Windows）**：GUI 版可执行文件的 `VersionInfo.ProductVersion` 为空，不能通过文件属性获取版本号，必须优先从注册表读取。macOS 和 Linux 不受此问题影响。

```powershell
$localVer = "not_installed"
$targetName = "Futu_OpenD"
$processName = "Futu_OpenD"
$installDir = "Futu_OpenD"

# Method 1: Check registry uninstall entries (most reliable)
# GUI installer writes DisplayVersion to HKCU uninstall registry
$regPaths = @(
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)
foreach ($regPath in $regPaths) {
    if ($localVer -ne "not_installed") { break }
    if (-not (Test-Path $regPath)) { continue }
    Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue | ForEach-Object {
        $props = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ($props.DisplayName -eq $targetName -and $props.DisplayVersion) {
            if ($props.DisplayVersion -match '(\d+\.\d+\.\d+)') {
                $localVer = $Matches[1]
            }
        }
    }
}

# Method 2: Check running GUI OpenD process
if ($localVer -eq "not_installed") {
    $proc = Get-Process -Name $processName -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($proc -and $proc.Path) {
        # ProductVersion may be empty for GUI OpenD, try path-based extraction
        if ($proc.Path -match '(\d+\.\d+\.\d+)') {
            $localVer = $Matches[1]
        }
    }
}

# Method 3: Check if GUI OpenD executable exists at default install path
if ($localVer -eq "not_installed") {
    $guiPath = Join-Path $env:APPDATA "$installDir\$processName.exe"
    if (Test-Path $guiPath) {
        # Executable exists but has no version info embedded; mark as installed with unknown version
        $localVer = "installed_unknown"
    }
}

Write-Host "LOCAL_VER=$localVer"
```

### macOS

依次通过以下方式检测，使用富途版对应名称：

```bash
LOCAL_VER="not_installed"
BRAND_PREFIX="Futu"
# Possible app names: installer may use different naming conventions
APP_NAMES=("Futu_OpenD" "Futu OpenD-GUI" "Futu OpenD")

# Method 1: Check running Futu OpenD process and read version from its app bundle
OPEND_PID=$(pgrep -f "${BRAND_PREFIX}_OpenD" 2>/dev/null | head -1)
if [ -n "$OPEND_PID" ]; then
    # Use full command path (args=) instead of comm= to locate the .app bundle
    OPEND_FULL_PATH=$(ps -p "$OPEND_PID" -o args= 2>/dev/null | awk '{print $1}')
    # Extract .app bundle path (everything up to and including .app)
    APP_BUNDLE=$(echo "$OPEND_FULL_PATH" | sed -n 's|\(.*\.app\)/.*|\1|p')
    if [ -n "$APP_BUNDLE" ] && [ -d "$APP_BUNDLE" ]; then
        LOCAL_VER=$(defaults read "$APP_BUNDLE/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "not_installed")
    fi
fi

# Method 2: Read Info.plist from /Applications/ (try all known app names)
if [ "$LOCAL_VER" = "not_installed" ]; then
    for APP_NAME in "${APP_NAMES[@]}"; do
        if [ -d "/Applications/${APP_NAME}.app" ]; then
            LOCAL_VER=$(defaults read "/Applications/${APP_NAME}.app/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "not_installed")
            [ "$LOCAL_VER" != "not_installed" ] && break
        fi
    done
fi

# Method 3: Search common paths for .app bundles or .dmg installers (GUI version has underscore: Futu_OpenD)
if [ "$LOCAL_VER" = "not_installed" ]; then
    FOUND=$(find "$HOME/Desktop" /Applications /opt "$HOME/Downloads" -maxdepth 4 \( -name "${BRAND_PREFIX}_OpenD*.dmg" -o -name "${BRAND_PREFIX}_OpenD*.app" \) 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        # Try reading Info.plist if it's an .app bundle
        if echo "$FOUND" | grep -q '\.app$' && [ -f "$FOUND/Contents/Info.plist" ]; then
            LOCAL_VER=$(defaults read "$FOUND/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "not_installed")
        fi
        # Fall back to extracting version from filename
        if [ "$LOCAL_VER" = "not_installed" ] && echo "$FOUND" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
            LOCAL_VER=$(echo "$FOUND" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
    fi
fi

echo "Local version: $LOCAL_VER"
```

### Linux

依次通过以下方式检测，使用富途版对应名称：

```bash
LOCAL_VER="not_installed"
BRAND_PROCESS="Futu_OpenD"
BRAND_PREFIX="Futu"

# Method 1: Check running OpenD process
OPEND_PID=$(pgrep -f "$BRAND_PROCESS" 2>/dev/null | head -1)
if [ -n "$OPEND_PID" ]; then
    OPEND_PATH=$(readlink -f /proc/"$OPEND_PID"/exe 2>/dev/null)
    # Try extracting version from path first
    if [ -n "$OPEND_PATH" ] && echo "$OPEND_PATH" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
        LOCAL_VER=$(echo "$OPEND_PATH" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    fi
    # If path has no version, try --version or the executable's directory for version info
    if [ "$LOCAL_VER" = "not_installed" ] && [ -n "$OPEND_PATH" ] && [ -x "$OPEND_PATH" ]; then
        VER_OUTPUT=$("$OPEND_PATH" --version 2>/dev/null || true)
        if echo "$VER_OUTPUT" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
            LOCAL_VER=$(echo "$VER_OUTPUT" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
    fi
fi

# Method 2: Search common paths for OpenD executable
if [ "$LOCAL_VER" = "not_installed" ]; then
    OPEND_BIN=$(find "$HOME/Desktop" /opt /usr/local "$HOME/Downloads" -maxdepth 4 -name "$BRAND_PROCESS" -type f 2>/dev/null | head -1)
    if [ -n "$OPEND_BIN" ]; then
        # Try extracting version from path
        if echo "$OPEND_BIN" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
            LOCAL_VER=$(echo "$OPEND_BIN" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
        # If path has no version, try --version
        if [ "$LOCAL_VER" = "not_installed" ] && [ -x "$OPEND_BIN" ]; then
            VER_OUTPUT=$("$OPEND_BIN" --version 2>/dev/null || true)
            if echo "$VER_OUTPUT" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
                LOCAL_VER=$(echo "$VER_OUTPUT" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            fi
        fi
    fi
fi

# Method 3: Search for installer/package by filename (GUI version has underscore: Futu_OpenD)
if [ "$LOCAL_VER" = "not_installed" ]; then
    FOUND=$(find "$HOME/Desktop" /opt /usr/local "$HOME/Downloads" -maxdepth 4 -name "${BRAND_PREFIX}_OpenD*" 2>/dev/null | head -1)
    if [ -n "$FOUND" ] && echo "$FOUND" | grep -qoE '[0-9]+\.[0-9]+\.[0-9]+'; then
        LOCAL_VER=$(echo "$FOUND" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    fi
fi

LOCAL_VER=${LOCAL_VER:-"not_installed"}
echo "Local version: $LOCAL_VER"
```

## 版本对比逻辑

版本号格式为 `X.Y.ZZZZ`（如 `10.2.6208`），按数值逐段对比。

**Bash 对比方法**（macOS / Linux）：

```bash
if [ "$LOCAL_VER" = "not_installed" ]; then
    echo "STATUS=not_installed"
elif printf '%s\n' "$LATEST_VER" "$LOCAL_VER" | sort -V | head -1 | grep -qx "$LATEST_VER"; then
    echo "STATUS=up_to_date"
else
    echo "STATUS=needs_update"
fi
```

**PowerShell 对比方法**（Windows）：

```powershell
if ($localVer -eq "not_installed") {
    Write-Host "STATUS=not_installed"
} elseif ([version]$localVer -ge [version]$latestVer) {
    Write-Host "STATUS=up_to_date"
} else {
    Write-Host "STATUS=needs_update"
}
```

## 根据对比结果执行

| 情况 | 动作 |
|------|------|
| 本地未安装（`not_installed`） | 继续正常下载安装流程 |
| 本地版本 < 最新版本（`needs_update`） | 提示"检测到本地 OpenD 版本 {LOCAL_VER}，最新版本为 {LATEST_VER}，将自动升级"，继续下载安装 |
| 本地版本 ≥ 最新版本（`up_to_date`） | 提示"本地已安装最新版本的Futu OpenD（{LOCAL_VER}），无需重新安装"，**跳过下载和安装步骤**，直接进入 SDK 升级步骤 |
