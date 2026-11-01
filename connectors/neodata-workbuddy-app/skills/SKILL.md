---
name: tencent-fintech-neodata-cards
description: >-
  NeoData 金融卡片 MCP（WorkBuddy App 授权范围 wb-buddy-app）。用单个标的代码 + 周期 + 日期区间等结构化入参，
  查询 A股/港股/美股的股票、指数、基金行情与分时/分钟/日周月季年K线、五档盘口、自选股批量行情列表、资产代码搜索，
  以及热点新闻、个股本地资讯、公告、财务报告 PDF、业绩会资料（演示文稿 / 业绩发布 / 文字稿）、宏观经济日历、宏观指标搜索与时序、证券概览、基本面概览、公司资料，返回结构稳定、可直接渲染图卡。
  Use when the user asks for stock/index/fund quotes and K-line charts, intraday charts, order book, watchlist snapshots,
  ticker lookup, stock news, announcements, financial report PDFs, earnings call materials and transcripts,
  macro calendar, macro indicator series, security overview with valuation percentiles, fundamentals or company profiles
  for A-share, HK or US markets.
description_zh: "A股/港股/美股行情K线、盘口、自选股、资讯公告、财报、业绩会、宏观日历与指标、证券概览与基本面卡片数据"
description_en: "Card-ready A/HK/US quotes and K-lines, order book, watchlist, news, filings, earnings calls, macro calendar and indicators, overviews and fundamentals"
version: "1.1.0"
display_name: "腾讯金融科技NeoData金融卡片"
display_name_en: "Tencent FinTech NeoData Cards"
visibility: "public"
---

# 腾讯金融科技NeoData金融卡片 MCP

> **一句话概述**：17 个卡片级工具，一次调用拿到一张图卡所需的完整数据——行情 K 线、盘口、资讯公告、财报、业绩会、宏观与基本面，覆盖 A股 / 港股 / 美股。

## 服务简介

本 MCP 是 NeoData 面向 WorkBuddy App 的**卡片数据服务**（OAuth 授权范围 `wb-buddy-app`），服务端已把多个底层数据接口聚合成「一张卡片一个工具」：例如 `get_security_overview` 一次返回行情 + 盘口 + 行业 + 市值 + 估值分位，`get_fundamental` 一次返回利润表 + 主要指标 + 现金流量表。返回结构固定、字段口径统一，适合直接画图或渲染卡片。

**能力边界**

| 维度 | 覆盖范围 |
|---|---|
| 资产类别 | 股票、指数、公募基金（场外 / 场内 ETF·LOF）、宏观经济 |
| 市场 | A股（沪深北）、港股、美股 |
| 时效 | 行情、盘口、指数为实时；K 线支持分钟级（当日）与日/周/月/季/年历史 |
| 数据主题 | 行情K线与技术指标、五档盘口、自选股列表、代码搜索、热点新闻、个股资讯、公告、财务报告、业绩会资料、宏观日历、宏观指标、证券概览、基本面、公司资料 |
| 工具数 | **17 个** |

**不覆盖**：期货、现货贵金属、外汇、债券、板块排行、资金流向、龙虎榜、研报评级等。这类问题请告知用户当前连接器未覆盖，不要用本服务的工具硬凑。

**入参形态**：全部为结构化字段，参数值一律传字符串（`get_local_news.content` 为布尔）。除 `get_watchlist` 外，**所有工具只接受单个 `code`**，传 `codes` / `stock_codes` 或逗号分隔的多个代码会直接报错。

## 数据源优先级

1. 本服务覆盖范围内的行情、资讯、公告、财报、宏观与基本面数据，一律通过本服务获取。
2. **禁止**用 `web_search`、HTTP 直连或训练记忆回答本服务可查询的问题；行情、估值、财务数据具有强时效性，必须以接口实时返回为准。
3. **禁止**把本服务数据与其他来源拼接成同一张卡片，避免口径冲突。
4. 仅当问题落在「不覆盖」范围时，才可使用其他已连接的数据源，并向用户说明来源。

## 典型使用场景

| 场景 | 场景说明 | 示例提问 | 调用工具 |
|---|---|---|---|
| **代码识别** | 名称、简称、拼音或代码转成标准代码 | 腾讯的股票代码是多少？ | `get_asset_search` |
| **个股看盘** | 实时快照、分时、分钟K、日/周/月K + 技术指标 | 贵州茅台近半年日K？<br>苹果今天分时？ | `get_stock_quote` |
| **指数看盘** | 指数分时与历史 K 线 | 上证指数今天走势？<br>纳斯达克100近两年周K？ | `get_index_quote` |
| **基金行情** | 场外净值、阶段收益、净值序列；场内 ETF/LOF 价格与 K 线 | 易方达蓝筹精选最新净值？ | `get_fund_quote` |
| **盘口** | 单标的五档买卖盘、委比 | 沪深300ETF 五档盘口？ | `get_order_book` |
| **自选股列表** | 多标的一次拿到现价、涨跌、成交、PE-TTM、营收、净利 | 茅台、五粮液、腾讯今天表现？ | `get_watchlist` |
| **证券概览卡** | 行情 + 盘口 + 行业 + 市值 + PE/PB 及 5 年分位 | 茅台现在估值贵不贵？ | `get_security_overview` |
| **基本面卡** | 营收、净利、毛利率、ROE、现金流、估值倍数 | 宁德时代2025年基本面？ | `get_fundamental` |
| **公司资料卡** | 公司简介、主营业务、上市日期、员工数、行业/概念/地域标签 | 比亚迪是做什么的？ | `get_company_profile` |
| **资讯** | 热点新闻（检索式）与个股本地资讯（可翻页、可带正文） | 腾讯最近有什么新闻？ | `get_financial_news` / `get_local_news` |
| **公告与财报** | 公告列表按类型筛选；财务报告摘要与 PDF 原文 | 茅台最近的风险提示公告？<br>苹果的年报 PDF？ | `get_stock_notice` / `get_financial_report` |
| **业绩会** | 美股演示文稿与业绩发布资料；A股、港股及查不到演示文稿的美股返回业绩会文字稿 | 英伟达最近的业绩会资料？<br>腾讯业绩会说了什么？ | `get_earning_call` |
| **宏观日历** | 经济数据公布值/预测值/前值、央行动态、财经事件、休市提醒 | 下周美国有哪些重要数据？ | `get_macro_calendar` |
| **宏观指标** | 先模糊搜索指标名，再按精确指标名查时序 | 中国CPI近一年走势？ | `search_macro_indicators` → `get_macro_indicator_data` |

## 快速上手

```text
# 1) 口语名称先查代码
get_asset_search(query="贵州茅台", type="stock")
  → 600519.SH

# 2) 画日K：日K及以上必须传 start_date，否则只返回最新一根
get_stock_quote(code="600519.SH", kline_type="day", start_date="20260427", limit="220")

# 3) 一张概览卡
get_security_overview(code="600519.SH")
```

## 调用优先级

1. 用户只给了名称 / 简称（"茅台""纳斯达克""沪深300ETF"）→ 先 `get_asset_search` 拿标准代码，不要凭印象拼代码。
2. 只要一张综合卡片（现价 + 估值 / 财务摘要 / 公司简介）→ 优先 `get_security_overview` / `get_fundamental` / `get_company_profile`，一次调用即可。
3. 需要画走势图 → `get_stock_quote` / `get_index_quote` / `get_fund_quote`，按「画图速查」填周期与 `start_date`。
4. 多只标的同时看 → `get_watchlist` 一次批量，不要循环调用 `get_stock_quote`。
5. 宏观指标时序 → 必须先 `search_macro_indicators` 拿到精确指标名，再调 `get_macro_indicator_data`。

## 代码与参数规范

### 代码格式

| 标的 | 格式 | 示例 |
|---|---|---|
| A股 | 主体代码 + 市场后缀 | `600519.SH` / `000858.SZ` / `830799.BJ` |
| 港股 | `.HK` | `00700.HK` |
| 美股 | `.US` | `AAPL.US` / `NVDA.US` |
| A股指数 | `.SH` / `.SZ` | `000001.SH`（上证指数）/ `399001.SZ` / `000300.SH` |
| 港股指数 | `.HK` | `HSI.HK` / `HSTECH.HK` |
| 美股指数 | 以 `.` 开头 + `.US` | `.IXIC.US`（纳斯达克）/ `.NDX.US`（纳斯达克100）/ `.INX.US`（标普500）/ `.DJI.US`（道琼斯） |
| 场内基金（ETF/LOF） | `.SH` / `.SZ`，行情用 `get_stock_quote` / `get_order_book` | `510300.SH` / `159915.SZ` |
| 场外基金 | `.OF`，用 `get_fund_quote` | `161725.OF` / `005827.OF` |

### 通用参数规范

| 参数 | 规范 |
|---|---|
| `code` | **单个**标的代码；除 `get_watchlist` 外所有工具都不接受多代码，也不接受 `codes` / `stock_codes` 参数名 |
| `codes` | 仅 `get_watchlist` 使用，英文逗号分隔、不含空格 |
| 日期 | 一律 `yyyyMMdd`（如 `20260101`） |
| `fiscal_period` | `{财年}-{报告期}`，如 `2025-FY`、`2026-Q1`、`2026-H1`；报告期枚举 `Q1`/`H1`/`9M`/`FY` 等 |
| `limit` / `page` | 正整数字符串；`page` 从 `1` 开始 |

### 常用枚举

| 工具.参数 | 取值 |
|---|---|
| `get_stock_quote` / `get_index_quote` / `get_watchlist` / `get_security_overview` `.kline_type` | `day`（默认）/ `week` / `month` / `season` / `year` / `m1` / `m5` / `m15` / `m30` / `m120`；**不支持 `m60`** |
| `.adjust_type`（股票类） | `0` 不复权 / `1` 前复权（默认）/ `2` 后复权；分钟级自动降级为不复权 |
| `get_fund_quote.adjust_type` | `qfq` 前复权（默认）/ `hfq` 后复权 / 空=不复权（仅对场内行情生效） |
| `get_asset_search.type` | `stock` / `index` / `fund` / `sector`，可逗号组合，如 `stock,index`；**请显式传入** |
| `get_stock_notice.notice_type` | `0` 全部 / `1` 财务报告 / `2` 配股 / `3` 增发 / `4` 股权变动 / `5` 重大事项 / `6` 风险提示 / `7` 其他公告 |
| `get_financial_report.market` | `cn` A股 / `hk` 港股 / `us` 美股 |
| `get_macro_calendar.type` | `1` 经济数据 / `2` 央行动态 / `3` 财经事件 / `4` 休市提醒（逗号多选，默认 `1,2,3`） |
| `get_macro_calendar.country` | `1` 中国 / `2` 美国 / `3` 香港 / `4` 英国 / `5` 欧洲 / `6` 亚太 / `7` 美洲（逗号多选，不传为全部） |
| `get_macro_calendar.importance` | `1` ~ `3`，数字越大越重要（逗号多选，不传为全部） |
| `get_macro_indicator_data.indicator_type` | `1` 行业经营 / `2` 全球宏观 / `3` 中国宏观 / `4` 中国地区宏观（不传查全部） |

### 画图速查（`get_stock_quote` / `get_index_quote`）

`start_date` 按「今天往前推」计算；**日 K 及以上必须传 `start_date`**，只传 `limit` 时只返回最新一根。分钟级只查当天，不需要 `start_date`。

| 图形 | `kline_type` | `start_date` | `limit` |
|---|---|---|---|
| 分时图 | `m1` | 不传 | `400` |
| 5 / 15 / 30 / 120 分钟 K | `m5` / `m15` / `m30` / `m120` | 不传 | `100` / `40` / `25` / `15` |
| 日 K（近半年） | `day` | 今天 − 180 天 | `220` |
| 周 K（近两年） | `week` | 今天 − 730 天 | `130` |
| 月 K（近六年） | `month` | 今天 − 2200 天 | `100` |
| 季 K | `season` | 今天 − 3650 天 | `60` |
| 年 K | `year` | 今天 − 7300 天 | `40` |

## 工具参考

按数据域分组，逐个给出用途、完整入参与调用示例。所有参数均为可选，除非标注 ✅。

### 代码搜索

#### `get_asset_search` - 资产搜索

按名称、简称或代码查询标的标准代码，返回的 `code` 可直接传给行情、概览等工具。结果按相关度排序，同名时会返回多条（如「腾讯」返回 `00700.HK`、`80700.HK`、`TCEHY.US`），请按 `name` 与 `type` 选择。返回 `items[]`（`code` / `name` / `type`）与 `total`；`type` 取值如 `GP_CH` A股、`GP_HK` 港股、`GP_US` 美股、`ZS_CH` / `ZS_HK` / `ZS_US` 指数。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `query` | string | ✅ | 名称、简称或代码，如 `贵州茅台`、`600519`、`腾讯`、`AAPL`、`纳斯达克`；最长 100 字 |
| `type` | string | - | `stock` / `index` / `fund` / `sector`，可逗号组合；建议显式传入，如查股票传 `stock`，查指数传 `index` |

**示例**：`get_asset_search(query="纳斯达克100", type="index")`

---

### 行情与盘口

#### `get_stock_quote` - 股票行情与 K 线

查询 A股 / 港股 / 美股个股及场内 ETF/LOF 的行情与 K 线，支持分时（`m1`）、分钟 K、日/周/月/季/年 K。返回 `items[]`（含 `market_status`、`kline_list[]`）和 `technical_list[]`（MA、EMA、BOLL、MACD、KDJ、RSI、DMI、OBV、VR 等技术指标，只覆盖最近若干交易日）。**`kline_list` 按时间倒序**，第 0 根为最新。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个股票代码，默认 `600519.SH`；如 `600519.SH`、`00700.HK`、`AAPL.US`、`510300.SH` |
| `kline_type` | string | - | K 线周期，默认 `day`；见常用枚举 |
| `adjust_type` | string | - | `0` 不复权 / `1` 前复权（默认）/ `2` 后复权 |
| `start_date` | string | - | 起始日期 `yyyyMMdd`；**日 K 及以上画历史必传** |
| `end_date` | string | - | 截止日期 `yyyyMMdd`，默认最近交易日 |
| `limit` | string | - | K 线最多返回条数，默认 `30` |

**示例**：`get_stock_quote(code="600519.SH", kline_type="day", start_date="20260427", limit="220")`

#### `get_index_quote` - 指数行情与 K 线

查询 A股 / 港股 / 美股指数的实时行情与 K 线，参数与股票一致但无 `adjust_type`，不返回技术指标。返回结构与 `get_stock_quote` 的 `items[]` 相同。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个指数代码，默认 `000001.SH`；如 `000300.SH`、`399006.SZ`、`HSI.HK`、`.NDX.US` |
| `kline_type` | string | - | K 线周期，默认 `day` |
| `start_date` | string | - | 起始日期 `yyyyMMdd`；**日 K 及以上画历史必传** |
| `end_date` | string | - | 截止日期 `yyyyMMdd` |
| `limit` | string | - | K 线最多返回条数，默认 `30` |

**示例**：`get_index_quote(code="000001.SH", kline_type="m1", limit="400")`

#### `get_fund_quote` - 基金行情与净值

查询公募基金的净值卡片：单位净值、累计净值、日涨跌、近1月/3月/1年/今年以来收益、净值序列（时间正序），以及场内份额的价格、成交、K 线、估算净值与溢价率。代码会被统一归一为 `.OF` 后缀查询，K 线周期固定为日线。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个基金代码，默认 `510300.OF`；如 `161725.OF`、`005827.OF` |
| `adjust_type` | string | - | 场内行情复权方式：`qfq`（默认）/ `hfq` / 空 |
| `start_date` | string | - | 起始日期 `yyyyMMdd` |
| `end_date` | string | - | 截止日期 `yyyyMMdd` |
| `limit` | string | - | 净值与 K 线返回条数，默认 `20` |

**示例**：`get_fund_quote(code="161725.OF", start_date="20260101", limit="120")`

#### `get_order_book` - 五档盘口

查询单个标的的实时盘口快照，不含 K 线。A股及场内 ETF/LOF 返回五档买卖价量与委比；港股、美股按实际可用档位返回（通常一档）。返回 `item`：`price`、`update_time`、`volume_unit`（A股为「手」，港美股为「股」）、`bid_ask_ratio`、`bids[]`、`asks[]`。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `600519.SH`；如 `510300.SH`、`00700.HK`、`AAPL.US` |

**示例**：`get_order_book(code="510300.SH")`

#### `get_watchlist` - 自选股行情列表

一次批量查询多只标的的列表行情：名称、现价、涨跌额、涨跌幅、成交量、成交额、换手率、量比、最高、最低、PE-TTM，以及指定财年的营业总收入与归母净利润。返回 `items[]`（取不到的字段列在 `miss`）与 `total`。**本工具是唯一接受多代码的工具**。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `codes` | string | - | 标的代码，英文逗号分隔、不含空格；默认 `600519.SH,000858.SZ,300750.SZ,00700.HK` |
| `kline_type` | string | - | K 线周期，默认 `day` |
| `adjust_type` | string | - | `0` / `1`（默认）/ `2` |
| `start_date` | string | - | 起始日期 `yyyyMMdd` |
| `end_date` | string | - | 截止日期 `yyyyMMdd` |
| `limit` | string | - | 每个标的取的 K 线条数，默认 `1`（列表只需最新一根） |
| `fiscal_period` | string | - | 营收、净利对应的财年报告期，默认 `2025-FY` |

**示例**：`get_watchlist(codes="600519.SH,000858.SZ,00700.HK,AAPL.US")`

---

### 卡片：概览、基本面与公司资料

#### `get_security_overview` - 证券概览

一次返回单个证券的概览卡片：现价、涨跌、今开、最高、最低、昨收、振幅、成交量额、换手率、量比、均价、涨跌停价、内外盘、所属行业、总市值、PE-TTM 及 5 年分位、预测 PE、实时 PB 及 5 年分位。适合回答「现在多少钱、估值贵不贵」类问题。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `600519.SH` |
| `kline_type` | string | - | K 线周期，默认 `day` |
| `adjust_type` | string | - | `0` / `1`（默认）/ `2` |
| `start_date` | string | - | 起始日期 `yyyyMMdd` |
| `end_date` | string | - | 截止日期 `yyyyMMdd` |
| `limit` | string | - | K 线条数，默认 `20` |

**示例**：`get_security_overview(code="600519.SH")`

#### `get_fundamental` - 基本面概览

一次返回单个上市公司指定报告期的基本面卡片：市值、企业价值、EV/EBITDA、PE / PS / PB / PCF、每股营收、毛利率 / 营业利润率 / 净利率（TTM）、ROA / ROE / ROIC（TTM）、营收与归母净利同比、营业总收入、归母净利润、毛利、经营 / 投资 / 筹资 / 自由现金流、资本开支。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `600519.SH` |
| `fiscal_period` | string | - | 财年报告期，默认 `2025-FY`；如 `2026-Q1`、`2025-H1` |

**示例**：`get_fundamental(code="300750.SZ", fiscal_period="2025-FY")`

#### `get_company_profile` - 公司资料

返回公司名称、简介、主营业务与主要产品、上市日期、员工人数、管理层信息、申万行业，以及行业 / 概念 / 地域标签（含标签代码与当日涨跌幅）。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `600519.SH` |

**示例**：`get_company_profile(code="002594.SZ")`

---

### 资讯、公告与财报

#### `get_financial_news` - 热点新闻

按检索词与标的查询财经热点新闻，返回 `items[]`：`title`、`content`、`url`、`h5Url`、`publishTime`、`source`。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `query` | string | - | 检索词；不传时默认「标的名称 + 最新动态」 |
| `code` | string | - | 单个标的代码，默认 `600519.SH` |
| `start_date` | string | - | 开始日期 `yyyyMMdd` |
| `end_date` | string | - | 结束日期 `yyyyMMdd` |
| `limit` | string | - | 返回条数，默认 `14`，范围 `5`-`30`，超出按边界处理 |

**示例**：`get_financial_news(code="00700.HK", query="腾讯 AI 进展")`

#### `get_local_news` - 个股本地资讯

查询单只股票（A股 / 港股 / 美股）的资讯列表，服务端已按时间、媒体、标题过滤并去重。默认只返回标题、来源、时间与链接；`content=true` 时附带正文（耗时增加，并额外过滤模板稿和过短正文）。支持游标翻页：`hasMore=true` 时把 `nextCursor` 原样作为 `cursor` 传回，其余参数保持不变。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个股票代码，默认 `600519.SH` |
| `local_num` | string | - | 每页条数，默认 `2`，范围 `1`-`20` |
| `cursor` | string | - | 翻页游标，传上一次返回的 `nextCursor`；不传从最新一条开始 |
| `start_date` | string | - | 开始日期 `yyyyMMdd`，默认 3 个月前 |
| `end_date` | string | - | 结束日期 `yyyyMMdd`，默认今天 |
| `content` | boolean | - | 是否返回正文，默认 `false`；需要做摘要时传 `true` |

**示例**：`get_local_news(code="600519.SH", local_num="5", content=true)`

#### `get_stock_notice` - 公告列表

查询单只股票（A股 / 港股 / 美股）的公告，支持按类型筛选与分页。返回 `total`、`total_page`、`page` 与 `items[]`：`title`、`notice_type`、`publish_date`、`pdf_url`、`publisher` 等。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `600519.SH` |
| `notice_type` | string | - | 公告类型，默认 `0`；见常用枚举 |
| `page` | string | - | 页码，默认 `1` |
| `limit` | string | - | 每页条数，默认 `5`，最大 `100` |

**示例**：`get_stock_notice(code="600519.SH", notice_type="6", limit="10")`

#### `get_financial_report` - 财务报告

按股票代码、市场分页查询财务报告，返回 `items[]`：`report_id`、`stock_code`、`stock_name`、`title`、`report_type`、`abstract`（摘要）、`pdf_url`（原文 PDF）、`publish_date`（`yyyy-MM-dd`）。上游不返回总数，`has_more=true` 表示可继续翻页。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，如 `600519.SH`、`00700.HK`、`AAPL.US`；可不传 |
| `market` | string | - | `cn` / `hk` / `us`；可不传 |
| `page` | string | - | 页码，默认 `1` |
| `limit` | string | - | 每页条数，默认 `20`，最大 `100` |

**示例**：`get_financial_report(code="AAPL.US", market="us")`

#### `get_earning_call` - 业绩会资料

按单个标的代码分页查询业绩会资料，覆盖 A股 / 港股 / 美股。美股优先返回演示文稿与业绩发布资料；查不到时（以及 A股、港股）返回业绩会文字稿。返回 `page`、`limit`、`count`（本页条数）、`has_more` 与 `items[]`：`title`、`document_type`、`document_url`、`publish_time`、`stock_code`、`symbol`、`meeting_id`。

- `document_type` 为 `业绩会文字稿` 时，`meeting_id` 有值，`document_url` 是可直接打开的文字稿页面；其他资料的 `meeting_id` 为 `null`，`document_url` 为资料原文链接。
- 上游不返回总数，`has_more=true` 表示可继续翻页。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `code` | string | - | 单个标的代码，默认 `NOK.US`；如 `NVDA.US`、`00700.HK`、`000001.SZ` |
| `page` | string | - | 页码，默认 `1` |
| `limit` | string | - | 每页条数，默认 `10`，最大 `100` |

**示例**：`get_earning_call(code="00700.HK", limit="5")`

---

### 宏观

#### `get_macro_calendar` - 宏观经济日历

查询指定日期起若干天内的宏观事件（北京时间）：经济数据（公布值 / 预测值 / 前值）、央行动态、财经事件、休市提醒。返回 `start_date`、`end_date`、`total` 与 `items[]`：`date`、`weekday`、`time`、`country`、`event`、`actual`、`forecast`、`previous`、`importance`、`released`。事件过多时会截断，可缩小 `days` 或加筛选。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `start_date` | string | - | 开始日期 `yyyyMMdd`，默认今天 |
| `days` | string | - | 天数，默认 `7`，最大 `31` |
| `type` | string | - | 事件类型，默认 `1,2,3`；见常用枚举 |
| `country` | string | - | 国家/地区，逗号多选；见常用枚举 |
| `importance` | string | - | 重要性 `1`-`3`，逗号多选 |

**示例**：`get_macro_calendar(days="7", country="2", importance="3")`

#### `search_macro_indicators` - 宏观指标搜索

按模糊关键词并行搜索行业经营、全球宏观、中国宏观、中国地区宏观四类指标，按相关度重排、去重后返回 `items[]`：`indicator_name`（精确指标名）、`info_source`、`indicator_type`。用于为 `get_macro_indicator_data` 确定精确指标名。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `query` | string | ✅ | 模糊指标名，如 `CPI`、`GDP`、`制造业PMI`、`社融` |

**示例**：`search_macro_indicators(query="中国CPI同比")`

#### `get_macro_indicator_data` - 宏观指标时序

按精确指标名查询时序数据，返回 `items[]`：`indicator_name`、`info_source`、`publish_date`、`end_date`、`value`、`unit`；单次最多 100 条。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `indicator_name` | string | ✅ | 精确指标名，取自 `search_macro_indicators` 返回的 `indicator_name` |
| `indicator_type` | string | - | `1` / `2` / `3` / `4`，取自搜索结果的 `indicator_type`；传入可减少无关调用 |
| `start_date` | string | - | 开始日期 `yyyyMMdd` |
| `end_date` | string | - | 结束日期 `yyyyMMdd` |

**示例**：`get_macro_indicator_data(indicator_name="<search_macro_indicators 返回的 indicator_name>", indicator_type="3", start_date="20251001")`

---

## 典型调用链路

```text
# 「茅台近半年走势怎么样，现在估值贵不贵」
get_asset_search(query="茅台", type="stock")                         → 600519.SH
get_stock_quote(code="600519.SH", kline_type="day",
                start_date="<今天-180天>", limit="220")               → 日K + 技术指标
get_security_overview(code="600519.SH")                              → PE/PB 及 5 年分位

# 「纳斯达克100 今天分时」
get_asset_search(query="纳斯达克100", type="index")                   → .NDX.US
get_index_quote(code=".NDX.US", kline_type="m1", limit="400")        → 当日分时

# 「宁德时代基本面和公司情况」
get_fundamental(code="300750.SZ", fiscal_period="2025-FY")           → 营收/净利/ROE/现金流
get_company_profile(code="300750.SZ")                                → 简介/主营/概念标签

# 「腾讯最近有什么消息和公告」
get_local_news(code="00700.HK", local_num="5", content=true)         → 资讯与正文
get_stock_notice(code="00700.HK", limit="5")                         → 最新公告

# 「英伟达最近的业绩会」
get_asset_search(query="英伟达", type="stock")                        → NVDA.US
get_earning_call(code="NVDA.US", limit="5")                          → 演示文稿 / 业绩发布 / 文字稿链接

# 「中国 CPI 近一年」
search_macro_indicators(query="中国CPI")                              → 精确指标名 + indicator_type
get_macro_indicator_data(indicator_name="<精确指标名>",
                         indicator_type="3", start_date="<一年前>")   → 时序
```

## 响应结构

工具结果在 `result.content[0].text` 中，是一个 JSON 字符串：

```json
{ "code": "200", "msg": "success", "traceId": "4bf92f3577b34da6a3ce929d0e0e4736", "data": { } }
```

- `code` — `"200"` 为成功，读取 `data`
- `data` — 业务数据；股票 / 指数为 `items[] + technical_list[]`，盘口 / 概览 / 基本面 / 公司资料 / 基金为单个 `item`，列表类为 `items[]`（多数附带 `total`；财报与业绩会不返回总数，用 `has_more` 判断翻页）
- `traceId` — 链路 ID，反馈问题时附上

数值字段一般为**字符串**，缺失值可能是 `""`、`null` 或 `"-"`；计算或画图前需转成数字并跳过无效值。成功但无数据时返回空数组（如非交易日查分钟 K），属于正常结果。

调用失败时返回 JSON-RPC `error`：

| `error.code` | 含义 | 处理 |
|---|---|---|
| `-32003` | 当前授权未开放该工具 | 告知用户无权限，不要重试 |
| `-32029` | 超出用户调用频率或并发限制 | 稍后退避重试，不要并发叠加 |
| `-32000` | 参数错误或数据服务异常，`message` 为具体原因 | 按 `message` 修正参数；如为上游失败，如实告知用户 |

HTTP 层面：`401` 表示授权失效（需重新登录授权），`429` 表示超出用户每分钟总请求数，处理方式同 `-32029`。

出错时如实转述原因，**不要反复改参数重试到"看起来成功"，更不要凭空补数据**。

## 排错建议

| 现象 | 检查点 |
|---|---|
| 报「参数已改为 code，且仅支持单个标的代码」 | 用了 `codes` / `stock_codes` 或多代码；多标的请改用 `get_watchlist` 或逐个调用 |
| 日 K 只返回一根 | 没传 `start_date`；日 K 及以上画历史必须传 |
| 分钟 K 为空 | 分钟级只查当天，非交易日或未开盘为空；可改查日 K |
| `m60` 不生效 | 不支持 60 分钟 K，可选 `m30` 或 `m120` |
| 美股最新价为 `"-"` | 盘前当日 bar 的 `close` 为 `"-"`，取第一根有效 `close` |
| 代码查不到 / 识别错 | 先用 `get_asset_search` 确认代码；美股指数要带前导 `.`（如 `.NDX.US`） |
| 宏观指标查不到数据 | `indicator_name` 必须是 `search_macro_indicators` 返回的精确名称 |
| 资讯翻页重复或遗漏 | 翻页时 `code`、`start_date`、`end_date`、`content` 保持不变，`cursor` 原样传回 |

## 注意事项

- **单代码**：除 `get_watchlist` 外只接受单个 `code`。
- **日期一律 `yyyyMMdd`**。
- **K 线倒序**：`kline_list` 第 0 根是最新，画图前需反转为时间正序；`get_fund_quote` 的 `nav_series` 已是正序。
- **技术指标不与 K 线等长**：`technical_list` 只覆盖最近若干交易日，适合展示最新值。
- **实时轮询**：同一组参数最短每 5 秒请求一次，前一次完成后再计时，禁止并发叠加；收到 `-32029` 后退避。
- **不覆盖的品类不要硬凑**：期货、贵金属、外汇、债券、资金流、研报等不在本服务范围内。
- **代码不确定就先 `get_asset_search`**，不要凭印象拼代码。
