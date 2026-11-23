---
name: hithink-finance-options
description: '通过 hithink-finance CLI 查询期权品种、合约目录与详情、交易时段、分时和日 K 行情。'
---

# hithink-finance-options

期权公开资料和行情入口。按完整 thscode 和固定行情参数查询。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图   | 首选命令 / 路由                      |
| ---------- | ------------------------------------ |
| 期权品种   | `options varieties`                  |
| 合约详情   | `options contract-detail`            |
| 分时或日 K | `options intraday` / `options daily` |

## Shortcuts

| 命令                                                               | 何时使用                                      |
| ------------------------------------------------------------------ | --------------------------------------------- |
| [options contract-detail](references/options-contract-detail.md)   | Query options contract details                |
| [options contracts](references/options-contracts.md)               | List options contracts                        |
| [options daily](references/options-daily.md)                       | Query fixed 1d options prices                 |
| [options intraday](references/options-intraday.md)                 | Query current options session intraday prices |
| [options session-timeline](references/options-session-timeline.md) | Query options session timeline                |
| [options varieties](references/options-varieties.md)               | List public options varieties                 |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance options <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- 分时 session 仅为 pre_market、intraday 或 post_market。
- 日 K 周期固定 1d；start/end 必须成对提供。
- 金融数值与日期允许 null，未知期权枚举保留原始编码。
