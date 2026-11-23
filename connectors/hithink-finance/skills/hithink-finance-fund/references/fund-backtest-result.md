# `hithink-finance fund backtest-result`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema fund.backtest-result --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。
- 先运行 fund backtest-indicators，按 indicator_code、support_operation、value_kind、unit 与 state_rules 核对用户指定的回测条件。示例仅用于说明参数结构，实际规则由用户给定。

## 命令

```bash
hithink-finance schema fund.backtest-result --format json
hithink-finance fund backtest-result --thscode 000001.OF --buy-conditions '{"indicator_code":"rsi_pct","operator":">","value":0.5}' --sell-conditions '{"indicator_code":"rsi_pct","operator":"<","value":0.3}' --buy-frequency-type WEEKLY --max-buy-times 5 --per-buy-amount 100 --output fund-backtest.json --format json
```

JSON 参数作为单个字符串传给 CLI，CLI 负责 URL 编码。示例适用于 POSIX shell 和 PowerShell 7.3+ 的标准原生参数传递；其他执行器用参数数组或其原生引用方式。

## 参数选择策略

| 参数                          | 必填 | 说明                                                                        |
| ----------------------------- | ---- | --------------------------------------------------------------------------- |
| `--thscode <code>`            | 是   | single fund thscode                                                         |
| `--buy-conditions <json>`     | 是   | buy condition JSON object or array；上游参数: buy_conditions                |
| `--sell-conditions <json>`    | 是   | sell condition JSON object or array；上游参数: sell_conditions              |
| `--buy-frequency-type <type>` | 是   | upstream buy frequency type；上游参数: buy_frequency_type                   |
| `--max-buy-times <number>`    | 是   | maximum buy count；上游参数: max_buy_times                                  |
| `--per-buy-amount <number>`   | 是   | amount for each buy；上游参数: per_buy_amount                               |
| `--output <path>`             | 否   | write the response or data rows to a file                                   |
| `--file-format <format>`      | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 无分页参数；仍检查返回中的 count/数组长度。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
