# JSON 输出契约

## 什么时候读取

需要判断命令成功或失败、编写脚本封装、处理 stdout/stderr，或连续执行多个 Agent operation 时读取本文件。

## 成功 envelope

成功写入 stdout，退出码为 0：

```json
{
  "schemaVersion": 1,
  "ok": true,
  "operation": "invoice.list",
  "data": {},
  "meta": { "status": "COMPLETE" },
  "warnings": []
}
```

判断成功使用退出码 0 和 `ok === true`。不要用 `code === 0`，成功 envelope 没有顶层 `code/msg`。

## 失败 envelope

失败写入 stderr，退出码非 0：

```json
{
  "schemaVersion": 1,
  "ok": false,
  "error": {
    "type": "validation",
    "subtype": "input_invalid",
    "message": "必须提供 fid 或 number",
    "retryable": false
  }
}
```

错误判断优先看：

- `error.type`
- `error.subtype`
- `error.message`
- `error.retryable`
- `error.stage`
- 进程退出码

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `2` | 参数或业务输入错误 |
| `3` | 认证错误 |
| `4` | 网络错误 |
| `10` | 需要明确确认 |
| `11` | 部分完成或结果不确定 |

`retryable=true` 只表示读操作或准备阶段可能可以重试；写入请求已经发出后，遇到 `partial/write_uncertain` 必须停止并交给用户判断。

## JSON 输入兼容

简单 JSON 优先使用 `--input-json`，两端都可用，能避开 Windows PowerShell 对 `printf`、管道、转义和续行的差异：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0}'
```

复杂或多行 JSON 使用临时 UTF-8 文件。Windows PowerShell 示例：

```powershell
$inputFile = Join-Path $env:TEMP "weaver-work-cli-input.json"
@{ page_size = 10; start_pos = 0 } | ConvertTo-Json -Depth 20 -Compress | Set-Content -Encoding UTF8 -NoNewline $inputFile
weaver-work-cli --profile eteams --json invoice run invoice.list --input $inputFile
```

macOS/Linux（bash/zsh）示例：

```bash
input_file="$(mktemp)"
printf '%s\n' '{"page_size":10,"start_pos":0}' > "$input_file"
weaver-work-cli --profile eteams --json invoice run invoice.list --input "$input_file"
```

Windows/PowerShell 下不要使用 `printf`、bash 反斜杠续行、`$HOME/...` 或 `~/...` 路径、`rm/ls/diff/python3` 等 Unix-only 写法；目录查看用 `Get-ChildItem`，删除用 `Remove-Item`，文件比对用 `Get-FileHash`，Python 启动器优先用 `py -3`。

## 大结果渲染与提效规则

当前 `weaver-work-cli` 输出层是轻量封装：JSON 模式把完整结果写 stdout，文本模式写人类可读文本；不像飞书 CLI 已内置 `--format table/pretty/ndjson`、`--jq` 或通用 `--page-all`。Agent 因此必须在调用和回复阶段主动控量，避免把超长接口响应原样渲染给用户。

### 调用前控量

- 列表类 operation 默认先取小页：优先 `page_size=10`，需要更多结果时再按用户目标递增，通常不要超过 `20`。
- 用户只想定位一个对象时，用筛选字段缩小范围；已有 `fid`、`number`、文件路径或 continuation 时直达对应 operation，不要先拉全量列表。
- 用户说“全部 / 全量 / 统计”时，先说明会分页读取；每页读取后只保留任务所需字段和去重键，避免在上下文里累计完整原始响应。
- 有 `hasMore`、`start_pos`、`page_token`、`next_page_token` 等分页字段时，用它们继续翻页；没有明确分页信号时不要无界循环。

### 回复时渲染

- 不要把完整 stdout JSON 直接粘给用户。优先输出结论、命中数量、关键字段、下一页/剩余数据提示和必要的文件路径。
- 列表结果只展示最相关的前 `10` 条；如果用户要求更多，分批展示并说明还可以继续读取。
- 详情结果只展示与用户问题相关的字段。发票类详情通常优先展示 `fid`、号码/代码、购销方、金额、日期、查验/报销状态和附件摘要。
- 超长文本、大数组、OCR 原文、逐项明细或调试需要的完整 JSON，优先写入本地文件再给路径；不要在对话里展开。可用 shell 重定向保存完整 stdout，或业务 operation 暴露 `output` 参数时使用其文件输出。
- 如果为了调试必须引用原始 envelope，只截取必要字段：`ok`、`operation`、`meta`、`warnings`、`error` 或 `data` 的相关子树。

### 参考飞书 CLI 的实践

- 飞书 CLI 用 `--format json` 保留机器可读 envelope，用 `pretty/table/ndjson/csv` 降低人读成本；本 CLI 目前主要依赖 `--json` envelope，因此 Agent 回复时承担 pretty/table 摘要职责。
- 飞书 CLI 的分页实践是显式页预算（如 `--page-limit`）和页间延迟；本 CLI 业务 operation 应使用自身 schema 中的 `page_size/start_pos` 等字段模拟同样的预算控制。
- 飞书 CLI 对大产物倾向返回 artifact 文件路径；本 CLI 遇到下载、导出、OCR 或超长 JSON 时也应优先落盘并只向用户展示路径和摘要。
