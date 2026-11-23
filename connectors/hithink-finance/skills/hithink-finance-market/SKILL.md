---
name: hithink-finance-market
description: '通过 hithink-finance CLI 查询 A 股实时价格、行情快照、集合竞价、历史 K 线、交易日历、复权因子和公司行动，导出本地历史行情面板。'
---

# hithink-finance-market

普通行情和本地行情派生能力。优先使用本地库覆盖的历史/面板能力，必要时走远端同花顺金融数据服务。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图                                   | 首选命令 / 路由                                                   |
| ------------------------------------------ | ----------------------------------------------------------------- |
| 单票历史日线/K 线                          | `market history`；`--source auto` 会在本地覆盖时走本地            |
| 多只 A 股历史 K 线                         | `market history-batch --thscodes <codes>`；每批最多 10 个原始代码 |
| 实时或分页行情快照                         | `market snapshot`                                                 |
| 集合竞价实时/终态快照                      | `market auction-snapshot`                                         |
| 集合竞价短期基准                           | `market auction-benchmark`                                        |
| 交易日历                                   | `market calendar`                                                 |
| 复权因子                                   | `market adjustment-factors`                                       |
| 公司行动/除权除息事件                      | `market corporate-actions`                                        |
| 全市场区间面板/批量研究输入                | `market panel --output <file>`                                    |
| 涨跌停池、炸板池、连板、热股、龙虎榜、异动 | 切到 `hithink-finance-special-data`                               |

## Shortcuts

| 命令                                                                 | 何时使用                                                                                                                      |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [market adjustment-factors](references/market-adjustment-factors.md) | 查询本地日级复权因子；需要本地库。                                                                                            |
| [market auction-benchmark](references/market-auction-benchmark.md)   | Query the short-term auction benchmark; omit date for the Asia/Shanghai current date and read resolved date/date_ms from data |
| [market auction-snapshot](references/market-auction-snapshot.md)     | Query auction snapshots whose timestamp is the response assembly timestamp                                                    |
| [market calendar](references/market-calendar.md)                     | Query the one-year A-share trading calendar                                                                                   |
| [market corporate-actions](references/market-corporate-actions.md)   | Query adjustment events                                                                                                       |
| [market history](references/market-history.md)                       | Query daily A-share history                                                                                                   |
| [market history-batch](references/market-history-batch.md)           | Query daily A-share history for multiple thscodes                                                                             |
| [market panel](references/market-panel.md)                           | 需要本地库覆盖请求窗口；适合作为研究样本输入。                                                                                |
| [market snapshot](references/market-snapshot.md)                     | Query A-share price snapshots                                                                                                 |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance market <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- 不提供投资建议、买卖判断或收益承诺；只返回数据或中立统计。
- 全市场、长区间、多标的结果必须落盘，只汇报路径、行数和关键元信息。
