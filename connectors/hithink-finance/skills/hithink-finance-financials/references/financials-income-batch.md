# `hithink-finance financials income-batch`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema financials.income-batch --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。

## 命令

```bash
hithink-finance schema financials.income-batch --format json
hithink-finance financials income-batch --thscodes <codes> --format json
hithink-finance financials income-batch --codes-file codes.txt --output result.json --format json
```

## 参数选择策略

| 参数                        | 必填 | 说明                                                                        |
| --------------------------- | ---- | --------------------------------------------------------------------------- |
| `--thscodes <codes>`        | 是   | comma-separated complete thscodes; raw token limit applies                  |
| `--period <period>`         | 否   | financial period；可选: annual, quarterly；默认: annual                     |
| `--limit <number>`          | 否   | recent report count (1-20)                                                  |
| `--start-ms <milliseconds>` | 否   | range start in milliseconds；上游参数: start                                |
| `--end-ms <milliseconds>`   | 否   | range end in milliseconds；上游参数: end                                    |
| `--output <path>`           | 否   | write the response or data rows to a file                                   |
| `--file-format <format>`    | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json |

## 窗口与分页

- 所有代码共享 period 以及最近 N 期或起止区间；两种模式互斥。
- 无分页参数；仍检查返回中的 count/数组长度。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。

## 批量操作说明

- 每批最多 10 个原始代码；先检查上限再规范化、稳定去重，按服务返回顺序保留代码分组。
- data.item 每组含 thscode、timestamp 和原记录数组；合法空组保留，无效标的由服务省略，调用成功时退出 0。CSV/NDJSON 每行导出一个代码分组。
- 每条命令发送一个批量查询；传输或业务错误由调用方处理。OAuth 仍沿用已确认鉴权拒绝后的单次凭据恢复。
- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 支持 `--codes-file` 或 `--codes-stdin` 读取多 thscode；不要同时用 `--api-key-stdin` 和 `--codes-stdin`。
