@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM NeoData 金融数据查询 - Windows CMD 封装
REM
REM Usage:
REM   query.cmd "腾讯最新财报"
REM
REM 环境变量:
REM   NEODATA_SUB_CHANNEL - 子渠道名称 (默认: qclaw)
REM   NEODATA_DATA_TYPE   - 数据类型 all/api/doc (默认: all)
REM   AUTH_GATEWAY_PORT   - 本地代理端口 (默认: 19000)

if "%~1"=="" (
    echo 用法: query.cmd ^<query^>
    exit /b 1
)

set "QUERY=%~1"

if not defined AUTH_GATEWAY_PORT set "AUTH_GATEWAY_PORT=19000"
if not defined NEODATA_SUB_CHANNEL set "NEODATA_SUB_CHANNEL=qclaw"
if not defined NEODATA_DATA_TYPE set "NEODATA_DATA_TYPE=all"

set "BASE_URL=http://localhost:%AUTH_GATEWAY_PORT%/proxy/api"
set "REMOTE_URL=https://jprx.m.qq.com/aizone/skillserver/v1/proxy/teamrouter_neodata/query"

REM 生成 request_id
for /f %%i in ('python -c "import uuid; print(uuid.uuid4().hex)" 2^>nul') do set "REQUEST_ID=%%i"
if not defined REQUEST_ID set "REQUEST_ID=req-%RANDOM%-%RANDOM%"

REM 构造 JSON payload 写入临时文件（避免 CMD 转义问题）
set "TMPJSON=%TEMP%\neodata_query_%RANDOM%.json"
set "TMPOUT=%TEMP%\neodata_resp_%RANDOM%.txt"

(
echo {
echo     "channel": "neodata",
echo     "sub_channel": "%NEODATA_SUB_CHANNEL%",
echo     "query": "%QUERY%",
echo     "request_id": "%REQUEST_ID%",
echo     "data_type": "%NEODATA_DATA_TYPE%",
echo     "se_params": {},
echo     "extra_params": {}
echo }
) > "%TMPJSON%"

REM 发送请求，将响应体写文件，HTTP 状态码输出到 stdout
for /f %%c in ('curl --silent --show-error --location --max-time 30 --connect-timeout 10 ^
    "%BASE_URL%" ^
    --header "Content-Type: application/json" ^
    --header "Remote-URL: %REMOTE_URL%" ^
    --data @"%TMPJSON%" ^
    --output "%TMPOUT%" ^
    --write-out "%%{http_code}"') do set "HTTP_CODE=%%c"

if not "%HTTP_CODE%"=="200" (
    echo 请求失败: HTTP %HTTP_CODE% >&2
    if exist "%TMPOUT%" type "%TMPOUT%" >&2
    del /q "%TMPJSON%" "%TMPOUT%" 2>nul
    exit /b 1
)

REM 格式化输出 JSON
python -m json.tool "%TMPOUT%" 2>nul || type "%TMPOUT%"

del /q "%TMPJSON%" "%TMPOUT%" 2>nul
endlocal
