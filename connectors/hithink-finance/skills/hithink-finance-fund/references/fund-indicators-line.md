# `hithink-finance fund indicators-line`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema fund.indicators-line --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。
- 每组 indexes 包含 thscodes 和 index_info；每个 index_info 元素包含 index_id。time_range 必须包含 time_type，绝对时间使用 Unix 毫秒。

## 命令

```bash
hithink-finance schema fund.indicators-line --format json
hithink-finance fund indicators-line --indexes '[{"thscodes":["000001.OF"],"index_info":[{"index_id":"rsi_pct"}]}]' --time-range '{"time_type":"DAY_1","start":1788192000000,"end":1788796800000}' --format json
```

JSON 参数作为单个字符串传给 CLI，CLI 负责 URL 编码。示例适用于 POSIX shell 和 PowerShell 7.3+ 的标准原生参数传递；其他执行器用参数数组或其原生引用方式。

## 参数选择策略

| 参数                     | 必填 | 说明                                                                                                          |
| ------------------------ | ---- | ------------------------------------------------------------------------------------------------------------- |
| `--indexes <json>`       | 是   | JSON array of groups: thscodes[], index_info[] with required index_id and optional attribute                  |
| `--time-range <json>`    | 是   | JSON object: required time_type; optional Unix-millisecond start/end and integer offset；上游参数: time_range |
| `--output <path>`        | 否   | write the response or data rows to a file                                                                     |
| `--file-format <format>` | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json                                   |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 无分页参数；仍检查返回中的 count/数组长度。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。
- 缺少嵌套字段时按错误中的 JSON 路径修正。指标 ID 与时间类型沿用已知契约或实际返回，不猜枚举。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
