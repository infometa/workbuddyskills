# =============================================================================
# ensure-node.ps1 — hook 转接脚本（Windows）
# =============================================================================
# 用法：ensure-node.ps1 [-EventType <event-type>]
#   -EventType：传给 hook-handler.js 的事件名，如 session-start / pre-tool 等
#               默认 session-start
#
# 目的：
#   查找可用的 Node.js（>= v18），找到后用它执行 hook-handler.js <event-type>。
#
# 查找顺序：
#   1) 系统 PATH 上 node >= v18                                          → 使用该 node
#   2) %USERPROFILE%\.workbuddy\binaries\node\ 递归查找                  → 使用该 node
#   3) %USERPROFILE%\.page-deliver\bin\node-win-x64\node.exe             → 使用该 node
#
# 退出码：始终 0，不阻塞主流程。
# =============================================================================

param(
    [string]$EventType = 'session-start'
)

$ErrorActionPreference = 'SilentlyContinue'

$MIN_MAJOR = 18

$PLUGIN_ROOT = if ($env:CODEBUDDY_PLUGIN_ROOT) { $env:CODEBUDDY_PLUGIN_ROOT } else {
    Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)))
}
# 按事件类型分发不同 handler
$handlerMap = @{
    'pre-tool'       = 'hooks\hr-ai-data\script\pre_tool_handler.js'
    'user-prompt'    = 'hooks\hr-ai-data\script\user_prompt_handler.js'
    'session-start'  = 'hooks\hr-ai-data\script\session_start_handler.js'
    'session-end'    = 'hooks\hr-ai-data\script\session_end_handler.js'
}
$handlerFile = if ($handlerMap.ContainsKey($EventType)) { $handlerMap[$EventType] } else { 'hooks\hr-ai-data\script\pre_tool_handler.js' }
$HANDLER_JS = Join-Path $PLUGIN_ROOT $handlerFile

# ---- 读取 stdin，保存供后续转发 -------------------------------------------

# 使用 System.Text.Encoding.UTF8 读取 stdin，避免 PowerShell 默认 UTF-16 导致的
# 中文乱码/截断（直接影响后续 JSON.parse 的成功率）。
try {
    $stdinStream = [Console]::OpenStandardInput()
    $reader = [System.IO.StreamReader]::new($stdinStream, [System.Text.Encoding]::UTF8)
    $raw = $reader.ReadToEnd()
    $reader.Close()
} catch {
    exit 0
}

# ---- 辅助函数 ---------------------------------------------------------------

function Get-NodeMajor($bin) {
    try {
        $ver = & $bin --version 2>$null
        if ($ver -match '^v?(\d+)') { return [int]$Matches[1] }
    } catch {}
    return 0
}

function Test-NodeBin($bin) {
    if (-not (Test-Path $bin)) { return $false }
    $maj = Get-NodeMajor $bin
    return $maj -ge $MIN_MAJOR
}

# 找到可用 node 后，用它执行 hook-handler.js，将原始 stdin 透传进去
function Invoke-Handler($nodeBin) {
    if (Test-Path $HANDLER_JS) {
        try {
            $proc = New-Object System.Diagnostics.Process
            $proc.StartInfo.FileName = $nodeBin
            $proc.StartInfo.Arguments = "`"$HANDLER_JS`" $EventType"
            $proc.StartInfo.UseShellExecute = $false
            # 抑制子进程控制台窗口：UseShellExecute=false 且未重定向 stdout/stderr 时，
            # 若父 PowerShell 控制台不可见，node.exe 会自建新控制台 → 黑框。CreateNoWindow 阻止该行为。
            $proc.StartInfo.CreateNoWindow = $true
            $proc.StartInfo.RedirectStandardInput = $true
            $proc.StartInfo.RedirectStandardOutput = $false
            $proc.StartInfo.RedirectStandardError = $false
            $proc.Start() | Out-Null
            # 使用 BaseStream + UTF-8 StreamWriter 写入 stdin，避免默认编码（如 GBK）
            # 导致中文损坏（兼容 PowerShell 5.1 / 7+）。
            $utf8Writer = New-Object System.IO.StreamWriter($proc.StandardInput.BaseStream, [System.Text.Encoding]::UTF8)
            $utf8Writer.Write($raw)
            $utf8Writer.Close()
            $proc.WaitForExit()
        } catch {}
    }
    exit 0
}

# ---- Step 1: 系统 PATH 中的 node -------------------------------------------

$sysNode = Get-Command 'node' -ErrorAction SilentlyContinue
if ($sysNode) {
    if (Test-NodeBin $sysNode.Source) {
        $ver = & $sysNode.Source --version 2>$null
        Write-Host "[ensure-node] system node found: $($sysNode.Source) ($ver)" -ForegroundColor Gray
        Invoke-Handler $sysNode.Source
    }
}

# ---- Step 2: workbuddy 管理的 node -----------------------------------------

$wbRoot = Join-Path $env:USERPROFILE '.workbuddy\binaries\node'
if (Test-Path $wbRoot) {
    $wbNodes = Get-ChildItem -Path $wbRoot -Recurse -Filter 'node.exe' -ErrorAction SilentlyContinue |
               Select-Object -First 20
    foreach ($f in $wbNodes) {
        if (Test-NodeBin $f.FullName) {
            $ver = & $f.FullName --version 2>$null
            Write-Host "[ensure-node] workbuddy node found: $($f.FullName) ($ver)" -ForegroundColor Gray
            Invoke-Handler $f.FullName
        }
    }
}

# ---- Step 3: preflight 安装的 page-deliver 缓存 node -----------------------

$pdNode = Join-Path $env:USERPROFILE '.page-deliver\bin\node-win-x64\node.exe'
if (Test-NodeBin $pdNode) {
    $ver = & $pdNode --version 2>$null
    Write-Host "[ensure-node] page-deliver cached node found: $pdNode ($ver)" -ForegroundColor Gray
    Invoke-Handler $pdNode
}

Write-Host "[ensure-node] no usable Node found, skipping handler" -ForegroundColor Gray
exit 0
