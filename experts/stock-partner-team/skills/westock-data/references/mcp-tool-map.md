# westock-data → westock-mcp 工具映射

本技能通过 **westock-mcp** 连接器的 `data_*` 系列 MCP Tool 取数，不再运行本地 `scripts/`。

返回格式：`{ "ok": true|false, "data": ..., "message": "..." }`。`ok: false` 时原样转述 `message`，禁止编造。

## 核心映射

| 场景 | MCP Tool | 主要参数 |
|------|----------|----------|
| 搜索股票/基金/板块 | `data_search` | `query`, `type`(stock/etf/sector/index) |
| 实时行情 | `data_quote` | `code` 或 `codes`(逗号分隔), `date` |
| 诊股评分 | `data_score` | `code`/`codes`, `date` |
| K 线 | `data_kline` | `code`, `period`, `limit`, `fq`, `start`, `end` |
| 分时 | `data_minute` | `code`, `days` |
| 财务报表 | `data_finance` | `code`/`codes`, `type`, `num` |
| 公司简况 | `data_profile` | `code` |
| 资金流向 | `data_fund_flow` | `code`/`codes`, `date`, `start`, `end` |
| 融券 | `data_fund_short` | `code`/`codes`, `date` |
| 融资融券 | `data_fund_margin` | `code`, `date` |
| 大宗交易 | `data_fund_block` | `code`, `date` |
| 回购 | `data_buyback` | `code`, `start`, `end` |
| 风险事件 | `data_risk` | `code`/`codes`, `types` |
| 龙虎榜 | `data_lhb` | `type`, `date` |
| 新闻 | `data_news` | `mode`(list/detail), `symbol`, `id`, `limit` |
| 公告 | `data_notice` | `mode`(list/detail), `symbol`, `id`, `limit` |
| 机构评级 | `data_rating` | `code` |
| 一致预期 | `data_consensus` | `code` |
| 研报 | `data_report` | `mode`, `symbol`, `id`, `limit` |
| 脱水研报 | `data_dehydrated` | `mode`, `id`, `limit` |
| 技术指标 | `data_technical` | `code`/`codes`, `group`/`indicator`, `date`, `start`, `end` |
| 筹码 | `data_chip` | `code`/`codes`, `date`, `start`, `end` |
| 股东 | `data_shareholder` | `code`/`codes` |
| 分红 | `data_dividend` | `code`/`codes`, `years` |
| ETF | `data_etf` | `code`/`codes`, `aspect`, `date`, `start`, `end` |
| 热搜/热榜 | `data_hot` | `kind`(stock/wechat/news/board/etf), `limit` |
| 股单 | `data_stocklist` | `mode`(rank/detail), `id`, `sort`, `limit`, `offset` |
| 投资日历 | `data_calendar` | `date`, `event`, `market`, `limit` |
| 交易日历 | `data_trade_calendar` | `date`, `start`, `end`, `year`, `trading_only` |
| 停复牌 | `data_suspension` | `market` |
| 公司事件 | `data_events` | `code`/`codes`, `types` |
| 新股 | `data_ipo` | `market` |
| 市场总览 | `data_market_overview` | `type`, `date` |
| 涨跌分布 | `data_changedist` | `type` |
| 指数成份 | `data_index` | `mode`, `code`/`codes`, `query`, `limit` |
| 陆股通 | `data_connect` | `exchange`(sh/sz), `limit`, `offset` |
| 板块 | `data_sector` | `mode`(list/search/constituent/info/ranking/oper), `query`, `code`, `scope`, `limit` |
| 宏观 | `data_macro` | `mode`, `names`, `year`, `date`, `start`, `end` |
| 产业链 | `data_industry_chain` | `code`, `mode`, `theme`, `category` |
| 北向持仓 | `data_north_holding` | `code`/`codes`, `date` |
| 南下持仓 | `data_south_holding` | `code`/`codes`, `date` |
| 期货 | `data_futures` | `mode`, `query`, `code` |
| 外汇 | `data_forex` | `mode`, `query` |
| 债券 | `data_bond` | `code`/`codes` |

## 板块/概念查询（两步）

1. `data_sector`：`mode=search`, `query=华为` → 获取板块 `code`
2. `data_sector`：`mode=constituent`, `code=<板块码>` → 获取成份股

## 批量查询

支持 `codes` 参数的 Tool（如 `data_quote`、`data_kline`）用逗号分隔多股，**只调 1 次**。

## 旧 CLI 对照（迁移参考）

| 旧 CLI | 新 MCP |
|--------|--------|
| `westock-data search 茅台` | `data_search` query=茅台 |
| `westock-data quote sh600519` | `data_quote` code=sh600519 |
| `westock-data sector --search 华为` | `data_sector` mode=search query=华为 |
| `westock-data sector style_pt01801517` | `data_sector` mode=constituent code=style_pt01801517 |
| `westock-data lgt sh` | `data_connect` exchange=sh |
| `westock-data watchlist rank` | `data_stocklist` mode=rank |
