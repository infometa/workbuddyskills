# 腾讯网盘 tdrive —— WorkBuddy 连接器安装脚本（Windows / PowerShell）
#
# 由 WorkBuddy 连接器的 `init` 命令下载后执行（见 connector/workbuddy/cli.json）。
# 非交互、幂等：已是目标版本则跳过下载；每次都会校验并补齐 WorkBuddy 会话钩子。
#
# 占位符 https://ai-drivecli-1251316161.cos.ap-guangzhou.myqcloud.com / 1.1.1-beta 由 scripts/package-connector.sh 在打包时替换。
#
# 安全约定与 install.sh 一致：只访问白名单域、必须通过 .sha256 校验、失败即中止。

$ErrorActionPreference = "Stop"

$DownloadBaseUrl = "https://ai-drivecli-1251316161.cos.ap-guangzhou.myqcloud.com"
$Version         = "1.1.1-beta"
$InstallDir      = Join-Path $env:LOCALAPPDATA "Programs\tdrive"
$ExePath         = Join-Path $InstallDir "tdrive.exe"

if (-not [Environment]::Is64BitOperatingSystem) {
  Write-Error "不支持的平台：需要 64 位 Windows"
  exit 1
}

$binUrl = "$DownloadBaseUrl/$Version/tdrive-windows-x86_64.exe"
$shaUrl = "$binUrl.sha256"

$needDownload = $true
if (Test-Path $ExePath) {
  try {
    $cur = ((& $ExePath --version) | Select-Object -First 1).Trim().Split(' ')[-1]
    if ($cur -eq $Version) {
      Write-Host "tdrive $cur 已安装，跳过下载。"
      $needDownload = $false
    }
  } catch {
    # 旧二进制损坏/无法执行：按需要重装处理
    $needDownload = $true
  }
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

if ($needDownload) {
  # Windows 会锁定运行中的 exe：覆盖安装前先停后台同步进程（未运行也返回成功）
  if (Test-Path $ExePath) {
    try { & $ExePath sync stop *> $null } catch { }
  }

  $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $tmp | Out-Null
  try {
    $tmpExe = Join-Path $tmp "tdrive.exe"
    $tmpSha = Join-Path $tmp "tdrive.sha256"
    Invoke-WebRequest -Uri $binUrl -OutFile $tmpExe -UseBasicParsing
    Invoke-WebRequest -Uri $shaUrl -OutFile $tmpSha -UseBasicParsing

    $expected = ((Get-Content $tmpSha -TotalCount 1).Trim().Split(' ')[0]).ToLower()
    $actual   = (Get-FileHash $tmpExe -Algorithm SHA256).Hash.ToLower()
    if ($expected -ne $actual) { throw "SHA256 校验失败: expected=$expected actual=$actual" }

    Move-Item -Force $tmpExe $ExePath
  } finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  }
}

# 注册 WorkBuddy 会话钩子（写 ~/.workbuddy/settings.json：只增不毁、幂等、改动前自动备份）。
# 失败不应让整个安装失败（二进制已就绪，网盘命令可用），仅提示。
try {
  & $ExePath hook register --host workbuddy *> $null
  if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
} catch {
  Write-Warning "未能写入 WorkBuddy 会话钩子（会话自动备份不可用，其余功能不受影响）。可稍后手动执行：`"$ExePath`" hook register --host workbuddy"
}

& $ExePath --version
exit 0
