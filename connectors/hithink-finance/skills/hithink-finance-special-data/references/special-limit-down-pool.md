# `hithink-finance special limit-down-pool`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema special.limit-down-pool --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。

## 命令

```bash
hithink-finance schema special.limit-down-pool --format json
hithink-finance special limit-down-pool --format json
```

## 参数选择策略

| 参数                       | 必填 | 说明                                                                                                                                                     |
| -------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--date-ms <milliseconds>` | 否   | trade date at Asia/Shanghai midnight；上游参数: date_ms                                                                                                  |
| `--page <number>`          | 否   | page number；默认: 1                                                                                                                                     |
| `--size <number>`          | 否   | page size (1-200)；默认: 50                                                                                                                              |
| `--sort-field <field>`     | 否   | sort field；可选: last_limit_time, first_limit_time, last_price, price_change_ratio_pct, turnover_ratio_pct；默认: last_limit_time；上游参数: sort_field |
| `--sort-dir <direction>`   | 否   | sort direction；可选: asc, desc；默认: desc；上游参数: sort_dir                                                                                          |
| `--output <path>`          | 否   | write the response or data rows to a file                                                                                                                |
| `--file-format <format>`   | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json                                                                              |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 使用 `--page` + `--size` 翻页；全量抓取时逐页推进。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
