# `hithink-finance special auction-opportunities`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema special.auction-opportunities --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。

## 命令

```bash
hithink-finance schema special.auction-opportunities --format json
hithink-finance special auction-opportunities --format json
hithink-finance special auction-opportunities --codes-file codes.txt --output result.json --format json
```

## 参数选择策略

| 参数                     | 必填 | 说明                                                                        |
| ------------------------ | ---- | --------------------------------------------------------------------------- |
| `--date <value>`         | 否   | optional date YYYY-MM-DD                                                    |
| `--warn-types <value>`   | 否   | comma-separated opportunity types 68710 through 68727；上游参数: warn_types |
| `--market <value>`       | 否   | market；可选: a_share, sh_sz_main, sh_a, sz_a, gem, star；默认: a_share     |
| `--exclude-st <value>`   | 否   | exclude-st；默认: false；上游参数: exclude_st                               |
| `--thscodes <value>`     | 否   | thscodes                                                                    |
| `--sort-by <value>`      | 否   | sort-by；可选: warn_time, warn_type；默认: warn_time；上游参数: sort_by     |
| `--sort-order <value>`   | 否   | sort-order；可选: asc, desc；默认: desc；上游参数: sort_order               |
| `--page <value>`         | 否   | page number starting at 1；默认: 1                                          |
| `--size <value>`         | 否   | page rows (1-20)；默认: 20                                                  |
| `--output <path>`        | 否   | write the response or data rows to a file                                   |
| `--file-format <format>` | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 使用 `--page` + `--size` 请求指定页，以 pagination.has_next 判断结束；保留记录顺序和空值。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 支持 `--codes-file` 或 `--codes-stdin` 读取多 thscode；不要同时用 `--api-key-stdin` 和 `--codes-stdin`。
