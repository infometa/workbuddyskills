@echo off
REM cloud_backup.cmd — 云文件上传备份 skill 统一入口 (Windows CMD版)
REM
REM 命令:
REM   upload       上传单个文件
REM   batch-upload 批量上传多个文件
REM   info         查询云端文件信息
REM   list         列出云端目录文件

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 初始化公共变量
call "%SCRIPT_DIR%\common.cmd"
if errorlevel 1 exit /b 1

REM 获取第一个参数作为命令
set "CMD=%~1"
if "%CMD%"=="" (
    call :print_help
    exit /b 0
)
shift

REM 路由命令
if /i "%CMD%"=="help" goto :do_help
if /i "%CMD%"=="-h" goto :do_help
if /i "%CMD%"=="--help" goto :do_help
if /i "%CMD%"=="upload" goto :do_upload
if /i "%CMD%"=="batch-upload" goto :do_batch_upload
if /i "%CMD%"=="info" goto :do_info
if /i "%CMD%"=="list" goto :do_list

echo {"success": false, "message": "未知命令: %CMD%，可用命令见 --help", "error": "未知命令: %CMD%"}
exit /b 1

REM --------------------------------------------------------
REM upload 命令
REM --------------------------------------------------------

:do_help
call :print_help
exit /b 0

:do_upload
set "LOCAL_PATH="
set "REMOTE_PATH="
set "CONFLICT_STRATEGY=ask"

:upload_parse
if "%~1"=="" goto :upload_exec
if /i "%~1"=="--local-path" (
    set "LOCAL_PATH=%~2"
    shift
    shift
    goto :upload_parse
)
if /i "%~1"=="--remote-path" (
    set "REMOTE_PATH=%~2"
    shift
    shift
    goto :upload_parse
)
if /i "%~1"=="--conflict-strategy" (
    set "CONFLICT_STRATEGY=%~2"
    shift
    shift
    goto :upload_parse
)
shift
goto :upload_parse

:upload_exec
if "%LOCAL_PATH%"=="" (
    echo {"success": false, "message": "缺少必填参数: local-path", "error": "缺少必填参数: local-path"}
    exit /b 1
)

echo [QClaw] Uploading: %LOCAL_PATH% >&2

REM 使用 node 构造 JSON 请求体
set "TMP_BODY=%TEMP%\cloud_backup_body_%RANDOM%.tmp"
set "TMP_RESP=%TEMP%\cloud_backup_resp_%RANDOM%.tmp"
set "TMP_STATUS=%TEMP%\cloud_backup_status_%RANDOM%.tmp"

if "%REMOTE_PATH%"=="" (
    "%NODE_EXEC%" -e "console.log(JSON.stringify({localPath:process.argv[1],conflictStrategy:process.argv[2]}))" "%LOCAL_PATH%" "%CONFLICT_STRATEGY%" > "%TMP_BODY%"
) else (
    "%NODE_EXEC%" -e "console.log(JSON.stringify({localPath:process.argv[1],remotePath:process.argv[2],conflictStrategy:process.argv[3]}))" "%LOCAL_PATH%" "%REMOTE_PATH%" "%CONFLICT_STRATEGY%" > "%TMP_BODY%"
)

"%CURL_EXEC%" -s -o "%TMP_RESP%" -w "%%{http_code}" -X POST "%UPLOAD_API_BASE%/upload" -H "Content-Type: application/json" -d @"%TMP_BODY%" > "%TMP_STATUS%" 2>nul

set /p HTTP_STATUS=<"%TMP_STATUS%"

REM 200 = 成功, 409 = 同名文件冲突（响应体包含冲突详情，需透传给 QClaw）
if "%HTTP_STATUS%"=="200" goto :upload_output
if "%HTTP_STATUS%"=="409" goto :upload_output

echo {"success": false, "message": "HTTP 请求失败，状态码: %HTTP_STATUS%", "error": "HTTP 请求失败，状态码: %HTTP_STATUS%"}
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 1

:upload_output
type "%TMP_RESP%"
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 0

REM --------------------------------------------------------
REM batch-upload 命令
REM --------------------------------------------------------

:do_batch_upload
set "FILES="

:batch_parse
if "%~1"=="" goto :batch_exec
if /i "%~1"=="--files" (
    set "FILES=%~2"
    shift
    shift
    goto :batch_parse
)
shift
goto :batch_parse

:batch_exec
if "%FILES%"=="" (
    echo {"success": false, "message": "缺少必填参数: files", "error": "缺少必填参数: files"}
    exit /b 1
)

echo [QClaw] Batch uploading... >&2

set "TMP_BODY=%TEMP%\cloud_backup_body_%RANDOM%.tmp"
set "TMP_RESP=%TEMP%\cloud_backup_resp_%RANDOM%.tmp"
set "TMP_STATUS=%TEMP%\cloud_backup_status_%RANDOM%.tmp"

"%NODE_EXEC%" -e "const files=JSON.parse(process.argv[1]);console.log(JSON.stringify({files}))" "%FILES%" > "%TMP_BODY%"

"%CURL_EXEC%" -s -o "%TMP_RESP%" -w "%%{http_code}" -X POST "%UPLOAD_API_BASE%/batch-upload" -H "Content-Type: application/json" -d @"%TMP_BODY%" > "%TMP_STATUS%" 2>nul

set /p HTTP_STATUS=<"%TMP_STATUS%"

REM 200 = 成功, 409 = 同名文件冲突（响应体包含冲突详情，需透传给 QClaw）
if "%HTTP_STATUS%"=="200" goto :batch_output
if "%HTTP_STATUS%"=="409" goto :batch_output

echo {"success": false, "message": "HTTP 请求失败，状态码: %HTTP_STATUS%", "error": "HTTP 请求失败，状态码: %HTTP_STATUS%"}
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 1

:batch_output
type "%TMP_RESP%"
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 0

REM --------------------------------------------------------
REM info 命令
REM --------------------------------------------------------

:do_info
set "REMOTE_PATH="

:info_parse
if "%~1"=="" goto :info_exec
if /i "%~1"=="--remote-path" (
    set "REMOTE_PATH=%~2"
    shift
    shift
    goto :info_parse
)
shift
goto :info_parse

:info_exec
if "%REMOTE_PATH%"=="" (
    echo {"success": false, "message": "缺少必填参数: remote-path", "error": "缺少必填参数: remote-path"}
    exit /b 1
)

set "TMP_BODY=%TEMP%\cloud_backup_body_%RANDOM%.tmp"
set "TMP_RESP=%TEMP%\cloud_backup_resp_%RANDOM%.tmp"
set "TMP_STATUS=%TEMP%\cloud_backup_status_%RANDOM%.tmp"

"%NODE_EXEC%" -e "console.log(JSON.stringify({remotePath:process.argv[1]}))" "%REMOTE_PATH%" > "%TMP_BODY%"

"%CURL_EXEC%" -s -o "%TMP_RESP%" -w "%%{http_code}" -X POST "%UPLOAD_API_BASE%/info" -H "Content-Type: application/json" -d @"%TMP_BODY%" > "%TMP_STATUS%" 2>nul

set /p HTTP_STATUS=<"%TMP_STATUS%"

if not "%HTTP_STATUS%"=="200" (
    echo {"success": false, "message": "HTTP 请求失败，状态码: %HTTP_STATUS%", "error": "HTTP 请求失败，状态码: %HTTP_STATUS%"}
    del "%TMP_BODY%" 2>nul
    del "%TMP_RESP%" 2>nul
    del "%TMP_STATUS%" 2>nul
    exit /b 1
)

type "%TMP_RESP%"
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 0

REM --------------------------------------------------------
REM list 命令
REM --------------------------------------------------------

:do_list
set "DIR_PATH=/"
set "LIMIT=50"

:list_parse
if "%~1"=="" goto :list_exec
if /i "%~1"=="--dir-path" (
    set "DIR_PATH=%~2"
    shift
    shift
    goto :list_parse
)
if /i "%~1"=="--limit" (
    set "LIMIT=%~2"
    shift
    shift
    goto :list_parse
)
shift
goto :list_parse

:list_exec
set "TMP_BODY=%TEMP%\cloud_backup_body_%RANDOM%.tmp"
set "TMP_RESP=%TEMP%\cloud_backup_resp_%RANDOM%.tmp"
set "TMP_STATUS=%TEMP%\cloud_backup_status_%RANDOM%.tmp"

"%NODE_EXEC%" -e "console.log(JSON.stringify({dirPath:process.argv[1],limit:parseInt(process.argv[2])}))" "%DIR_PATH%" "%LIMIT%" > "%TMP_BODY%"

"%CURL_EXEC%" -s -o "%TMP_RESP%" -w "%%{http_code}" -X POST "%UPLOAD_API_BASE%/list" -H "Content-Type: application/json" -d @"%TMP_BODY%" > "%TMP_STATUS%" 2>nul

set /p HTTP_STATUS=<"%TMP_STATUS%"

if not "%HTTP_STATUS%"=="200" (
    echo {"success": false, "message": "HTTP 请求失败，状态码: %HTTP_STATUS%", "error": "HTTP 请求失败，状态码: %HTTP_STATUS%"}
    del "%TMP_BODY%" 2>nul
    del "%TMP_RESP%" 2>nul
    del "%TMP_STATUS%" 2>nul
    exit /b 1
)

type "%TMP_RESP%"
del "%TMP_BODY%" 2>nul
del "%TMP_RESP%" 2>nul
del "%TMP_STATUS%" 2>nul
exit /b 0

REM --------------------------------------------------------
REM 帮助信息
REM --------------------------------------------------------

:print_help
echo cloud_backup.cmd — 云文件上传备份统一入口 (Windows)
echo.
echo 命令：
echo   upload --local-path ^<path^> [--remote-path ^<path^>] [--conflict-strategy ask^|rename^|overwrite]
echo       上传单个本地文件到云端
echo.
echo   batch-upload --files ^<json-array^>
echo       批量上传多个本地文件到云端
echo.
echo   info --remote-path ^<path^>
echo       查询云端文件信息
echo.
echo   list [--dir-path ^<path^>] [--limit ^<n^>]
echo       列出云端目录中的文件
echo.
echo   help
echo       显示此帮助信息
goto :eof
