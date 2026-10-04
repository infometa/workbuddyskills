# 下载后版本一致性校验（Futu OpenD）

下载并解压完成后、启动安装程序前，**必须验证解压出的安装文件版本与预期下载的最新版本（`LATEST_VER`）一致**，防止 CDN 缓存、下载中断或镜像不同步导致实际安装文件版本不符。

## 校验原理

解压后的目录名和安装文件名中均包含版本号（如 `Futu_OpenD-GUI_10.1.6108_Windows.exe`）。校验方式为：在解压目录中**查找文件名包含预期版本号（`LATEST_VER`）的 GUI 安装程序**，找到则校验通过，找不到则校验失败。

**注意**：压缩包可能同时包含多个版本的目录（如同时包含 `10.2.6208` 和 `10.1.6108`），因此**不能用 `Select-Object -First 1` 或 `head -1` 取第一个匹配再对比版本号**，必须直接按预期版本号筛选文件。

## Windows

在解压完成后、启动安装程序前执行校验：

```powershell
# Step 2.5: Verify expected version exists in extracted files
$guiExe = Get-ChildItem -Path $extractDir -Recurse -Filter "*OpenD-GUI*$latestVer*.exe" | Select-Object -First 1
if ($guiExe) {
    Write-Host "Version verified: found $($guiExe.Name) (matches expected $latestVer)"
} else {
    # Fallback: list all GUI exe versions found for diagnosis
    $allGui = Get-ChildItem -Path $extractDir -Recurse -Filter "*OpenD-GUI*.exe"
    $foundVersions = ($allGui | ForEach-Object { if ($_.Name -match '(\d+\.\d+\.\d+)') { $Matches[1] } }) -join ", "
    Write-Host "WARNING: Expected version $latestVer not found in extracted files."
    Write-Host "Found versions: $foundVersions"
    Write-Host "The download may not contain the expected version. Aborting installation."
    exit 1
}
```

**注意**：`$latestVer` 需在脚本顶部通过获取重定向 URL 或下载链接文件名提取并传入。校验通过后，后续步骤应使用此处找到的 `$guiExe` 来启动安装程序。

## macOS

在解压完成后（第三步）、挂载 DMG 前（第四步）执行校验：

```bash
DMG_FILE=$(find "$HOME/Desktop" -maxdepth 3 -name "*OpenD-GUI*${LATEST_VER}*.dmg" -type f | head -1)
if [ -n "$DMG_FILE" ]; then
    echo "Version verified: found $(basename "$DMG_FILE") (matches expected $LATEST_VER)"
else
    # List all GUI DMG versions found for diagnosis
    ALL_DMG=$(find "$HOME/Desktop" -maxdepth 3 -name "*OpenD-GUI*.dmg" -type f 2>/dev/null)
    echo "WARNING: Expected version $LATEST_VER not found in extracted files."
    echo "Found DMG files: $ALL_DMG"
    echo "The download may not contain the expected version. Aborting installation."
    exit 1
fi
```

如果用户通过 `-path` 指定了路径，将 `$HOME/Desktop` 替换为对应路径。校验通过后，后续挂载步骤应使用此处找到的 `$DMG_FILE`。

## Linux

在解压完成后、安装 GUI 包前执行校验：

```bash
# Ubuntu/Debian
PKG_FILE=$(find ~/Desktop -maxdepth 3 \( -name "*OpenD-GUI*${LATEST_VER}*.deb" -o -name "*OpenD-GUI*${LATEST_VER}*.rpm" \) -type f 2>/dev/null | head -1)

# CentOS/RHEL
# PKG_FILE=$(find ~/Desktop -maxdepth 3 -name "*OpenD-GUI*${LATEST_VER}*.rpm" -type f | head -1)

if [ -n "$PKG_FILE" ]; then
    echo "Version verified: found $(basename "$PKG_FILE") (matches expected $LATEST_VER)"
else
    ALL_PKG=$(find ~/Desktop -maxdepth 3 \( -name "*OpenD-GUI*.deb" -o -name "*OpenD-GUI*.rpm" \) -type f 2>/dev/null)
    echo "WARNING: Expected version $LATEST_VER not found in extracted files."
    echo "Found packages: $ALL_PKG"
    echo "The download may not contain the expected version. Aborting installation."
    exit 1
fi
```

如果用户通过 `-path` 指定了路径，将 `~/Desktop` 替换为对应路径。校验通过后，后续安装步骤应使用此处找到的 `$PKG_FILE`。

## 校验失败处理

| 情况 | 动作 |
|------|------|
| 找到预期版本文件 | 输出 "Version verified: found xxx"，继续安装流程 |
| 未找到预期版本文件 | 输出警告并列出实际找到的版本，**中止安装**，提示下载内容可能不包含预期版本 |
