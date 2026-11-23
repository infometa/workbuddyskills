---
name: hithink-finance-news
description: '通过 hithink-finance CLI 查询资讯详情、快讯、公告解读、热门专题、日期范围异动解读和个股分时新闻。'
---

# hithink-finance-news

资讯查询入口。保留正文 HTML、链接、字符串标识、空值与原有顺序。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图             | 首选命令 / 路由                                                      |
| -------------------- | -------------------------------------------------------------------- |
| 已知资讯标识的正文   | `news article-detail --client-type WEB --encoded-seq <id>`           |
| 栏目快讯             | `news flash-list --tag-id <id> --seq 0`                              |
| 刷新快讯             | `news flash-refresh --tag-id <id> --seq <seq> --create-time-ms <ms>` |
| 公告详情与结构化解读 | `news notice-detail --seq <id>`                                      |
| 热门深度专题         | `news topic-hot-list --tab-id <id>`                                  |
| 日期范围异动解读     | `news anomaly-analysis --begin-date <date> --end-date <date>`        |
| 个股分时新闻         | `news stock-timeline-list --thscode 300033.SZ --offset first`        |

## Shortcuts

| 命令                                                               | 何时使用                                        |
| ------------------------------------------------------------------ | ----------------------------------------------- |
| [news anomaly-analysis](references/news-anomaly-analysis.md)       | Query anomaly interpretations over a date range |
| [news article-detail](references/news-article-detail.md)           | Query news article detail                       |
| [news flash-list](references/news-flash-list.md)                   | Query a page of news flashes                    |
| [news flash-refresh](references/news-flash-refresh.md)             | Refresh news flashes from a supplied cursor     |
| [news notice-detail](references/news-notice-detail.md)             | Query announcement detail and interpretation    |
| [news stock-timeline-list](references/news-stock-timeline-list.md) | Query stock timeline news                       |
| [news topic-hot-list](references/news-topic-hot-list.md)           | Query hot news topics                           |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance news <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- 栏目与内容标识由调用方按接口提供；内容链接不保证能转换为资讯详情标识。
- 快讯只承诺单次查询，分页与刷新边界以接口说明为准；seq 必须使用字符串以保留长整数精度。
- 公告查询提供已有结构化解读；公告正文、PDF 与附件超出当前范围。
