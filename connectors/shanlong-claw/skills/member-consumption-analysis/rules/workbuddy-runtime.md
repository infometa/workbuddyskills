# WorkBuddy 二进制执行规则

本技能只执行正文登记的固定只读查询。所有查询直接启动连接器安装并认证的 `sl-sea` 二进制，无需额外 Node.js 或 Python 环境，不需要拼装 JavaScript 查询脚本。

## 定位规则

依次检查 `SL_BIN`、`SL_CLI_BIN` 指定的绝对二进制路径，`SL_CLI_HOME/bin`，以及当前操作系统用户主目录下的 `.slclaw/bin`。Windows 文件名为 `sl-sea.exe`，macOS/Linux 为 `sl-sea`。无效候选继续回退；不要使用开发者用户名、当前目录、Skill 目录或 PATH 中的裸命令。

`<sl-sea-absolute>` 是正文命令模板的占位符，执行前替换为上述解析结果；不是命令名称。禁止调用旧 `sl`、`sl.cmd`、`sl.ps1` 或开发版 CLI 入口。找不到二进制时停止并提示检查连接器安装，不改用其它入口。

## Windows：PowerShell

先在当前 PowerShell 会话定位二进制：

```powershell
$seaCandidates = @($env:SL_BIN, $env:SL_CLI_BIN)
if ($env:SL_CLI_HOME) { $seaCandidates += Join-Path $env:SL_CLI_HOME 'bin\sl-sea.exe' }
$seaCandidates += Join-Path ([Environment]::GetFolderPath('UserProfile')) '.slclaw\bin\sl-sea.exe'
$resolved = $seaCandidates | Where-Object {
    $_ -and ($_ -match '^(?:[A-Za-z]:[\\/]|\\\\)') -and (Test-Path -LiteralPath $_ -PathType Leaf)
} | Select-Object -First 1
if (-not $resolved) { throw 'sl-executable-not-found：请检查商龙连接器安装' }
```

按正文查询构造参数数组；JSON 先按业务规则确定时间与筛选值，完整放在一个参数中。下例中的域、动作、JSON 必须替换，不新增正文未登记的命令：

```powershell
$paramsJson = '<按正文填写的完整 JSON>'
$cliArgs = @('<domain>', '<action>', '--params', $paramsJson, '--format', 'json')
```

无需 JSON 的查询省略 `--params` 及其值。门店查询使用 `@('store', 'find', '--type', 'crm', '--name', $shopName, '--format', 'json')`；关键词查询将 `--name` 改为 `--keyword`。单引号字符串内的单引号写成两个单引号；不得用字符串拼接执行用户输入。

PowerShell 7.3 及以上使用原生参数数组，保留 JSON 双引号和空格：

```powershell
$PSNativeCommandArgumentPassing = 'Standard'
& $resolved @cliArgs
if ($LASTEXITCODE -ne 0) { throw 'process-exit-nonzero：本次查询失败' }
```

Windows PowerShell 5.1 / PowerShell 7.0–7.2 对原生程序的 JSON 引号传递方式不同。使用下面的系统进程接口直接启动同一二进制，按 Windows 参数规则编码；不要直接照搬 Bash 单引号命令，也不要要求客户安装 Node.js。只在旧版 PowerShell 使用此段：

```powershell
$seaStart = New-Object System.Diagnostics.ProcessStartInfo
$seaStart.FileName = $resolved
$seaStart.UseShellExecute = $false
$seaStart.CreateNoWindow = $true
$seaStart.RedirectStandardOutput = $true
$seaStart.RedirectStandardError = $true
$seaStart.StandardOutputEncoding = [Text.Encoding]::UTF8
$seaStart.StandardErrorEncoding = [Text.Encoding]::UTF8
$seaStart.Arguments = (($cliArgs | ForEach-Object {
    $seaArg = [string]$_
    $seaArg = [regex]::Replace($seaArg, '(\\*)"', '$1$1\"')
    $seaArg = [regex]::Replace($seaArg, '(\\+)$', '$1$1')
    '"' + $seaArg + '"'
}) -join ' ')
$seaProcess = New-Object System.Diagnostics.Process
$seaProcess.StartInfo = $seaStart
try {
    if (-not $seaProcess.Start()) { throw 'process-start-failed' }
    $seaOutTask = $seaProcess.StandardOutput.ReadToEndAsync()
    $seaErrTask = $seaProcess.StandardError.ReadToEndAsync()
    if (-not $seaProcess.WaitForExit(120000)) {
        $seaProcess.Kill()
        throw 'process-timeout：本次查询超时'
    }
    $seaStdout = $seaOutTask.GetAwaiter().GetResult()
    $seaStderr = $seaErrTask.GetAwaiter().GetResult()
    if ($seaProcess.ExitCode -ne 0) { throw 'process-exit-nonzero：本次查询失败' }
    Write-Output $seaStdout
} finally {
    $seaProcess.Dispose()
}
```

## macOS / Linux：Bash

使用系统 Bash，定位后用双引号保护二进制路径，以数组传递参数；不要使用 `eval`。

```bash
resolved=''
for candidate in "${SL_BIN:-}" "${SL_CLI_BIN:-}" "${SL_CLI_HOME:+$SL_CLI_HOME/bin/sl-sea}" "$HOME/.slclaw/bin/sl-sea"; do
  case "$candidate" in
    /*) if [ -f "$candidate" ] && [ -x "$candidate" ]; then resolved="$candidate"; break; fi ;;
  esac
done
if [ -z "$resolved" ]; then
  printf '%s\n' 'sl-executable-not-found：请检查商龙连接器安装' >&2
  exit 1
fi
```

对应正文命令的直接调用形式如下，执行前替换域、动作与 JSON：

```bash
params_json='<按正文填写的完整 JSON>'
cli_args=('<domain>' '<action>' '--params' "$params_json" '--format' 'json')
"$resolved" "${cli_args[@]}"
sea_status=$?
if [ "$sea_status" -ne 0 ]; then
  printf '%s\n' 'process-exit-nonzero：本次查询失败' >&2
  exit "$sea_status"
fi
```

门店查询使用 `cli_args=('store' 'find' '--type' 'crm' '--name' "$shop_name" '--format' 'json')`。无需 JSON 的查询省略 `--params` 及其值。用户文本含单引号时，先正确构造变量，不能直接插入单引号模板；Bash 单引号字面量中的单引号使用 `'\''` 转义序列。JSON 内部引号与反斜杠按 JSON 规则编码，不能省略双引号。执行工具支持超时设置时使用 120 秒，超时按失败处理。

## 结果与认证

- 只有进程成功、退出码为 0、结果可解析且 HTTP/业务状态成功，数据才可进入分析。若 CLI 输出 JSON 文件路径，读取该结果文件；不能假定 stdout 一定是纯 JSON。
- 程序缺失、权限不足、超时、非零退出、无法解析或业务错误均是查询失败，不能解释为无数据或零值。部分模块失败时只分析成功模块，并说明缺失。
- 默认连接器已认证，不额外查询状态。认证或门店清单缺失时引导在连接器重新认证，再重试原查询一次；不读取认证文件、不自行构造请求头。
- 客户是否支持 CRM8 按主文件判断；空结果不能用于推断客户版本。

## 执行边界与隐私

只执行当前 Skill 正文登记的域、动作和参数；不得搜索其它命令、执行 help 或自行变更接口。禁止 `--verbose`/`-v`、`--header`、`--envPath`、`--body-file`、`token show`、动态 DataCube、可变任务 ID、`title/where`、直连 MCP/数据库。

不输出 token/session/cookie/密钥/认证参数或原始错误堆栈。明细按主文件脱敏；不主动执行触达、发券、导出敏感明细或其它写操作。
