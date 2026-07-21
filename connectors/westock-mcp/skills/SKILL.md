---
name: westock-skill
description: 提供实时行情，支持条件选股、自选管理、股价提醒与模拟交易
version: "1.0.0"
author: "腾讯自选股"
---

# 腾讯自选股 WeStock Skill

本 Skill 提供腾讯自选股/微证券 MCP 的完整能力：查询 A股/港股/美股等市场数据，按条件/策略/标签筛选股票，管理用户自选股、股价提醒与模拟交易。

**返回格式**：`{ "ok": true|false, "data": ..., "message": "..." }`。`ok: false` 时原样转述 `message`，禁止编造。

**代码格式**：`sh600519`（沪）/ `sz000001`（深）/ `hk00700`（港）/ `usAAPL`（美）；板块 `pt01801080`。

---

## 可用工具

### data_search - 搜索股票/基金/板块

按名称、代码或拼音搜索标的。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| query | string | ✅ | 搜索关键词 |
| type | string | - | stock/etf/bond/sector/index/futures/forex，默认 stock |
| jpkr_market | string | - | 日韩市场 jp/kr |
| limit | integer | - | 返回条数，默认 10 |

**使用示例**：
- 用户只说「宁德时代」：先 `data_search`，再用返回的 code 查行情
- 找 ETF：`type=etf`；找板块：`type=sector`

---

### data_quote - 股票行情快照

最新价、涨跌幅等；支持多只批量（`codes` 逗号分隔）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 单只或多只代码 |
| date | string | - | 历史日期 YYYY-MM-DD |

**使用示例**：对比茅台和平安银行 → `codes: "sh600519,sh600036"`

---

### data_kline - K 线

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| period | string | - | day/week/month/season/year |
| limit | integer | - | 条数，默认 100 |
| fq | string | - | qfq/hfq，空为不复权 |
| start / end | string | - | 日期范围 |

---

### data_minute - 分时

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | - | 股票代码 |
| days | integer | - | 天数，默认 1 |

---

### data_technical - 技术指标

KDJ/MACD/RSI/BOLL 等。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| group / indicator | string | - | 指标名，逗号分隔，如 macd |
| date / start / end | string | - | 单日或区间 |

---

### data_chip - 筹码分布

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| date / start / end | string | - | 日期 |

---

### data_hot - 热门数据

热搜股、热基、热榜等。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| kind | string | - | stock/wechat/news/board/etf |
| limit | integer | - | 默认 50 |

---

### data_stocklist - 股单/排行榜

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | rank/detail |
| id | string | - | 股单 ID |
| sort | string | - | 排序字段 |
| limit / offset | integer | - | 分页 |

---

### data_finance - 财务报表

利润表/资产负债表/现金流量表。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| type | string | - | income/balance/cashflow；省略则拉取三大报表 |
| num | integer | - | 期数，默认 1 |
| start / end | string | - | 报告期范围 |

---

### data_disclosure - 信息披露预约

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |

---

### data_rating - 机构评级

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |

---

### data_consensus - 机构一致预期

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |

---

### data_score - 诊股评分

指定股票多维诊股评分（Comp/Cap/Funm 等）。**全市场排行用 `tool_ranking`，勿混淆**。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| date | string | - | 可选日期 |

---

### data_report - 研究报告

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/detail，默认 list |
| symbol | string | list 时 | 股票代码 |
| id | string | detail 时 | 研报 ID |
| page | integer | - | 页码，默认 1 |
| limit | integer | - | 默认 20 |

---

### data_dehydrated - 脱水研报

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/detail |
| id | string | detail 时 | 研报 ID |
| page | integer | - | 页码，默认 1 |
| limit | integer | - | 默认 10 |

---

### data_profile - 公司概况

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |

---

### data_fund_flow - 资金流向

A 股最全；港股部分字段；美股为卖空相关数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| date | string | - | 快照日期；历史区间用 start+end（仅单 code） |
| start / end | string | - | 历史日期区间（仅单 code） |

---

### data_fund_short - 融券数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| date / start / end | string | - | 日期 |

---

### data_fund_margin - 融资融券明细

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | - | 股票代码 |
| date | string | - | 日期 |

---

### data_fund_block - 大宗交易

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | - | 股票代码 |
| date | string | - | 日期 |

---

### data_north_holding - 北向资金持仓

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| date | string | - | YYYY-MM-DD |

---

### data_south_holding - 南下资金持仓

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 仅港股 hk 前缀 |
| date | string | - | YYYY-MM-DD |

---

### data_shareholder - 股东信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |

---

### data_dividend - 分红送转

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| years | integer | - | 查询年数，默认 1 |
| all | boolean | - | 是否包含未实际分红记录，默认 false |

---

### data_buyback - 回购数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | - | 股票代码 |
| start / end | string | - | 日期范围 |

---

### data_news - 新闻资讯

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/detail |
| symbol | string | list 时 | 股票代码 |
| id | string | detail 时 | 新闻 ID |
| limit | integer | - | 默认 20 |

---

### data_notice - 公告查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/detail，默认 list |
| symbol | string | list 时 | 股票代码 |
| id | string | detail 时 | 公告 ID |
| type | string | - | 公告类型，默认 0（全部） |
| limit | integer | - | 默认 20 |

---

### data_calendar - 财经日历

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | - | 查询日期 |
| event | string | - | 事件类型 |
| market | string | - | hs/hk/us（小写） |
| limit | integer | - | 默认 10 |

---

### data_trade_calendar - 交易日历

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | - | 单日 YYYY-MM-DD（与 start/end/year 互斥） |
| start / end | string | - | 区间 |
| year | integer | - | 查整年 |
| trading_only | boolean | - | 仅交易日，默认 false |
| limit | integer | - | 返回条数上限，默认 50 |
| offset | integer | - | 偏移量，默认 0 |

---

### data_suspension - 停牌列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| market | string | - | HS/HK/US |

---

### data_events - 公司事件

查指定股票的事件标签（大宗交易/分红/停牌等）。**全市场事件选股用 `tool_event`**；无 code 且 types 空时返回事件类型目录。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| types | string | - | 事件类型 ID(1-42) 逗号分隔；空参返回类型目录 |

---

### data_risk - 风险提示

单股风险事件明细（质押/解禁/诉讼等，仅 A 股）。**全市场筛 ST 等标签股用 `tool_label`**；无 code 时返回风险类型列表。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |
| types | string | - | 如 st/pledge/unlock/lawsuit 等；逗号分隔 |

---

### data_lhb - 龙虎榜

不传 date 时由上游返回最近可用交易日数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| type | string | - | jg/yzb/yyb/gslmr/gslxw 或 institution/hotmoney 等；逗号分隔，默认全部 |
| date | string | - | 交易日 YYYY-MM-DD，可选 |

---

### data_ipo - 新股 IPO

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| market | string | - | HS/HK/US |

---

### data_market_overview - 市场总览

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| type | string | - | summary/trade/interval/technical/updown/margin/valuation/rotation/all，默认 summary |
| date | string | - | 日期 |

---

### data_changedist - 涨跌分布

沪深 A 股涨跌分布（涨跌家数/涨跌停/区间/成交额）。type 默认 0。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| type | string | - | 市场类型，默认 0（沪深 A 股） |

---

### data_index - 指数数据

指数列表/搜索/成分股。mode: list(默认)|search|constituent。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/search/constituent |
| query | string | search 时 | 搜索关键词 |
| code / codes | string | - | 指数代码如 sh000300 |
| limit | integer | - | 默认 50 |

---

### data_connect - 陆股通成份股

沪/深股通成份股名单（陆股通北向可买入标的）。查持股明细用 `data_north_holding`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| exchange | string | - | sh(沪股通)/sz(深股通)，默认 sh |
| limit / offset | integer | - | 分页 |

---

### data_sector - 板块数据

清单/搜索/成份股/概况/排名/经营数据。list 时 scope 用 sw1 等；板块码可作 `tool_filter`/`tool_ranking` 的 universe。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/search/constituent/info/ranking/oper，默认 list |
| query | string | search 时 | 关键词 |
| code | string | constituent 时 | 板块代码，裸码 pt01801080 或 sw1_pt01801080 |
| scope | string | list 时 | industry_list_sw1 或 sw1(申万一级) 等 |
| date | string | - | 查询日期 YYYY-MM-DD，默认今天 |
| limit | integer | - | 默认 50 |

**使用示例**：「华为概念股」→ `mode=search, query=华为` 拿 code → `mode=constituent, code=...`

---

### data_macro - 宏观经济数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list(指标目录)/indicator(默认拉数)/expect(海外预期) |
| names | string | - | 指标名，逗号分隔，如 cn_cpi_ppi |
| region | string | - | 地区 |
| area | string | - | 区域列表，逗号分隔 |
| year / date / start / end | string | - | 时间 |

---

### data_industry_chain - 产业链

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list(主题列表，默认)/graph(需 theme)/stock(需 code 查个股归属) |
| theme | string | graph 时 | 产业主题名 |
| code | string | stock 时 | 股票代码 |
| category | string | list 时 | upstream 仅上中下游 |

---

### data_etf - ETF 数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | ETF 代码 |
| aspect | string | - | holdings/nav/company/holders/financial，默认详情快照 |
| date / start / end | string | - | 日期 |

---

### data_futures - 期货

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | search/list/quote/detail |
| query | string | search 时 | 关键词 |
| code | string | - | 合约代码 |

---

### data_forex - 外汇

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| mode | string | - | list/quote |
| query | string | - | 搜索关键词 |

---

### data_bond - 债券/可转债

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | - | 债券代码 |
| terms / schedule | boolean | - | 是否查条款/付息计划 |

---

### tool_filter - 条件选股

自定义表达式或预设条件筛选股票。标签股票池（央企/ST）请用 `tool_label`，勿作 universe。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| expression / preset | string | 二选一 | 表达式或预设名 |
| market | string | - | hs/hk/us，默认 hs |
| universe | string | - | 可选板块码(11010001/pt01801080 等)或 hs/hk/us |
| date | string | - | 基准日期 YYYY-MM-DD，默认今天 |
| orderby / order | string | - | 排序字段 / asc|desc |
| limit | integer | - | 默认 20 |
| max_pe / max_pb / min_dividend 等 | string | - | 预设调参，见 `tool_list_presets` |

**使用示例**：`expression: "intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])"`

---

### tool_list_presets - 列出预设选股条件

无必填参数。不确定可用预设时先调用本 Tool。

---

### tool_strategy - 策略选股

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| names | string | ✅ | 策略短名，逗号分隔，如 macd_golden（勿 strategy_ 前缀） |
| date | string | - | 快照日期，默认今天 |
| start / end | string | - | 区间查询（与 date 互斥） |
| limit | integer | - | 默认 20 |
| offset | integer | - | 偏移量，默认 0 |

**使用示例**：「MACD 金叉信号股」→ `names: "macd_golden"`

---

### tool_list_strategies - 列出可用策略

不确定时先调本工具；部分付费策略不可用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group | string | - | 按分组过滤 |

---

### tool_label - 标签选股

勿用 `tool_filter` 的 universe；单股风险明细用 `data_risk`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| names | string | ✅ | 标签短名，如 shareholder_central_state、risk_st |
| asset | string | - | stock/etf，默认 stock |
| date | string | - | 快照日期，默认今天 |
| start / end | string | - | 区间查询 |
| limit | integer | - | 默认 20 |
| offset | integer | - | 偏移量，默认 0 |

**使用示例**：「央企股票」→ `names: "shareholder_central_state"`

---

### tool_list_labels - 列出可用标签

不确定 names 时先调本工具；部分付费标签不可用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| asset | string | - | stock/etf |
| group | string | - | 分组过滤 |

---

### tool_event - 事件驱动选股

查单股事件标签用 `data_events`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| names | string | ✅ | 事件短名，逗号分隔 |
| limit | integer | - | 默认 20 |
| offset | integer | - | 偏移量，默认 0 |

---

### tool_list_events - 列出可用事件

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group | string | - | 分组过滤 |

---

### tool_ranking - 多因子排行选股

metric 必填且须与 asset 匹配；见 `tool_list_ranking_metrics`。已知 codes 查评分用 `data_score`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| metric | string | ✅ | 排行指标；股票如 CompScore，ETF 如 size |
| asset | string | - | stock/etf，默认 stock |
| type | string | - | 评分变动周期: cur/weekly/monthly（仅评分类指标） |
| date | string | - | 基准日期，默认今天 |
| universe | string | - | 可选板块码；非标签 |
| orderby / order | string | - | 排序字段 / asc|desc |
| limit | integer | - | 默认 20 |
| offset | integer | - | 偏移量，默认 0 |
| within_label | string | - | 可选标签短名，如 shareholder_central_state |
| within_strategy | string | - | 可选策略短名，与 within_label/event 互斥 |
| within_event | string | - | 可选事件短名，与 within_label/strategy 互斥 |
| min_fields | string | - | 最小阈值 JSON，如 `{"CompScore":70}` |

---

### tool_list_ranking_metrics - 列出排行指标

不确定 metric 时先调本工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| asset | string | - | stock/etf |
| group | string | - | 分组过滤 |

---

### portfolio_watchlist - 查询自选股

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group | string | - | 分组 ID 或名称 |
| market | string | - | A/HK/US |
| limit | integer | - | 默认 200 |
| offset | integer | - | 偏移量，默认 0 |

---

### portfolio_watchlist_groups - 查询自选分组

返回正式 `group_id`（写操作必用，勿用 tmp 前缀）。无必填参数。

**使用示例**：置顶/移动/备注前必须先调用本 Tool 获取 `group_id`。

---

### portfolio_watchlist_add - 添加自选股

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| group_id | string | - | 不传则加入「全部」 |

---

### portfolio_watchlist_remove - 删除自选股（软删除）

将股票移入「待删除」分组，**非物理删除**；查「全部」时仍可能看到。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 股票代码 |

**使用示例**：用户说「删除自选茅台」→ 调用本 Tool；回复须说明已移入待删除分组，彻底清空需用户到 App 手动清「待删除」。

---

### portfolio_watchlist_batch_add - 批量添加自选

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code / codes | string | 二选一 | 逗号分隔 |
| group_id | string | - | 目标分组 ID |

---

### portfolio_watchlist_move - 移动自选到其他分组

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| from | string | ✅ | 源分组 ID |
| to | string | ✅ | 目标分组 ID |
| retain | boolean | - | 原分组是否保留 |

---

### portfolio_watchlist_pin - 组内置顶

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| group_id | string | ✅ | 分组 ID |

---

### portfolio_watchlist_unpin - 取消置顶

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| group_id | string | ✅ | 分组 ID |

---

### portfolio_watchlist_bottom - 组内沉底

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| group_id | string | ✅ | 分组 ID |

---

### portfolio_watchlist_note - 自选备注

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码 |
| group_id | string | ✅ | 分组 ID |
| notes | string | - | 空串表示删除备注 |

---

### portfolio_watchlist_sort - 组内排序

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group_id | string | ✅ | 分组 ID |
| code / codes | string | 二选一 | 按目标顺序排列的代码列表 |
| star_count | integer | - | 置顶数量，默认 0 |

---

### portfolio_group_add - 新建自选分组

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| name | string | ✅ | 分组名称，不可与已有分组重名 |

返回正式分组 ID，可直接用于后续写操作。

---

### portfolio_group_rename - 重命名分组

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group_id | string | ✅ | 分组 ID |
| name | string | ✅ | 新名称 |

---

### portfolio_group_sort - 调整分组显示顺序

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group_ids | string | ✅ | 分组 ID 列表，逗号分隔，按目标顺序 |

---

### portfolio_tips_query - 查询股价提醒

查询当前用户已设置的全部股价提醒。返回 `tips` 数组，字段空串或 0 表示未开启。无必填参数。

| 返回字段 | 说明 |
|------|------|
| code | 股票代码 |
| high / low | 价格涨至 / 跌至提醒 |
| updown | 涨跌幅阈值提醒(%) |
| pdrhigh / pdrlow | 场内 ETF 溢折率涨至 / 跌至提醒 |
| fundjz | 基金净值提醒（仅基金有效） |
| notice / research | 公告 / 研报提醒开关(1/0) |
| updatetime | 更新时间 |

**使用示例**：修改单项提醒前，必须先调本 Tool 拿到该 code 现有提醒值，用于回填。

---

### portfolio_tips_set - 新增/修改股价提醒

⚠️ 上游为**全量覆盖**语义：未传的字段会被清空，传空串也会清空。修改单项前**必须先调 `portfolio_tips_query`** 拿到该 code 现有提醒，把不想改动的字段原值一并带上；只有想取消的字段才传空串。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 股票代码，如 sh600519/sz000001/hk00700，兼容 600519.SH 等后缀格式 |
| high | string | - | 价格涨至提醒；传空串取消；不想改则回填 query 现值 |
| low | string | - | 价格跌至提醒；传空串取消；不想改则回填 query 现值 |
| updown | string | - | 涨跌幅超过阈值提醒(%)；传空串取消；不想改则回填 query 现值 |
| pdrhigh | string | - | 场内 ETF 溢折率涨至提醒；传空串取消 |
| pdrlow | string | - | 场内 ETF 溢折率跌至提醒；传空串取消 |
| type | string | - | 公告/研报订阅：2010 沪深公告、2011 沪深研报、2020 港股公告、2021 港股研报；传空串取消 |
| isfund | string | - | 是否基金：1 基金，0 非基金；仅 isfund=1 时 action=open 生效 |
| action | string | - | 基金净值提醒动作，open 表示打开（仅 isfund=1 有效） |

**使用示例**：
- 「贵州茅台涨到 1300 元提醒我」→ 先 `data_search` 拿代码 → `code: "sh600519", high: "1300"`
- 「宁德时代跌破 300 元提醒我」→ `code: "sz300750", low: "300"`
- 「腾讯控股日涨幅超 5% 提醒我」→ `code: "hk00700", updown: "5"`
- 为已有提醒（low=1500）的 sh600519 新增 high=1800 → 先 query 回填 → `code: "sh600519", high: "1800", low: "1500"`

---

### portfolio_paper_portfolio - 模拟交易账户概览

查询练习赛组合总资产、持仓市值、可用资金、总盈亏等。无必填参数。

**使用示例**：
- 「我的模拟账户概况」→ 直接调用
- 模拟买入/卖出前先查可用资金

---

### portfolio_paper_positions - 模拟交易持仓

查询持仓列表（成本价、现价、浮盈浮亏）。无必填参数。

**使用示例**：
- 「模拟账户里有哪些持仓」→ 直接调用
- 模拟卖出前先调用，确认可用数量

---

### portfolio_paper_profit - 模拟交易盈亏统计

查询胜率、已实现/未实现盈亏、个股收益贡献等。无必填参数。

**使用示例**：
- 「模拟交易收益怎么样」→ 结合 `portfolio_paper_portfolio` 综合分析

---

### portfolio_paper_trade - 模拟限价下单

仅沪深 A 股；虚拟资金，非真实交易。须限价单，数量须 100 整数倍。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | A 股代码，如 sh600519/sz000001 |
| direction | string | ✅ | buy / sell |
| price | number | ✅ | 限价（元） |
| quantity | integer | - | 数量（股），100 整数倍，默认 100 |

**使用示例**：
- 模拟买入平安银行 100 股 → 先 `data_quote` 拿现价，再 `code: "sz000001", direction: "buy", price: 10.16, quantity: 100`
- 用户只说「模拟买茅台」→ 先 `data_search` + `data_quote`，再下单
- 卖出无持仓时会返回业务错误，须先查 `portfolio_paper_positions`

---

### portfolio_paper_cancel - 撤销模拟委托

仅可撤销待成交订单。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| order_id | string | ✅ | 订单 ID，来自 `portfolio_paper_trade` 或 `portfolio_paper_history` |

**使用示例**：
- 撤单前先用 `portfolio_paper_history`（`range: "today"`）找待成交订单的 `orderId`

---

### portfolio_paper_history - 模拟交易记录

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| range | string | - | today（默认）/ recent（近 3 月合并）/ history（指定月） |
| month | string | history 时 ✅ | YYYYMM，如 202604 |
| code | string | - | 按股票过滤 |
| direction | string | - | buy / sell |
| limit | integer | - | 返回条数，默认 50 |
| offset | integer | - | 偏移量，默认 0 |

**使用示例**：
- 「今天的模拟交易记录」→ `range: "today"`
- 「近几个月模拟交易」→ `range: "recent"`（勿逐月遍历）
- 「2025 年 4 月模拟交易」→ `range: "history", month: "202504"`
- 「模拟交易里茅台的买卖记录」→ `code: "sh600519", range: "recent"`

---

## 注意事项

- **禁止绕过**：不用 web_search 或训练数据替代本 Connector 的行情/财务/宏观数据
- **先 search 再查**：用户只给股票名称时，先 `data_search` 拿代码
- **分工**：单股明细用 `data_*`；批量筛选用 `tool_*`；用户自选/股价提醒/模拟交易用 `portfolio_*`
- **股价提醒**：`portfolio_tips_set` 为全量覆盖语义，修改单项前必须先 `portfolio_tips_query` 回填其余字段，避免误清空已有提醒；用户只给股票名称时先 `data_search` 拿代码
- **多股批量**：同一市场、支持 `codes` 的 Tool 只调 1 次，逗号分隔
- **概念股**：用 `data_sector`（search → constituent），不要用 `data_search` 代替成份股
- **删除自选**：`portfolio_watchlist_remove` 为软删除（移入「待删除」），告知用户彻底删除需到自选股 App 清空该分组
- **空结果**：如实说明「暂无数据」，不要编造
- **模拟交易**：仅沪深 A 股、限价单、数量 100 整数倍；虚拟资金，非真实交易；撤单仅待成交订单；下单前建议先 `data_quote` 确认价格
- **投资组合类能力**（自选/股价提醒/模拟交易）操作用户本人数据，需用户完成 Connector 授权后方可使用

---

## 免责声明

> 仅提供客观市场数据与用户自选/模拟交易管理，不构成投资建议。模拟交易仅供学习体验，虚拟资金非真实交易。数据可能有延迟，以交易所官方为准。投资有风险，决策需谨慎。
