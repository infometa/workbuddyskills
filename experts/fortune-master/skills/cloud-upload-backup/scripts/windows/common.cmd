@echo off
REM common.cmd — cloud-upload-backup skill common functions (Windows CMD)
REM Provides unified port detection, dependency checks, and base variables
REM Token is auto-injected by the local proxy service

REM Switch to UTF-8 code page to avoid garbled Chinese characters in GBK console
chcp 65001 >nul 2>nul

setlocal enabledelayedexpansion

REM --------------------------------------------------------
REM Detect Node.js availability
REM --------------------------------------------------------
REM Priority:
REM   1. Read QClaw embedded Node.js path from ~/.qclaw/qclaw.json (cli.nodeBinary)
REM   2. Fall back to system PATH node
REM   3. Exit with standard JSON error if none available

set "NODE_EXEC="
set "META_FILE=%USERPROFILE%\.qclaw\qclaw.json"

REM Try to read embedded Node.js path from QClaw meta file
if exist "%META_FILE%" (
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Get-Content '%META_FILE%' -Raw | ConvertFrom-Json).cli.nodeBinary" 2^>nul`) do set "NODE_EXEC=%%i"
)

REM Verify the path from meta actually exists
if defined NODE_EXEC (
    if not exist "!NODE_EXEC!" (
        echo [QClaw] Warning: nodeBinary from qclaw.json not found: !NODE_EXEC!, falling back to system node >&2
        set "NODE_EXEC="
    )
)

REM Verify the executable is actually Node.js (not QClaw.exe or other binary)
if defined NODE_EXEC (
    "!NODE_EXEC!" -e "process.exit(0)" >nul 2>nul
    if errorlevel 1 (
        echo [QClaw] Warning: nodeBinary from qclaw.json is not a valid Node.js executable: !NODE_EXEC!, falling back to system node >&2
        set "NODE_EXEC="
    )
)

REM Fall back to system PATH node
if not defined NODE_EXEC (
    for /f "delims=" %%N in ('where node 2^>nul') do (
        if not defined NODE_EXEC set "NODE_EXEC=%%N"
    )
)

REM Final validation
if not defined NODE_EXEC (
    echo {"success": false, "message": "Environment dependency missing: Node.js not found.\n\nQClaw embedded Node.js path is unavailable, and Node.js is not installed in system PATH.\nPlease try:\n1. Restart QClaw desktop application\n2. Or install Node.js (https://nodejs.org)", "error": "node unavailable: not found in qclaw.json or system PATH"}
    exit /b 1
)

echo [QClaw] Using Node.js: %NODE_EXEC% >&2

REM --------------------------------------------------------
REM Parse local proxy port (from environment variable)
REM --------------------------------------------------------

REM Get local proxy port from AUTH_GATEWAY_PORT environment variable
REM This variable is set by Electron main process when starting Auth Gateway, inherited by child processes
REM Falls back to default port 19000 if not set

if defined AUTH_GATEWAY_PORT (
    set "PROXY_PORT=%AUTH_GATEWAY_PORT%"
) else (
    set "PROXY_PORT=19000"
    echo [QClaw] AUTH_GATEWAY_PORT not set, falling back to default port: 19000 >&2
)

echo [QClaw] AUTH_GATEWAY_PORT: %PROXY_PORT% >&2

set "PROXY_BASE_URL=http://localhost:%PROXY_PORT%"
set "UPLOAD_API_BASE=%PROXY_BASE_URL%/proxy/qclaw-cos"

REM --------------------------------------------------------
REM Parent Process ID
REM --------------------------------------------------------
REM Use PowerShell (built-in on Windows) instead of python to get PPID

set "PPID_VAL=unknown"
for /f "delims=" %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"ProcessId=$PID\").ParentProcessId" 2^>nul') do set "PPID_VAL=%%P"
if "%PPID_VAL%"=="" set "PPID_VAL=unknown"
echo [QClaw] Parent PID: %PPID_VAL% >&2

REM --------------------------------------------------------
REM 检测 curl 可用性
REM --------------------------------------------------------
REM 优先级:
REM   1. 系统 PATH 中的 curl
REM   2. Windows 自带路径 %SystemRoot%\System32\curl.exe
REM   3. 都不可用则输出标准 JSON 错误并退出

set "CURL_EXEC="

REM 尝试从 PATH 查找 curl
for /f "delims=" %%C in ('where curl 2^>nul') do (
    if not defined CURL_EXEC set "CURL_EXEC=%%C"
)

REM 回退到 Windows 自带路径
if not defined CURL_EXEC (
    if exist "%SystemRoot%\System32\curl.exe" (
        set "CURL_EXEC=%SystemRoot%\System32\curl.exe"
        echo [QClaw] curl not in PATH, using system fallback: %SystemRoot%\System32\curl.exe >&2
    )
)

REM 最终校验
if not defined CURL_EXEC (
    echo {"success": false, "message": "❌ 环境依赖缺失：未找到 curl。\n\n系统 PATH 和 Windows 默认路径中均未找到 curl.exe。\n请尝试：\n1. 确认 Windows 10 1803+ 或 Windows 11\n2. 或手动安装 curl (https://curl.se/download.html)\n3. 检查系统 PATH 是否包含 %SystemRoot%\\System32", "error": "curl 不可用: 未在系统 PATH 和 Windows 默认路径中找到 curl.exe"}
    exit /b 1
)

echo [QClaw] Using curl: %CURL_EXEC% >&2

REM 返回到调用者（使用 endlocal 导出变量）
endlocal & set "PROXY_PORT=%PROXY_PORT%" & set "PROXY_BASE_URL=%PROXY_BASE_URL%" & set "UPLOAD_API_BASE=%UPLOAD_API_BASE%" & set "PPID_VAL=%PPID_VAL%" & set "NODE_EXEC=%NODE_EXEC%" & set "CURL_EXEC=%CURL_EXEC%"
exit /b 0
