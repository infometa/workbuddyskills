# `hithink-finance fund quota-list`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema fund.quota-list --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。
- tab 为类别字符串数组；示例类别来自现有契约，其他类别须有已知取值依据。

## 命令

```bash
hithink-finance schema fund.quota-list --format json
hithink-finance fund quota-list --tab '["nazhi100"]' --buy true --output fund-quota.json --format json
```

JSON 参数作为单个字符串传给 CLI，CLI 负责 URL 编码。示例适用于 POSIX shell 和 PowerShell 7.3+ 的标准原生参数传递；其他执行器用参数数组或其原生引用方式。

## 参数选择策略

| 参数                     | 必填 | 说明                                                                        |
| ------------------------ | ---- | --------------------------------------------------------------------------- |
| `--tab <json>`           | 是   | category name JSON array                                                    |
| `--buy <boolean>`        | 否   | optional true/false purchasable filter                                      |
| `--output <path>`        | 否   | write the response or data rows to a file                                   |
| `--file-format <format>` | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 无分页参数；仍检查返回中的 count/数组长度。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
