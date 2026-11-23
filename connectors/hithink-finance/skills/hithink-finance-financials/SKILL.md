---
name: hithink-finance-financials
description: '通过 hithink-finance CLI 查询 A 股利润表、资产负债表、现金流量表和财务指标；支持单只或批量查询、年报和季报窗口。'
---

# hithink-finance-financials

A 股财务报表和指标入口。把报告期、时间窗口和 limit 约束转成稳定命令。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图                | 首选命令 / 路由                                                                               |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| 利润表/收入成本利润项目 | `financials income`                                                                           |
| 资产负债结构            | `financials balance-sheet`                                                                    |
| 现金流量项目            | `financials cash-flow`                                                                        |
| 多只股票的三大财务报表  | `financials income-batch`、`balance-sheet-batch` 或 `cash-flow-batch`；每批最多 10 个原始代码 |
| 单个报告期的财务指标    | `financials indicators`                                                                       |
| 用户问价格或涨跌        | 切到 `hithink-finance-market`                                                                 |

## Shortcuts

| 命令                                                                           | 何时使用                                                       |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| [financials balance-sheet](references/financials-balance-sheet.md)             | Query balance-sheet financial statements                       |
| [financials balance-sheet-batch](references/financials-balance-sheet-batch.md) | Query balance-sheet financial statements for multiple thscodes |
| [financials cash-flow](references/financials-cash-flow.md)                     | Query cash-flow financial statements                           |
| [financials cash-flow-batch](references/financials-cash-flow-batch.md)         | Query cash-flow financial statements for multiple thscodes     |
| [financials income](references/financials-income.md)                           | Query income financial statements                              |
| [financials income-batch](references/financials-income-batch.md)               | Query income financial statements for multiple thscodes        |
| [financials indicators](references/financials-indicators.md)                   | Query financial indicators for a report                        |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance financials <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- 财务报表窗口最多 10 年；超过时拆分不重叠窗口并合并去重。
- `--limit` 与 `--start-ms/--end-ms` 互斥；不要同时传。
