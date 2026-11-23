# `hithink-finance special dragon-tiger-department-history`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema special.dragon-tiger-department-history --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。

## 命令

```bash
hithink-finance schema special.dragon-tiger-department-history --format json
hithink-finance special dragon-tiger-department-history --department-id <value> --format json
```

## 参数选择策略

| 参数                           | 必填 | 说明                                                                                                  |
| ------------------------------ | ---- | ----------------------------------------------------------------------------------------------------- |
| `--department-id <value>`      | 是   | department record identifier (1-128 characters)；上游参数: department_id                              |
| `--page <value>`               | 否   | page number starting at 1；默认: 1                                                                    |
| `--size <value>`               | 否   | page rows (1-30)；默认: 30                                                                            |
| `--min-net-buy-amount <value>` | 否   | minimum net buy bucket in CNY: 5000000, 30000000, 50000000 or 100000000；上游参数: min_net_buy_amount |
| `--sort-field <value>`         | 否   | sort-field；可选: trade_date, change_ratio, net_buy_amount；默认: trade_date；上游参数: sort_field    |
| `--sort-dir <value>`           | 否   | sort-dir；可选: asc, desc；默认: desc；上游参数: sort_dir                                             |
| `--output <path>`              | 否   | write the response or data rows to a file                                                             |
| `--file-format <format>`       | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json                           |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 使用 `--page` + `--size` 请求指定页，以 pagination.has_next 判断结束；保留记录顺序和空值。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
