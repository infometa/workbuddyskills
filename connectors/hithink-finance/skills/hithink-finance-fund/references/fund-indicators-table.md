# `hithink-finance fund indicators-table`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema fund.indicators-table --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端调用先用 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。
- 已知基金集合用 code_selectors.include 的 fund_code + thscodes 显式选择；indexes 每项包含 index_id，排序 sort 每项包含 idx 与 type。

## 命令

```bash
hithink-finance schema fund.indicators-table --format json
hithink-finance fund indicators-table --code-selectors '{"include":[{"type":"fund_code","thscodes":["000001.OF"]}]}' --indexes '[{"index_id":"maxDrawDownWeek"}]' --page-info '{"page_begin":0,"page_size":20,"code_begin":0,"code_page_size":20}' --output fund-indicators.json --format json
```

JSON 参数作为单个字符串传给 CLI，CLI 负责 URL 编码。示例适用于 POSIX shell 和 PowerShell 7.3+ 的标准原生参数传递；其他执行器用参数数组或其原生引用方式。

## 参数选择策略

| 参数                      | 必填 | 说明                                                                                                                                  |
| ------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `--code-selectors <json>` | 否   | JSON object with include[]; fund_code/stock_code selectors use thscodes[], other types use values[]；上游参数: code_selectors         |
| `--indexes <json>`        | 否   | JSON array: required index_id; optional timestamp and attribute                                                                       |
| `--page-info <json>`      | 否   | JSON object: optional integer page_begin/page_size/code_begin/code_page_size; verify progress from returned rows；上游参数: page_info |
| `--sort <json>`           | 否   | JSON array with required integer idx and string type                                                                                  |
| `--output <path>`         | 否   | write the response or data rows to a file                                                                                             |
| `--file-format <format>`  | 否   | output file format (requires --output)；可选: json, ndjson, csv；默认: json                                                           |

## 窗口与分页

- 无额外时间窗口限制，仍按命令参数和上游返回为准。
- 通过 `--page-info` 传 JSON 对象：page_begin、page_size、code_begin、code_page_size 为可选整数，起点为 0。是否实际推进须核对返回的唯一代码与 total；不能仅凭页码变化认定翻页成功。

## 常见错误

- 参数校验失败时按 `error.hint` 修正，不要猜字段名。
- 认证失败时先用 `auth status` 检查当前方式，再按 shared 的认证流程恢复。
- 核对响应 data.data 的唯一 thscode 数与 data.total；改变 page_info 后没有新增主键时停止，不把重复页当新增数据。已知代码可显式分批；未确认全集时报告已取得范围。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
