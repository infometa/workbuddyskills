# Windows 安装步骤（Futu OpenD）

## 安装包说明

Windows 版安装包是 **7z 压缩包**，解压后得到的 `*OpenD-GUI*.exe` 是一个**安装程序**（非最终可执行程序），启动后会弹出安装向导界面，用户需要按指引完成安装。

压缩包内部结构：
```
Futu_OpenD_x.x.xxxx_Windows/
├── Futu_OpenD-GUI_x.x.xxxx_Windows/
│   └── Futu_OpenD-GUI_x.x.xxxx_Windows.exe   ← GUI 版安装程序（安装后生成 %APPDATA%\Futu_OpenD\Futu_OpenD.exe）
├── Futu_OpenD_x.x.xxxx_Windows/
│   ├── FutuOpenD.exe                           ← 命令行版主程序（不要启动这个）
│   ├── FutuOpenD.xml                           ← 配置文件
│   ├── AppData.dat                             ← 数据文件
│   └── ...（DLL 等依赖）
└── README.txt
```

**重要**：`Futu_OpenD-GUI*.exe` 是 GUI 版的安装程序，安装完成后 GUI 版会安装到 `%APPDATA%\Futu_OpenD\Futu_OpenD.exe`。`Futu_OpenD_x.x.xxxx_Windows/` 目录下的 `FutuOpenD.exe` 是命令行版，**不要启动命令行版**。

## PowerShell 下载 + 解压 + 启动安装程序

生成 PowerShell 脚本（install_opend.ps1），**一键完成下载、解压、启动安装程序**。

**启动安装程序后**：
- 如果你具备自动点击屏幕的能力（如通过 MCP 工具截图 + 模拟点击），则帮用户自动完成安装向导的每一步
- 如果不具备自动点击能力，则提示用户："安装程序已启动，请根据弹出的安装向导完成安装。安装完成后 OpenD 会自动启动。"

**重要：PowerShell 脚本中必须使用英文输出**。在 MINGW64/Git Bash 环境下通过 `powershell -ExecutionPolicy Bypass -File` 执行 `.ps1` 脚本时，如果脚本中包含中文字符（如 `Write-Host "正在下载..."`），会因编码问题导致 `TerminatorExpectedAtEndOfString` 解析错误。所有 `Write-Host` 输出必须使用英文。

```powershell
# ===== 富途版，按需替换路径 =====
$url = "https://www.futunn.com/download/fetch-lasted-link?name=opend-windows"
$downloadDir = [Environment]::GetFolderPath("Desktop")  # or user-specified path
$archiveName = "FutuOpenD.7z"
# =====================================================

$archivePath = Join-Path $downloadDir $archiveName
$extractDir = Join-Path $downloadDir "FutuOpenD"

# Step 1: Download
Write-Host "Downloading latest Futu OpenD..."
Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing
$size = [math]::Round((Get-Item $archivePath).Length / 1MB, 2)
Write-Host "Download complete! File size: $size MB"

# Step 2: Extract (requires 7-Zip)
$sevenZip = "C:\Program Files\7-Zip\7z.exe"
if (-not (Test-Path $sevenZip)) {
    $sevenZip = "C:\Program Files (x86)\7-Zip\7z.exe"
}
if (Test-Path $sevenZip) {
    Write-Host "Extracting..."
    & $sevenZip x $archivePath -o"$extractDir" -y | Out-Null
    Write-Host "Extracted to: $extractDir"
} else {
    Write-Host "7-Zip not found. Please extract manually: $archivePath"
    Write-Host "Download 7-Zip: https://www.7-zip.org/download.html"
    Write-Host "Backup link: https://github.com/ip7z/7zip/releases"
    exit 1
}

# Step 3: Launch OpenD installer
$guiExe = Get-ChildItem -Path $extractDir -Recurse -Filter "*OpenD-GUI*.exe" | Select-Object -First 1
if ($guiExe) {
    Write-Host "Launching Futu OpenD installer: $($guiExe.FullName)"
    Start-Process $guiExe.FullName
    Write-Host "Installer launched. Please follow the installation wizard to complete setup."
} else {
    Write-Host "Installer not found. Check directory: $extractDir"
}

# Cleanup
Remove-Item $archivePath -Force
Write-Host "Done! Follow the installer to complete installation."
```

## 路径替换规则

- 默认（桌面）：`$downloadDir = [Environment]::GetFolderPath("Desktop")`
- 用户指定：`$downloadDir = "用户提供的路径"`

## 前置条件

需要安装 7-Zip。如果未安装，脚本会提示，此时告知用户：
- 下载 7-Zip：`https://www.7-zip.org/download.html`
- 备用链接：`https://github.com/ip7z/7zip/releases`
- 或手动右键解压 .7z 文件

## 执行步骤

1. 用 Write 工具将脚本写入临时文件 `install_opend.ps1`
2. 用 Bash 工具执行：`powershell -ExecutionPolicy Bypass -File "install_opend.ps1"`
3. 完成后删除临时脚本：`rm install_opend.ps1`

注意：Bash 工具中 `$` 符号会被转义，必须先写 `.ps1` 文件再执行。
