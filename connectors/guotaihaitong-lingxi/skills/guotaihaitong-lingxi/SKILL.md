---
name: guotaihaitong-lingxi
description: Use for China A-share/HK/US quotes, K-lines (bars), company fundamentals and financial statements, macro data, natural-language screening and backtesting, Guotai Haitong research reports, listed-company announcements, financial news, market sentiment, Lingxi anomalies/movers, equity-bond rotation signals, watchlist/monitoring management, and Guotai Haitong smart-investment (Junhong Zhitou) strategies, via the Guotai Haitong Lingxi MCP.
---

# 国泰海通灵犀 MCP 使用说明

本连接器连接国泰海通证券基于灵犀大模型提供的 MCP 服务（serverInfo: `doubao-server`，MCP 协议 2025-03-26，streamableHttp）。用户可通过自然语言获取行情、财务、选股回测、资讯、情绪异动、智投策略，并管理自选股与盯盘。

## 认证前置（重要）

- `initialize` 与 `tools/list` 可匿名，但**所有 `tools/call` 都需要登录授权**。首次调用任何工具时，WorkBuddy 会按 MCP OAuth 流程打开浏览器，由用户登录国泰海通账号并授权（scope：`mcp:read` / `mcp:write` / `offline_access`）。
- 工具返回 `401`、`Request denied by JWT Auth check. JWT verification fails` 或登录态过期提示时，**不要反复重试**，提示用户重新连接/重新授权；access_token 过期由 WorkBuddy 自动用 refresh_token 续期，对用户透明。
- `smart-invest`、`business-handle`、`margin-trading` 三个工具的 `userId` 为必填；若当前上下文无法获得用户标识，应说明并请用户补充，不要伪造。

## 选择工具的总原则

1. 先明确证券/市场、指标、报告期、时间口径；名称或代码有歧义时先向用户澄清，不得用近似证券替代。
2. 优先选择**能直接回答问题的最小只读工具**；多证券/多指标时按可用方式批量查询并保持用户给定顺序。
3. 回复中给出证券名称与代码、指标名、数值、单位、报告期或时间戳，并区分实时行情、延时行情、财报数据、计算指标与资讯，不得混为一谈。
4. 选股/回测类请求要说明所应用的条件、时间区间和未覆盖的条件。
5. 数据不可用、过期、部分缺失或前后不一致时，明确说明局限，不做无依据的推断。

## 工具能力分组

### 一、行情与 K 线
- `kline`：查询证券 K 线（Bar）。必填 `code`、`origin_date_time`、`count`、`unit`、`unit_count`、`bar_adjust_type`。
  - `code`：`SH600000`、`SZ300750`、`US.AAPL`、`HK00700`，长度须大于 2。
  - `unit`：1 分钟 / 2 小时 / 3 交易日 / 4 周 / 5 月 / 6 季 / 7 年；配合 `unit_count` 表示周期粒度。
  - `bar_adjust_type`：0 不复权 / 1 前复权 / 2 后复权。
  - `count`：向基准时间之前取的根数，**必须小于 350**。
  - `origin_date_time`：`yyyyMMddHHmmss`，留空表示从最新行情往前取。
- `marketdata-tool`：自定义榜单行情，入参 `reduced_codes`（证券代码及所需行情/产品字段 mask 的对象数组）。
- `ranklist`：按指定字段排序的证券榜单。`code`（板块/指数代码，如 `BK101003`）、`limit`、`offset`、`order_by`（0 最新价 / 2 涨跌幅 / 5 换手率 / 6 总市值 / 7 市盈率 / 8 量比 / 11 资金流 / 29 市净率等）、`sorted_type`（1 升序 / 2 降序）。

### 二、金融数据、选股与回测
- `financial_data_query`：自然语言查询股票、ETF、场外基金、指数板块及宏观数据（**不含历史回测**）。入参 `question`，仅填入确定的查询问句。
- `backtest`：对自然语言选股条件做历史回测。必填 `question`（选股条件）、`startDate`、`endDate`（`yyyyMMdd`）、`holdingPeriod`（持仓天数，默认 10）、`stockHoldCount`（持股上限，默认 10）、`dayBuyStockNum`（单日买入数，默认 5）。
- `lingxi_card_query`：入参 `query`（自然语言），返回内置数据与渲染逻辑的灵犀卡片 HTML，用于可视化展示。

### 三、资讯、研报、公告与专题
- `zixun-search`：财经新闻、市场快讯、政策动态、宏观要闻。必填 `query`、`start_date`、`end_date`（`yyyy-MM-dd`，如 `2026-10-12`；传空串表示不过滤）。
- `search-research-report`：国泰海通研究所研报（宏观策略、行业深度等），入参 `question`。
- `search-announcement`：A股上市公司公告（定期财报、分红派息、回购增持、资产重组等），入参 `query`。
- `get_hotTopic`：热点资讯专题（无入参）；专题名取 `titleName`，解读取 `ai_read` 数组元素的 `text`。

### 四、市场情绪、异动与股债风向
- `getMarketSentiment`：当前交易日最新市场情绪与情绪指标（无入参）。
- `getStockDebtDirection`：当天最新股债风向（无入参）。
- `getHistoryStockDebtDirection`：历史股债风向。`showType`（0 全部 / 3 近 3 年 / 5 近 5 年 / 10 近 10 年）、`monthAndweekFlag`（0 全部 / 1 仅每周最后一天 / 2 仅每月最后一天）。
- `getLingxiYdList`：灵犀异动列表，`start`（0 为最新，或上一页最后一条的 `time` 时间戳）、`num`。`infoSubType=7000` 为板块异动；含 `blokcode/blokname/show/rise/mark/infos` 等。
- `getLingxiYdTimeline`：灵犀异动分时图数据（无入参）。
- `get_ydRadar`：全市场异动雷达（固定 YDB 类型），`start`、`num`；`stkCode` 为小写带市场前缀，如 `sh600519`、`sz002614`；含 `changeType/msg/mark` 等。

### 五、君弘智投策略（估值 / 定投 / 策略选股）
- `query_etf_regression_valuation`：按策略编码查询指数或股票的估值数据与历史百分位。`STRATEGY_CODE`：`ZT_KJDT` 宽基定投 / `ZT_HYGZ` 行业估值 / `ZT_ETFDT` ETF 定投；`QUERY_TYPE`：`LATEST` / `PERIOD`（区间需 `BUSIN_DATE_START/END`，`yyyyMMdd`）。
- `query_etf_regression_investment`：定投策略计划目标回测（达成数、平均达成时长等）。`DT_TERM`（W 周 / DW 双周 / M 月）、`STOP_LINE`（止盈收益率，5–50）、`VALUATION_LEVEL`/`PE_VALUATION_LEVEL`/`PB_VALUATION_LEVEL`（0–9 分档）、`WITHDRAW_LEVEL`（回撤分档）、`PRODUCT_CODE` 等。
- `query_jhzt_index_funds`：按策略与指数查询关联基金列表（含基金代码、名称、收益率、规模、跟踪误差等）。`FUND_TYPE`（1 场内 / 2 场外）、`STRATEGY_CODE`、`S_IRDCODE`。
- `query_jhzt_strategy_securities`：策略入选股票列表（分页，`PAGE_INDEX`/`PAGE_SIZE`），配合 `JHZT_CODE`、`STATISTIC_PERIOD`、`TIME_PERIOD`、`TRADE_DT` 等。
- `query_jhzt_strategy_gain_distribution`：入选股票最高涨幅分布与五档百分位占比。
- `query_jhzt_strategy_history_securities`：历史止盈明细（`JHZT_CODE`、`BEGIN_TRADE_DT`、`STOP_LINE`）。
- `query_jhzt_strategy_index`：入选股票关联的核心指数。
- `query_jhzt_strategy_regression`：策略回测统计指标（最大收益、最大回撤均值等）。
- `strategiesSquare`：策略广场卡片，入参 `name` 为占位符，无需填写。
- 常用 `JHZT_CODE`：`ZT_ZNYX` 智能优选、`ZT_GZHG` 估值回归、`ZT_CYQD` 撑压强度、`ZT_JXTP` 均线突破、`ZT_GGJC` 杠杆加仓。

### 六、自选股与盯盘（用户私有数据）
- `dingPan_query`：查询用户自选/盯盘。`PAGE_NO`、`PAGE_SIZE`、`BUSIN_TYPE`（`ZXG` 自选股默认 / `DH_SM` 道合私募自选 / `DH_ZXG` 道合自选 / `LXDP` 灵犀盯盘）。
- `dingPan-join`：添加/删除自选股或盯盘（**写操作**）。
  - `ACTION_FLAG`：`00` 单条插入 / `01` 单条删除 / `10` 批量插入 / `11` 批量删除 / `20` 多分组批量插入。
  - `BATCH_DATA`：`[{GROUP_NO, MARKET_CODE, SHOW_ORDER, STOCK_CODE}]`；`ACTION_FLAG != 20` 时必传 `GROUP_NO`；`BUSIN_TYPE` 同 `dingPan_query`。

### 七、投教、业务与融资融券知识
- `smart-invest`：灵犀大模型投资答疑与投教指导，必填 `question`、`userId`。
- `business-handle`：国泰海通业务/产品/软件/活动、交易或账号操作知识、营业部网点、经纪业务常见问题，必填 `question`、`userId`。
- `margin-trading`：融资融券业务规则、标的交易参数、可融券源范围等，必填 `question`、`userId`。

### 八、客户适当性合规接口（本连接器已禁用，不可调用）
- `query_appropriateness_record`、`register_appropriateness_record` 为券商内部客户适当性留痕接口，涉及姓名、资金账号、手机号、风险等级等敏感个人信息。
- 本连接器已通过 `mcp.json` 的 `disabledTools` 将这两个工具**禁用**，它们不会出现在可用工具中，**任何情况下都不得调用**。
- 若用户提出客户适当性信息查询/留痕、协议签署记录等需求，应说明该能力不在本连接器开放范围，并引导其通过国泰海通官方 App、网上营业厅或营业部等正规渠道办理。

## 高风险/写操作确认规则

- 执行 `dingPan-join`（新增/删除自选或盯盘）前，必须先向用户展示：动作（加入/删除）、标的名称与代码、市场、分组（`BUSIN_TYPE`/`GROUP_NO`），获用户**明确确认**后才调用。
- 客户适当性留痕/查询接口（`register_appropriateness_record`、`query_appropriateness_record`）已在本连接器禁用，不得执行任何写入或查询；如用户提出相关需求，引导走国泰海通官方渠道。
- 写操作完成后，仅依据工具返回的确认结果与标识汇报，不得仅凭请求成功即声称完成；结果不确定时先查询核对，不自动重试。
- 本连接器**不提供真实证券下单/交易/撤单能力**；策略回测、入选股票、定投目标均为历史/模拟测算，不得表述为真实委托或收益承诺。

## 错误与恢复

- 工具结果 `isError:true`、HTTP/业务 `401`、`JWT verification fails`：鉴权问题，引导用户重新连接授权，不重复调用。
- 参数错误（如 `code` 格式不符、`count` 超限、日期格式错误）：根据工具描述修正参数后重试，并向用户说明所需格式。
- 超时：单次请求建议 30 秒内；超时后缩小查询范围（如缩短 K 线根数、收窄资讯日期区间）再试。
- 服务端返回可读错误时，向用户转述可读信息，不暴露内部堆栈、凭证或账户标识。

## 合规与表述边界

- 所有行情、财务、策略与回测输出仅为信息参考与投资分析，不构成个性化投资建议，不承诺收益；涉及历史回测时提示历史表现不代表未来。
- 不虚构价格、财务数值、报告期、新闻、证券代码、工具结果或自选/订单状态。
- 不得声称具备工具能力之外的市场、产品、账户或数据访问权限；模拟/回测结果须明确标注为模拟或历史测算。
- 不在回复或日志中泄露凭证、账户标识、授权数据或内部错误细节。
