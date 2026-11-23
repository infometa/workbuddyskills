# `hithink-finance ipo hk-applications`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema ipo.hk-applications --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。

## 命令

```bash
hithink-finance schema ipo.hk-applications --format json
hithink-finance ipo hk-applications --format json
```

## 参数选择策略

| 参数                     | 必填 | 说明                                                                        |
| ------------------------ | ---- | --------------------------------------------------------------------------- |
| `--page <value>`         | 否   | page number starting at 1；默认: 1                                          |
| `--output <path>`        | 否   | write the response or data rows to a file                                   |
| `--file-format <format>` | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 使用 `--page` 逐页查询，页码从 1 开始；分页状态以响应 pagination.has_next 为准。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
