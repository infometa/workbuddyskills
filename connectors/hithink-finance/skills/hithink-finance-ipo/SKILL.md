---
name: hithink-finance-ipo
description: '通过 hithink-finance CLI 查询 A 股新股申购和上市日历、港股递表与认购日历，以及发行价格、每手股数和入场费等新股资料。'
---

# hithink-finance-ipo

新股资料与发行阶段查询入口。区分沪深、北交所和港股；港股发行标识来自日历。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图                       | 首选命令 / 路由                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| A 股发行、可申购或待上市新股   | `ipo a-share-calendar --market sh_sz\|bj --status upcoming\|subscribable\|awaiting_listing` |
| 港股递表记录                   | `ipo hk-applications`                                                                       |
| 港股认购或待上市日历           | `ipo hk-calendar`                                                                           |
| 港股发行价格、每手股数和入场费 | `ipo hk-issue-detail --issue-code <id>`                                                     |

## Shortcuts

| 命令                                                       | 何时使用                                           |
| ---------------------------------------------------------- | -------------------------------------------------- |
| [ipo a-share-calendar](references/ipo-a-share-calendar.md) | Query A-share IPO dates and subscription status    |
| [ipo hk-applications](references/ipo-hk-applications.md)   | Query a page of Hong Kong IPO applications         |
| [ipo hk-calendar](references/ipo-hk-calendar.md)           | Query Hong Kong IPO subscription and listing dates |
| [ipo hk-issue-detail](references/ipo-hk-issue-detail.md)   | Query Hong Kong IPO issue price range and lot size |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance ipo <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- 发行资料不提供申购、交易或投资建议。
- 发行记录标识与正式证券代码分别使用，不补造 thscode。
