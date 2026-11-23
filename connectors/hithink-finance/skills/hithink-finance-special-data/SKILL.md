---
name: hithink-finance-special-data
description: '通过 hithink-finance CLI 查询涨停池、跌停池、炸板池、连板天梯、股票异动及原因、热股与热度排名、龙虎榜和机构营业部记录。'
---

# hithink-finance-special-data

特色榜单和事件型数据入口。强调窗口约束和榜单口径，不替代普通行情或财报。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图                     | 首选命令 / 路由                                                                               |
| ---------------------------- | --------------------------------------------------------------------------------------------- |
| 今日异动列表/异动标签        | `special anomaly-list`，仅今日                                                                |
| 最多 50 只股票的今日异动原因 | `special anomaly-stock`，仅今日                                                               |
| 涨停池分页                   | `special limit-up-pool`                                                                       |
| 跌停池分页                   | `special limit-down-pool`                                                                     |
| 炸板池分页                   | `special limit-break-pool`                                                                    |
| 连板天梯                     | `special limit-up-ladder`                                                                     |
| 飙升榜                       | `special skyrocket`                                                                           |
| 当前热股榜                   | `special hot-stock`                                                                           |
| 历史热股榜                   | `special hot-stock-history`                                                                   |
| 单股热度趋势                 | `special hot-stock-trend`                                                                     |
| 龙虎榜/机构/游资             | `special dragon-tiger`                                                                        |
| 市场涨停汇总与连板统计       | `special limit-up-statistics`                                                                 |
| 单股龙虎榜机构金额           | `special dragon-tiger-stock-institution`                                                      |
| 营业部经典战绩与历史记录     | `special dragon-tiger-department-classic-record` 或 `special dragon-tiger-department-history` |
| 严重异动与重点监控           | `special abnormal-monitor`                                                                    |
| 集合竞价机会与可选日期       | `special auction-opportunities` 与 `special auction-opportunity-dates`                        |

## Shortcuts

| 命令                                                                                                           | 何时使用                                                |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| [special abnormal-monitor](references/special-abnormal-monitor.md)                                             | Query severe anomaly and monitored stock records        |
| [special anomaly-list](references/special-anomaly-list.md)                                                     | Query today-only anomaly analysis rows                  |
| [special anomaly-stock](references/special-anomaly-stock.md)                                                   | Query today-only anomalies for up to 50 raw code tokens |
| [special auction-opportunities](references/special-auction-opportunities.md)                                   | Query real-time or historical auction opportunities     |
| [special auction-opportunity-dates](references/special-auction-opportunity-dates.md)                           | Query available auction opportunity dates               |
| [special dragon-tiger](references/special-dragon-tiger.md)                                                     | Query dragon-tiger board records                        |
| [special dragon-tiger-department-classic-record](references/special-dragon-tiger-department-classic-record.md) | Query department classic records                        |
| [special dragon-tiger-department-history](references/special-dragon-tiger-department-history.md)               | Query a page of department historical records           |
| [special dragon-tiger-stock-institution](references/special-dragon-tiger-stock-institution.md)                 | Query institution amounts for a single stock            |
| [special hot-stock](references/special-hot-stock.md)                                                           | Query the current hot-stock ranking                     |
| [special hot-stock-history](references/special-hot-stock-history.md)                                           | Query a historical hot-stock ranking                    |
| [special hot-stock-trend](references/special-hot-stock-trend.md)                                               | Query one stock hot-rank trend                          |
| [special limit-break-pool](references/special-limit-break-pool.md)                                             | Query the limit-break stock pool                        |
| [special limit-down-pool](references/special-limit-down-pool.md)                                               | Query the limit-down stock pool                         |
| [special limit-up-ladder](references/special-limit-up-ladder.md)                                               | Query the 30-day limit-up ladder                        |
| [special limit-up-pool](references/special-limit-up-pool.md)                                                   | Query the limit-up stock pool                           |
| [special limit-up-statistics](references/special-limit-up-statistics.md)                                       | Query limit-up market and board statistics              |
| [special skyrocket](references/special-skyrocket.md)                                                           | Query the skyrocket ranking                             |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance special <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- today-only 能力不能补历史；用户要历史时说明边界并选择有历史窗口的命令。
- 榜单热度不是投资建议，不要扩写成推荐或确定性原因。
