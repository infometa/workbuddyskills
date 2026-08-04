---
name: comein-investment-research
description: "Use the Finenter Investment Research MCP to query institutional insights, research reports, company announcements, roadshows, market data, financial data, fund data, macroeconomic data, and quantitative data, and to access or manage the current user's authorized watchlists, documents, subscriptions, and meetings, subject to the capabilities available for each resource. It is suitable for company and industry research, event tracking, data validation, stock screening and backtesting, and personal investment research workspace operations. It covers seven categories of tools: Meeting Management, Data Analysis, Watchlist Management, Professional Investment Research Content, WeChat Official Account Management, Document Management, and Quantitative Backtesting."
description_zh: 使用进门投研 MCP 查询机构观点、研报、公告、路演、行情、财务、基金、宏观和量化数据，并管理当前用户已授权的自选股、文档、订阅与会议；适用于公司或行业研究、事件跟踪、数据验证、选股回测及个人投研工作区操作。共覆盖 7 大类工具：会议管理、数据分析、自选股管理、专业投研资料、公众号管理、文档管理、量化回测。
description_en: "Use the Finenter Investment Research MCP to query institutional insights, research reports, company announcements, roadshows, market data, financial data, fund data, macroeconomic data, and quantitative data, and to access or manage the current user's authorized watchlists, documents, subscriptions, and meetings, subject to the capabilities available for each resource. It is suitable for company and industry research, event tracking, data validation, stock screening and backtesting, and personal investment research workspace operations. It covers seven categories of tools: Meeting Management, Data Analysis, Watchlist Management, Professional Investment Research Content, WeChat Official Account Management, Document Management, and Quantitative Backtesting."
version: 1.0.0
---

# 进门投研连接器使用指南

> 连接器名称：`comein-mcp-all`（进门投研平台）
> MCP Server：`mcp-server-brm`
> SSE 地址：`https://mcp-server-global.comein.cn/mcp-servers/mcp-server-brm/sse`
> 工具前缀：`mcp__comein-mcp-all__`（实际前缀以 `tools/list` 返回为准）
> 时间格式统一：`yyyy-MM-dd HH:mm:ss`

---

> ⚠️ **MCP 工具可能随时变化（新增、改名、参数调整、废弃）。本文档的工具清单和参数仅为编写时快照，不保证与实时 MCP 一致。执行任何任务前，必须先读取当前 MCP** `tools/list`**，以实时返回的** `name`**、**`description`**、**`inputSchema` **作为唯一工具契约。** 文档中工具名和参数表仅用于路由参考和意图理解，不作为调用依据。

---

## 1. 动态工具原则

### 1.1 实时优先

- **每次执行前必须读取当前 MCP** `tools/list`，以工具实时 `description`、`inputSchema` 和返回结果作为唯一工具契约。
- 本文档第 7 节的工具清单和参数表是**编写时快照**，仅帮助理解能力范围和路由意图，不作为实际调用的参数依据。
- 如果 `tools/list` 返回的工具名、参数或返回字段与本文档不一致，**以** `tools/list` **为准**。
- 如果 MCP 新增了本文档未覆盖的工具，根据 `description` 判断是否匹配任务，直接使用。
- 如果本文档记录的工具在 `tools/list` 中已消失或改名，根据 `description` 重新匹配同类能力；无法匹配时告知用户当前可用工具范围。



### 1.2 调用原则

- 根据任务所需能力选择最匹配的专用工具或工具组合，不依赖固定工具名、工具数量、参数或返回字段。
- 使用综合检索能力获取全貌或补充召回；涉及行情、财务、基金、宏观等结构化事实时，优先选择对应专用能力。
- 直接使用 MCP 返回的标准工具名，不添加客户端私有前缀，不传入实时 Schema 未声明的参数。
- 文档中的枚举值（如 recordStatus、reportType 等）如有变化，以 `tools/list` 的 `inputSchema` 中的 `enum` 或 `description` 为准。

---



## 2. 认证与权限

- 首次连接时，由 WorkBuddy 打开浏览器完成进门 OAuth 授权，仅使用当前账号已有权限。
- Access Token 过期时由 WorkBuddy 自动刷新；收到 401 或授权失效时，引导用户重新连接。
- 收到 403 或业务权限不足时，说明受限范围，并提示联系所属机构管理员或进门服务人员开通后重试。
- 不读取、记录或输出 Token、Cookie、用户身份、机构权限、会议密码或主持人密钥。

---



## 3. 能力路由与调用原则


| 任务类型         | 选择原则                                                                                                                                                                                                                                          | 结果要求或操作边界                           |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| 公司、行业和事件研究   | 先获取机构观点（`research_query` / `searchDomesticReports` / `searchForeignReports`），再按缺口补充公告（`searchAnnouncementReport`）、点评（`searchAnalystComments`）、路演纪要（`searchRoadshowSummary`）                                                                   | 区分公司披露事实、机构观点和 AI 归纳，注明来源类型与绝对时间范围  |
| 热门内容、路演和调研活动 | 热度排行用 `research_hot_data_query` / `search_popular_roadshow`；活动排期用 `meeting_activity_list` / `research_activity_list` / `strategy_list`                                                                                                        | 标明排序口径、时间窗口和主体，不把热度直接等同于投资价值        |
| 行情、指数和公司数据   | 实时行情用 `pricePerformance`；指数行情用 `searchIndexQuotation`（4 种模式）；公司基础信息用 `get_stock_details`                                                                                                                                                      | 标明交易时点、市场、代码、周期、复权和币种口径             |
| 财务和盈利预测      | 财务报表用 `company_finance_search`；主营拆分用 `get_main_business_segments`；盈利预测用 `getStockProfitForecast`；报告期查询用 `company_report_date_search`                                                                                                          | 标明报告期、单季/累计、预测年度和数据来源               |
| 基金研究         | 基金持仓与暴露用 `get_fund_holdings`                                                                                                                                                                                                                  | 区分基金主体与份额，标明披露期和观察日                 |
| 宏观和期货研究      | 宏观指标先 `indicatorNameRetrieve` 找指标 → `indicatorInfoRetrieve` 看采集信息 → `indicatorDataRetrieve` 取数值；期货用 `futures_contracts`（合约信息）/ `futures_kline`（K线）/ `futures_price`（实时报价）                                                                     | 标明国家、频率、单位、合约和时间范围                  |
| 选股、技术分析和回测   | 选股用 `screenerStock`（一次性传入全部条件）；回测用 `backtest_submit` → `backtest_tasks_status` 轮询 → `backtest_task_list` 查记录                                                                                                                                  | 保留条件、区间、基准、任务状态和风险指标，不承诺未来收益        |
| 自选股管理        | 查列表用 `watchlist_stock_list`；分组管理用 `stock_group_list` / `create_portfolio_group` / `add_stocks_to_portfolio_group` / `rename_portfolio_group`                                                                                                  | 仅操作当前账号的自选股，分组名需唯一                  |
| 公众号、会议和代录    | 公众号列表用 `official_account_subscription_list`；群消息用 `wechat_opinion_list`；公众号文章用 `wechat_article_query`；代录用 `meeting_recording_submit` / `meeting_recording_list` / `meeting_recording_delete`；自助会议用 `self_meeting_create` / `self_meeting_list` | 写操作必须来自用户明确请求；创建前确认对象和时间，删除前核对唯一 ID |
| 文档管理         | 访问用 `document_access`；搜索列表用 `document_search`；内容检索用 `searchMyKnowledge` / `searchMySummary` / `searchMyDoc`；上传用 `document_upload`                                                                                                             | 仅操作当前账号有权访问的内容，个人资料结果不扩大解释为公共数据     |


---



## 4. 推荐工作流

1. 确认用户目标、主体、市场、时间范围及必要口径；只有缺少的信息会实质改变结果时才追问一个关键条件。
2. 读取当前工具清单和 Schema，选择任务匹配度最高的能力。
3. 先获取事实或原始观点，再根据任务需要进行跨来源、跨口径验证。
4. 需要解释数据变化时，将结构化数据与机构观点结合，但分开呈现证据和推断。
5. 输出时注明主体、绝对日期、数据或来源类型、关键口径及未验证项。



### 典型场景


| 场景                   | 工具链                                                                                           |
| -------------------- | --------------------------------------------------------------------------------------------- |
| "查宁德时代最近四个报告期核心财务数据" | `company_report_date_search`（取报告期）→ `company_finance_search`（取财务数据）                           |
| "帮我选 A 股低估值高股息的股票"   | `screenerStock`（一次性传入 PE + 股息率 + 市场条件）                                                        |
| "查 CPI 最新数据"         | `indicatorNameRetrieve`（找指标 ID）→ `indicatorInfoRetrieve`（看采集信息）→ `indicatorDataRetrieve`（取数值） |
| "帮我回测一个低估值策略"        | `backtest_submit`（提交）→ `backtest_tasks_status`（轮询状态）→ 完成后查看结果                                 |
| "建一个 AI 概念分组并加几只股票"  | `create_portfolio_group`（建分组）→ `add_stocks_to_portfolio_group`（加股票）                           |
| "帮我提交一个代录"           | `meeting_recording_submit`（传会议信息文本）→ `meeting_recording_list`（确认状态）                           |
| "搜光伏行业研报"            | `searchDomesticReports`（内资研报）/ `searchForeignReports`（外资研报，推荐英文 query）                        |
| "看看这周有什么热门路演"        | `search_popular_roadshow`（按热度排序）或 `meeting_activity_list`（按时间排期）                              |


---



## 5. 写操作与异步任务

- 查询类操作可直接执行；创建、上传、订阅、添加、重命名、提交和删除等写操作必须来自用户明确请求。
- 批量写入前展示对象和数量；删除前回读目标名称、唯一 ID 和归属范围并再次确认。
- 写入后使用当前可用的查询或访问能力回读；未获得成功响应时不得宣称完成。
- 异步任务只提交一次，保留任务 ID，并通过当前匹配的状态或结果能力查询；超时只报告当前状态，不重复创建任务。
- 部分成功时分别列出成功、跳过和失败项，不把整批操作标记为完成。

---



## 6. 错误、降级与内容边界

- 区分未连接、未授权、权限不足、参数错误、空结果和工具限制，分别给出可执行的下一步。
- 实体命中多个候选时先消歧；结果为空时检查主体、市场、代码、时间、报告期和披露滞后，再决定是否调整范围。
- 专用能力不可用时，可使用当前综合能力降级检索，但不得伪造缺失字段、数据口径或成功状态。
- 不将"无结果"直接解释为"不存在"，不将单次工具缺失表述为平台永久不支持。
- 不在上架文案或输出中宣称提供"非公开信息"；仅描述用户当前权限范围内可访问的投研内容。

---



## 7. 工具清单与参数详解

> ⚠️ **以下为编写时快照，仅供路由参考和意图理解。MCP 工具可能已变化（新增/改名/参数调整/废弃）。实际调用前务必读取** `tools/list`**，以实时 Schema 为准。**
>
> 当发现以下情况时，以 `tools/list` 为准：
>
> - 工具名不一致 → 按 `description` 重新匹配
> - 参数名/类型/必填变化 → 按 `inputSchema` 调用
> - 枚举值变化 → 按 `inputSchema` 中的 `enum` 调用
> - 工具被废弃 → 用 `description` 匹配替代能力
> - 出现新工具 → 按 `description` 判断是否适用当前任务



### 7.1 会议管理（8 个工具）



#### meeting_recording_submit — 提交代录信息


| 参数            | 类型     | 必填  | 说明              |
| ------------- | ------ | --- | --------------- |
| `meetingInfo` | string | ✅   | 会议信息文本，从当前会话中提取 |


```json
{"meetingInfo": "腾讯会议 123-456-789，主题：2026Q2新能源行业展望，时间：2026-08-05 14:00:00"}
```



#### meeting_recording_list — 查询代录列表


| 参数             | 类型      | 必填  | 默认  | 说明                                    |
| -------------- | ------- | --- | --- | ------------------------------------- |
| `stime`        | string  | ❌   | —   | 会议开始时间（起）                             |
| `etime`        | string  | ❌   | —   | 会议结束时间（止）                             |
| `recordStatus` | string  | ❌   | —   | 状态（逗号分隔）：1待审核 2进行中 3已完成 4录会失败         |
| `recordType`   | string  | ❌   | —   | 类型（逗号分隔）：1腾讯会议 2进门路演 3zoom 4电话会议 -1未知 |
| `recordSource` | string  | ❌   | —   | 来源（逗号分隔）：0单独会话 1群聊 2APP 3BRM          |
| `keyword`      | string  | ❌   | —   | 关键词模糊搜索                               |
| `page`         | integer | ❌   | 1   | 页码                                    |
| `size`         | integer | ❌   | 10  | 每页条数                                  |




#### meeting_recording_delete — 删除代录信息


| 参数                   | 类型      | 必填  | 说明                                   |
| -------------------- | ------- | --- | ------------------------------------ |
| `meetingRecordingId` | integer | ✅   | 代录 ID，通过 `meeting_recording_list` 获取 |




#### self_meeting_create — 创建预约会议


| 参数                   | 类型       | 必填  | 默认  | 说明                      |
| -------------------- | -------- | --- | --- | ----------------------- |
| `subject`            | string   | ✅   | —   | 会议主题                    |
| `stime`              | string   | ✅   | —   | 开始时间                    |
| `etime`              | string   | ✅   | —   | 结束时间                    |
| `conferenceTypeDesc` | string   | ❌   | —   | 沟通类型描述                  |
| `needPassword`       | integer  | ❌   | 0   | 是否需要密码：0否 1是            |
| `password`           | string   | ❌   | —   | 参会密码（needPassword=1 时填） |
| `enableHostKey`      | integer  | ❌   | 0   | 主持人密钥：0关 1开             |
| `hostKey`            | string   | ❌   | —   | 主持人密钥，仅6位数字             |
| `needRegister`       | integer  | ❌   | 0   | 是否需要报名：0否 1是            |
| `commitment`         | integer  | ❌   | 0   | 是否需要承诺书：0否 1是           |
| `receptionists`      | string[] | ❌   | —   | 接待人姓名列表                 |




#### self_meeting_list — 查询自助会议列表


| 参数                | 类型      | 必填  | 默认  | 说明                       |
| ----------------- | ------- | --- | --- | ------------------------ |
| `key`             | string  | ❌   | —   | 关键词模糊搜索                  |
| `subject`         | string  | ❌   | —   | 会议标题                     |
| `meetingCode`     | string  | ❌   | —   | 腾讯会议号                    |
| `sponsor`         | string  | ❌   | —   | 发起人                      |
| `stime` / `etime` | string  | ❌   | —   | 开始/结束时间范围                |
| `status`          | integer | ❌   | —   | 1待开始 2进行中 3已结束 4已取消 5其他  |
| `typeForUser`     | string  | ❌   | —   | `generic`常规 `webinar`研讨会 |
| `page`            | integer | ❌   | 1   | 页码                       |
| `size`            | integer | ❌   | 10  | 每页条数                     |




#### meeting_activity_list — 查询进门路演列表

> ⚠️ 时间限制：开始时间不能早于三天前，结束时间不能晚于三天后。


| 参数           | 类型      | 必填  | 默认  | 说明                              |
| ------------ | ------- | --- | --- | ------------------------------- |
| `startTime`  | string  | ❌   | —   | 开始时间（不能早于三天前）                   |
| `endTime`    | string  | ❌   | —   | 结束时间（不能晚于三天后）                   |
| `stockCodes` | string  | ❌   | —   | 股票代码，逗号分隔，如 `sz300750,sh600519` |
| `page`       | integer | ❌   | 1   | 页码                              |
| `size`       | integer | ❌   | 10  | 每页条数                            |




#### research_activity_list — 查询调研活动列表


| 参数                      | 类型      | 必填  | 默认  | 说明                  |
| ----------------------- | ------- | --- | --- | ------------------- |
| `companyKeyword`        | string  | ❌   | —   | 调研公司关键词             |
| `fullCode`              | string  | ❌   | —   | 完整股票代码，如 `sz300750` |
| `startTime` / `endTime` | string  | ❌   | —   | 时间范围                |
| `page`                  | integer | ❌   | 1   | 页码                  |
| `size`                  | integer | ❌   | 10  | 每页条数                |




#### strategy_list — 查询策略列表


| 参数                      | 类型      | 必填  | 默认  | 说明     |
| ----------------------- | ------- | --- | --- | ------ |
| `title`                 | string  | ❌   | —   | 标题     |
| `fullCode`              | string  | ❌   | —   | 完整股票代码 |
| `regionList`            | string  | ❌   | —   | 地区     |
| `sponsorName`           | string  | ❌   | —   | 举办方名称  |
| `startTime` / `endTime` | string  | ❌   | —   | 时间范围   |
| `page`                  | integer | ❌   | 1   | 页码     |
| `size`                  | integer | ❌   | 10  | 每页条数   |


---



### 7.2 数据分析（15 个工具）



#### company_finance_search — 查询财务报表数据


| 参数              | 类型       | 必填  | 说明                                                               |
| --------------- | -------- | --- | ---------------------------------------------------------------- |
| `querys`        | string[] | ✅   | 公司查询词列表（名称或代码），单次最多 20 个                                         |
| `reportDates`   | object[] | ✅   | 报告期，含 `fiscalYear`/`reportType`(Q1/S1/Q3/A)/`type`(quarter/year) |
| `searchData`    | string[] | ✅   | 数据指标，如"营业总收入"、"净利润"、"归母净利润"、"毛利率"、"ROE"                          |
| `statementType` | string[] | ❌   | 数据源：IS利润表 / BS资产负债表 / CF现金流量表 / indicators财务指标                   |


```json
{
  "querys": ["贵州茅台", "五粮液"],
  "reportDates": [{"fiscalYear": 2024, "reportType": "A", "type": "year"}],
  "searchData": ["营业总收入", "净利润", "归母净利润", "毛利率", "净资产收益率(ROE)"]
}
```



#### get_main_business_segments — 查询主营分拆数据

> ⚠️ 主营拆分数据一般在年报和半年报披露。


| 参数             | 类型       | 必填  | 说明                                                     |
| -------------- | -------- | --- | ------------------------------------------------------ |
| `companyInfos` | object[] | ✅   | 含 `fullCode`（如 `sh600519`），必须完整代码                      |
| `reportDates`  | object[] | ✅   | 含 `fiscalYear`/`reportType`(S1/A)/`type`(quarter/year) |
| `searchData`   | string[] | ✅   | 仅支持：营业收入、营业成本、毛利润、毛利率、成本同比、收入同比                        |
| `itemClassify` | string[] | ✅   | 拆解维度：按产品 / 按行业 / 按地区                                   |




#### getStockProfitForecast — 查询盈利预测


| 参数              | 类型        | 必填  | 默认      | 说明                  |
| --------------- | --------- | --- | ------- | ------------------- |
| `queries`       | string[]  | ✅   | —       | 股票名称或代码，不建议超过 20 个  |
| `forecastYears` | integer[] | ❌   | []      | 预测年度，如 [2026, 2027] |
| `from` / `to`   | string    | ❌   | 3个月前/今日 | 日期范围                |
| `page`          | integer   | ❌   | 1       | 页码                  |
| `size`          | integer   | ❌   | 20      | 每页条数                |




#### indicatorNameRetrieve — 检索宏观指标


| 参数          | 类型       | 必填  | 默认            | 说明                                           |
| ----------- | -------- | --- | ------------- | -------------------------------------------- |
| `queries`   | string[] | ❌   | —             | 关键词，如 ["CPI"] / ["PMI","社会融资"]               |
| `country`   | string   | ❌   | —             | 中国/美国/日本/欧元区                                 |
| `category`  | string   | ❌   | —             | 九分类（见枚举速查）                                   |
| `frequency` | string   | ❌   | —             | 季/年/月/不定期/日/周/旬/两周                           |
| `page`      | integer  | ❌   | 1             | 页码                                           |
| `size`      | integer  | ❌   | 10            | 每页条数                                         |
| `sort_by`   | string   | ❌   | headline_rank | 排序：headline_rank/latest_period/name/category |




#### indicatorInfoRetrieve — 查询指标采集信息


| 参数            | 类型     | 必填  | 说明                                |
| ------------- | ------ | --- | --------------------------------- |
| `indicatorId` | string | ✅   | 指标 ID（来自 `indicatorNameRetrieve`） |




#### indicatorDataRetrieve — 查询指标数值时序


| 参数                        | 类型      | 必填  | 默认     | 说明                                   |
| ------------------------- | ------- | --- | ------ | ------------------------------------ |
| `indicator_id`            | integer | ❌   | —      | 指标 ID（首选，精确主键），与 query 二选一           |
| `query`                   | string  | ❌   | —      | 关键词（传 query 时 category 和 country 必填） |
| `country`                 | string  | ❌   | —      | 国家/地区（传 query 时必填）                   |
| `category`                | string  | ❌   | —      | 九分类（传 query 时必填）                     |
| `frequency`               | string  | ❌   | —      | 频度过滤                                 |
| `start_date` / `end_date` | string  | ❌   | 近3年/今日 | 日期范围 YYYY-MM-DD                      |
| `latest_only`             | boolean | ❌   | false  | 仅返回最新一期                              |
| `page`                    | integer | ❌   | 1      | 页码                                   |
| `size`                    | integer | ❌   | 100    | 每页条数                                 |




#### futures_contracts — 查询期货合约信息


| 参数       | 类型     | 必填  | 说明                                                  |
| -------- | ------ | --- | --------------------------------------------------- |
| `market` | string | ✅   | `internal`内盘 / `external`外盘                         |
| `symbol` | string | ✅   | 品种代码。主力末尾加"0"：SC0=原油主力、RB0=螺纹钢主力；具体月份：SC2407、RB2501 |




#### futures_kline — 查询期货 K 线


| 参数       | 类型      | 必填  | 默认  | 说明                                   |
| -------- | ------- | --- | --- | ------------------------------------ |
| `market` | string  | ✅   | —   | `internal` / `external`              |
| `symbol` | string  | ✅   | —   | 合约代码。内盘主力加"0"（RB0）；外盘传品种代码（CL=WTI原油） |
| `type`   | string  | ✅   | 0   | K线类型：0日K, 1/5/30/60/120/240分钟K       |
| `limit`  | integer | ❌   | 100 | 返回条数，建议不超过 500                       |




#### futures_price — 查询期货实时报价

> ⚠️ symbol 传**具体月份合约代码**（非主力品种代码），多个逗号分隔。


| 参数       | 类型     | 必填  | 说明                                      |
| -------- | ------ | --- | --------------------------------------- |
| `market` | string | ✅   | `internal` / `external`                 |
| `symbol` | string | ✅   | 具体合约代码，如 `rb2501,i2505,cu2503`（不要传 RB0） |




#### searchIndexQuotation — 指数数据统一查询

四种模式：


| 模式           | 说明                                | queries 要求   |
| ------------ | --------------------------------- | ------------ |
| `snapshot`   | 最新截面快照：基础信息+行情+多区间涨跌+PE/PB估值及历史分位 | 必填，支持多指数     |
| `timeseries` | 日度历史时序：收盘价、涨跌幅、估值按日展开             | 必填，仅 1 个指数   |
| `kline`      | K线：日/周/月/季/年周期的开高低收、成交量额          | 必填，仅 1 个指数   |
| `realtime`   | 盘中实时行情快照                          | 可不传，返回常用指数看板 |



| 参数                        | 类型       | 必填  | 默认       | 说明                         |
| ------------------------- | -------- | --- | -------- | -------------------------- |
| `mode`                    | string   | ❌   | snapshot | 查询模式                       |
| `queries`                 | string[] | ❌   | —        | 指数查询词（名称或代码）               |
| `start_date` / `end_date` | string   | ❌   | 视模式/今日   | 日期范围 YYYY-MM-DD            |
| `period_type`             | string   | ❌   | D        | K线周期（仅 kline 模式）：D/W/M/Q/Y |
| `limit`                   | integer  | ❌   | —        | 返回行数上限                     |
| `market_name`             | string   | ❌   | —        | 市场过滤：A股/港股/美股              |
| `index_type_name`         | string   | ❌   | —        | 指数类别过滤                     |




#### screenerStock — 多条件组合选股

> ⚠️ **务必一次性传入全部筛选条件，禁止分步迭代查询。** 用户无明确市场要求时，默认 marketType 为 sh/sz/bj（即 A 股）。


| 参数                 | 类型       | 必填  | 说明                                 |
| ------------------ | -------- | --- | ---------------------------------- |
| `page`             | integer  | ✅   | 页码，默认 1                            |
| `size`             | integer  | ✅   | 每页条数，默认 20，不建议超过 100               |
| `sort`             | object[] | ✅   | 排序规则，含 `field` + `order`(asc/desc) |
| `numberConditions` | object[] | ❌   | 数值筛选条件                             |
| `enumConditions`   | object[] | ❌   | 枚举筛选条件                             |


**数值筛选可用字段**：`changePct`(涨跌幅) `marketCap`(总市值) `turnoverRate`(换手率) `latestPrice`(最新价) `turnoverVolume`(成交量) `turnoverValue`(成交额) `lyrPe`(静态PE) `ttmPe`(滚动PE) `pb`(市净率) `ttmDividendRatio`(滚动股息率) `changePctWeek/Month/ThreeMonth/SixMonth/Ytd`(多周期涨跌幅)

**枚举筛选可用字段**：`concept`(股票概念，如"高股息"、"半导体") `marketType`(sh/sz/bj/hk/us)

```json
{
  "page": 1, "size": 20,
  "sort": [{"field": "marketCap", "order": "desc"}],
  "numberConditions": [
    {"key": "ttmPe", "range": {"gte": 0, "lte": 30}},
    {"key": "ttmDividendRatio", "range": {"gte": 3}}
  ],
  "enumConditions": [
    {"key": "marketType", "values": ["sh", "sz"]},
    {"key": "concept", "values": ["高股息"]}
  ]
}
```



#### get_fund_holdings — 查询基金持仓与暴露


| 参数            | 类型       | 必填  | 默认               | 说明                                                                |
| ------------- | -------- | --- | ---------------- | ----------------------------------------------------------------- |
| `query_text`  | string   | ✅   | —                | 基金名称、份额名称或交易代码                                                    |
| `sections`    | string[] | ❌   | ["top_holdings"] | top_holdings/asset_allocation/industry_exposure/concentration/all |
| `report_date` | string   | ❌   | 最近一期             | 报告期 yyyy-MM-dd                                                    |
| `top_n`       | integer  | ❌   | 10               | 返回前 N 大重仓，1-10                                                    |




#### get_stock_details — 批量查询公司基本信息


| 参数        | 类型       | 必填  | 说明                                                                                        |
| --------- | -------- | --- | ----------------------------------------------------------------------------------------- |
| `queries` | string[] | ✅   | 股票名称或代码，最多 10 个                                                                           |
| `include` | string[] | ❌   | 返回模块（不传默认4个）：standardized_info/market_value/industry_concepts/business_profile/management |




#### pricePerformance — 批量查询股票行情与表现


| 参数        | 类型       | 必填  | 说明                                                                                                                              |
| --------- | -------- | --- | ------------------------------------------------------------------------------------------------------------------------------- |
| `queries` | string[] | ✅   | 股票代码或名称，最多 10 个                                                                                                                 |
| `include` | string[] | ❌   | 返回模块（不传默认3个）：standardized_info/regular_market/pre_market/post_market/period_change/valuation/market_value/price_boundary/margin |




#### company_report_date_search — 查询最新报告期

> ⚠️ 仅支持 A 股，不支持港股、美股。


| 参数             | 类型       | 必填  | 说明                                |
| -------------- | -------- | --- | --------------------------------- |
| `companyInfos` | object[] | ✅   | 含 `fullCode`（如 `sh600519`），必须完整代码 |


---



### 7.3 自选股管理（5 个工具）



#### watchlist_stock_list — 查询自选股列表


| 参数        | 类型      | 必填  | 默认  | 说明                                           |
| --------- | ------- | --- | --- | -------------------------------------------- |
| `groupId` | integer | ❌   | -1  | 分组 ID。-1=全部股票。其他 ID 通过 `stock_group_list` 获取 |
| `page`    | integer | ❌   | 1   | 页码                                           |
| `size`    | integer | ❌   | 50  | 每页条数                                         |




#### stock_group_list — 查询自选分组列表

无参数。

#### create_portfolio_group — 创建自选股分组

> ⚠️ 分组名称不能为空，且需在该用户下唯一。


| 参数          | 类型     | 必填  | 说明   |
| ----------- | ------ | --- | ---- |
| `groupName` | string | ✅   | 分组名称 |




#### add_stocks_to_portfolio_group — 向分组添加股票

> 💡 如果用户尚未创建该分组，请先调用 `create_portfolio_group` 或 `stock_group_list` 确认分组信息。


| 参数            | 类型       | 必填  | 说明                         |
| ------------- | -------- | --- | -------------------------- |
| `stockNames`  | string[] | ✅   | 股票列表，支持名称或代码               |
| `groupId`     | integer  | ❌   | 分组 ID（与 groupName 二选一）     |
| `groupName`   | string   | ❌   | 分组名称（与 groupId 二选一）        |
| `marketTypes` | string[] | ❌   | 市场过滤：sh/sz/bj/hk/us，不传默认全部 |




#### rename_portfolio_group — 重命名自选分组

> ⚠️ 原名称与新名称均不能为空。


| 参数        | 类型     | 必填  | 说明    |
| --------- | ------ | --- | ----- |
| `oldName` | string | ✅   | 原分组名称 |
| `newName` | string | ✅   | 新分组名称 |


---



### 7.4 专业投研资料（8 个工具）



#### research_hot_data_query — 查询投研热门数据

> ⚠️ startTime 和 endTime 时间间隔不能超过 90 天。


| 参数            | 类型      | 必填  | 说明                                                         |
| ------------- | ------- | --- | ---------------------------------------------------------- |
| `contentType` | string  | ✅   | `minutes`纪要 / `domestic`内资研报 / `oversea`外资研报 / `comment`点评 |
| `startTime`   | string  | ✅   | 开始时间                                                       |
| `endTime`     | string  | ✅   | 结束时间                                                       |
| `page`        | integer | ❌   | 页码，默认 1。page × pageSize 不能超过 10000                         |
| `pageSize`    | integer | ❌   | 每页条数，默认 10，最大 50                                           |




#### search_popular_roadshow — 查询热门路演


| 参数                 | 类型      | 必填  | 说明                    |
| ------------------ | ------- | --- | --------------------- |
| `popularStartTime` | string  | ✅   | 热度统计窗口开始时间            |
| `popularEndTime`   | string  | ✅   | 热度统计窗口结束时间            |
| `industryName`     | string  | ❌   | 申万一级行业名称，如"医药生物"、"电子" |
| `popularTopN`      | integer | ❌   | 最多返回条数，最大 25          |




#### searchDomesticReports — 搜索内资研报

> 💡 后端为向量数据库，请使用完整的自然语言问题，明确公司名称、行业主题、事件背景。


| 参数            | 类型      | 必填  | 说明                           |
| ------------- | ------- | --- | ---------------------------- |
| `query`       | string  | ✅   | 完整中文自然语言问题                   |
| `filterImage` | boolean | ✅   | 是否过滤图片类型数据，MCP 默认传 true      |
| `start_time`  | string  | ❌   | 开始日期 YYYY-MM-DD（动态时间窗口规则见下方） |
| `topK`        | integer | ❌   | 返回数量上限，1-50                  |




#### searchForeignReports — 搜索外资研报

> 💡 推荐使用英文描述检索意图。


| 参数            | 类型      | 必填  | 说明                  |
| ------------- | ------- | --- | ------------------- |
| `query`       | string  | ✅   | 英文自然语言描述            |
| `filterImage` | boolean | ✅   | 是否过滤图片，MCP 默认传 true |
| `start_time`  | string  | ❌   | 开始日期 YYYY-MM-DD     |
| `topK`        | integer | ❌   | 返回数量上限，1-50         |




#### searchRoadshowSummary — 搜索路演纪要


| 参数           | 类型      | 必填  | 说明                         |
| ------------ | ------- | --- | -------------------------- |
| `query`      | string  | ✅   | 完整中文自然语言，描述纪要内容、发言人、关心的问题点 |
| `start_time` | string  | ❌   | 开始日期 YYYY-MM-DD            |
| `topK`       | integer | ❌   | 返回数量上限，1-50                |


> 💡 如果用户输入的是股票代码，需补充公司简称一起搜索。



#### searchAnnouncementReport — 搜索上市公司公告

> ⚠️ 公司名称通过 fullCode 指定，禁止在 query 中罗列公司名称。


| 参数          | 类型      | 必填  | 说明                             |
| ----------- | ------- | --- | ------------------------------ |
| `query`     | string  | ✅   | 公告要点描述，支持多个子问题用空格分隔，每条 15~20 字 |
| `fullCode`  | string  | ❌   | 股票代码，多个逗号分隔                    |
| `labelList` | string  | ❌   | 公告业绩期间，如"2024A,2025Q1"         |
| `topK`      | integer | ❌   | 返回数量上限，1-50                    |




#### searchAnalystComments — 搜索分析师点评


| 参数           | 类型      | 必填  | 说明                 |
| ------------ | ------- | --- | ------------------ |
| `query`      | string  | ✅   | 完整中文自然语言问题，明确公司、事件 |
| `start_time` | string  | ❌   | 开始日期 YYYY-MM-DD    |
| `topK`       | integer | ❌   | 返回数量上限，1-50        |




#### research_query — 投研数据综合查询


| 参数                      | 类型      | 必填  | 默认       | 说明                                                                    |
| ----------------------- | ------- | --- | -------- | --------------------------------------------------------------------- |
| `type`                  | string  | ✅   | —        | domestic/oversea/minutes/comment/announcement/eventSignal/dailyReport |
| `keywords`              | string  | ❌   | —        | 关键词模糊匹配                                                               |
| `stockCode`             | string  | ❌   | —        | 股票代码/ticker                                                           |
| `market`                | string  | ❌   | —        | sz/sh/bj/hk/us（与 stockCode 配合时填纯代码）                                   |
| `industryName`          | string  | ❌   | —        | 申万一级行业名称，不带"行业"后缀                                                     |
| `groupIds`              | string  | ❌   | —        | 自选分组 ID，"-1"为全部                                                       |
| `startTime` / `endTime` | string  | ❌   | 最近30天/当前 | 时间范围                                                                  |
| `page`                  | integer | ❌   | 1        | 页码                                                                    |
| `pageSize`              | integer | ❌   | 20       | 每页条数，最大 100                                                           |
| `divergenceLevel`       | string  | ❌   | low      | 关键词发散等级：low/medium/high                                               |
| `region`                | string  | ❌   | —        | 研报标的地区（仅 type=oversea 生效）                                             |
| `reportDayTime`         | integer | ❌   | —        | 内参时段：0早参 1午评 2夜读                                                      |




#### 研报搜索动态时间窗口规则

> 适用于 searchDomesticReports / searchForeignReports / searchRoadshowSummary / searchAnalystComments 的 `start_time`。


| 场景         | 关键词          | 时间窗口       |
| ---------- | ------------ | ---------- |
| 估值/买入/最新观点 | 还能买吗/目标价/性价比 | 当前日期 - 3个月 |
| 突发事件/短期点评  | 大跌/异动/点评/为何  | 当前日期 - 1个月 |
| 财务/排名/数据查询 | 年报/业绩/占比/Top | 当前日期 - 1年  |
| 深度复盘/行业演变  | 壁垒/十年复盘/技术路线 | 当前日期 - 3年  |


用户明确提到"今天"、"本周"、"本月"、"本季度"时，锚定到精确日期（优先于动态窗口）。

---



### 7.5 公众号管理（3 个工具）



#### official_account_subscription_list — 查询公众号订阅列表


| 参数         | 类型      | 必填  | 默认  | 说明   |
| ---------- | ------- | --- | --- | ---- |
| `page`     | integer | ❌   | 1   | 页码   |
| `pageSize` | integer | ❌   | 10  | 每页条数 |




#### wechat_opinion_list — 查询微信群消息


| 参数                                    | 类型        | 必填  | 默认  | 说明                  |
| ------------------------------------- | --------- | --- | --- | ------------------- |
| `keyword`                             | string    | ❌   | —   | 关键词搜索（匹配标题和描述）      |
| `stockCodes`                          | string    | ❌   | —   | 股票代码，逗号分隔           |
| `startTime` / `endTime`               | string    | ❌   | —   | 时间范围                |
| `releaseStartTime` / `releaseEndTime` | string    | ❌   | —   | 消息发送时间范围            |
| `type`                                | integer[] | ❌   | —   | 1活动 2纪要 3报告         |
| `firstType`                           | string    | ❌   | —   | 一级分类，如"会议"、"路演会议"   |
| `subCategory`                         | string    | ❌   | —   | 二级分类，如"宏观研究"、"业绩点评" |
| `province` / `city`                   | string[]  | ❌   | —   | 省份/城市列表             |
| `page`                                | integer   | ❌   | 1   | 页码                  |
| `size`                                | integer   | ❌   | 10  | 每页条数                |




#### wechat_article_query — 查询公众号文章


| 参数                      | 类型      | 必填  | 默认      | 说明                                        |
| ----------------------- | ------- | --- | ------- | ----------------------------------------- |
| `wechatArticleScope`    | string  | ✅   | —       | `all`全部 / `subscribed`我的订阅 / `featured`精选 |
| `keywords`              | string  | ❌   | —       | 关键词（匹配标题、正文、公众号名、行业、个股）                   |
| `accountName`           | string  | ❌   | —       | 公众号名称，支持模糊匹配                              |
| `fullCode`              | string  | ❌   | —       | 股票代码，逗号分隔                                 |
| `stockNames`            | string  | ❌   | —       | 股票名称，逗号分隔                                 |
| `industryName`          | string  | ❌   | —       | 申万一级行业名称                                  |
| `startTime` / `endTime` | string  | ❌   | 最近7天/今日 | 时间范围                                      |
| `page`                  | integer | ❌   | 1       | 页码                                        |
| `pageSize`              | integer | ❌   | 10      | 每页条数，最大 100                               |


---



### 7.6 文档管理（6 个工具）



#### document_access — 访问文档内容


| 参数           | 类型     | 必填  | 说明    |
| ------------ | ------ | --- | ----- |
| `documentId` | string | ✅   | 文件 ID |




#### document_search — 搜索云文档列表


| 参数                      | 类型        | 必填  | 默认  | 说明             |
| ----------------------- | --------- | --- | --- | -------------- |
| `keyword`               | string    | ❌   | —   | 文档标题关键字，模糊搜索   |
| `type`                  | integer   | ❌   | —   | 条目类型：1文件夹 2文件  |
| `fileType`              | integer   | ❌   | —   | 文件类型（见枚举速查）    |
| `sourceList`            | integer[] | ❌   | —   | 来源类型列表（见枚举速查）  |
| `startTime` / `endTime` | string    | ❌   | —   | 筛选时间范围（基于修改时间） |
| `parentId`              | integer   | ❌   | —   | 父级文件夹 ID       |
| `page`                  | integer   | ❌   | 1   | 页码             |
| `size`                  | integer   | ❌   | 10  | 每页条数           |




#### searchMyKnowledge — 检索个人共享知识库


| 参数      | 类型     | 必填  | 说明          |
| ------- | ------ | --- | ----------- |
| `query` | string | ✅   | 完整的中文自然语言问题 |




#### searchMySummary — 检索个人纪要


| 参数      | 类型     | 必填  | 说明          |
| ------- | ------ | --- | ----------- |
| `query` | string | ✅   | 完整的中文自然语言问题 |




#### searchMyDoc — 检索个人文档


| 参数      | 类型     | 必填  | 说明          |
| ------- | ------ | --- | ----------- |
| `query` | string | ✅   | 完整的中文自然语言问题 |




#### document_upload — 上传文件/文件夹

> *fileList 和 folderList 至少传一项。


| 参数           | 类型       | 必填  | 说明                                             |
| ------------ | -------- | --- | ---------------------------------------------- |
| `fileList`   | object[] | ❌*  | 顶层文件列表，每项含 `name`/`fileUrl`/`fileType`/`size`  |
| `folderList` | object[] | ❌*  | 文件夹树，每项含 `name`/`files`/`folders`(递归)/`remark` |
| `documentId` | integer  | ❌   | 父级文件夹 ID，不传则上传到"我的文档"根目录                       |
| `sourceType` | integer  | ❌   | 来源类型，不传默认 1（本地上传）                              |


---



### 7.7 量化回测（3 个工具）



#### backtest_submit — 提交量化回测任务


| 参数                        | 类型      | 必填  | 默认    | 说明                                                     |
| ------------------------- | ------- | --- | ----- | ------------------------------------------------------ |
| `prompt`                  | string  | ✅   | —     | 自然语言描述回测需求（因子思路、策略说明）                                  |
| `universe`                | string  | ❌   | hs300 | 股票池：small_scale/hs300/csi500/all_a/hsi/sw:行业名          |
| `benchmark`               | string  | ❌   | hs300 | 基准指数：hs300/zz500/sz50/csi1000/csi2000/hsi/hscei/hstech |
| `start_date` / `end_date` | string  | ❌   | —     | 回测起止日 YYYY-MM-DD                                       |
| `holding_period`          | integer | ❌   | —     | 持仓周期（交易日），一般 1~60                                      |
| `n_groups`                | integer | ❌   | —     | 分组数量，一般 2~20                                           |
| `neutralize_cap`          | boolean | ❌   | true  | 市值中性化                                                  |
| `neutralize_industry`     | boolean | ❌   | true  | 行业中性化（申万一级；单行业池自动降级到二级）                                |
| `mode`                    | string  | ❌   | local | 解析模式：local=全部算子 / wq=仅WQ兼容算子                           |


> 💡 港股池(hsi/all_hk)未显式指定 benchmark 时会自动对齐到 hsi。

```json
{
  "prompt": "低估值高股息策略：选取市盈率低于15且股息率高于5%的股票，等权持有",
  "universe": "all_a",
  "benchmark": "hs300",
  "start_date": "2023-01-01",
  "end_date": "2026-07-01",
  "holding_period": 20,
  "n_groups": 5
}
```



#### backtest_tasks_status — 查询回测任务状态


| 参数       | 类型     | 必填  | 说明            |
| -------- | ------ | --- | ------------- |
| `taskId` | string | ✅   | 提交回测时返回的任务 ID |




#### backtest_task_list — 查询回测任务记录


| 参数     | 类型      | 必填  | 默认  | 说明   |
| ------ | ------- | --- | --- | ---- |
| `page` | integer | ❌   | 1   | 页码   |
| `size` | integer | ❌   | 10  | 每页条数 |


---



## 8. 枚举值速查



### 股票代码格式


| 市场   | 格式        | 示例            |
| ---- | --------- | ------------- |
| 深圳A股 | sz + 6位代码 | sz300750      |
| 上海A股 | sh + 6位代码 | sh600519      |
| 北交所  | bj + 6位代码 | bj920185      |
| 港股   | hk + 5位代码 | hk00700       |
| 美股   | 直接代码      | AAPL / usAAPL |




### 市场类型 (marketType)


| 值   | 含义  |
| --- | --- |
| sh  | 上证  |
| sz  | 深证  |
| bj  | 北交所 |
| hk  | 港股  |
| us  | 美股  |




### 报告期类型 (reportType)


| 值   | 含义       |
| --- | -------- |
| Q1  | 第一季度     |
| S1  | 半年度（上半年） |
| Q3  | 第三季度     |
| A   | 年度报告（全年） |




### 统计口径 (type)


| 值       | 含义                   |
| ------- | -------------------- |
| quarter | 单季度数据                |
| year    | 年初至该季度的累计数据（年报为全年累计） |




### 公告业绩期间 (labelList)


| 值      | 含义       |
| ------ | -------- |
| 2024A  | 2024年年报  |
| 2025Q1 | 2025年一季报 |
| 2025S1 | 2025年半年报 |
| 2025Q3 | 2025年三季报 |




### 宏观指标九分类 (category)


| 值      |
| ------ |
| 货币政策   |
| 财政政策   |
| 景气与情绪  |
| 通胀与物价  |
| 就业与劳动力 |
| 贸易与外部  |
| 金融市场   |
| 房地产与住房 |
| 经济增长   |




### 宏观指标国家/地区 (country)


| 值   |
| --- |
| 中国  |
| 美国  |
| 日本  |
| 欧元区 |




### 期货市场 (market)


| 值        | 含义  | 交易所                  |
| -------- | --- | -------------------- |
| internal | 内盘  | 上期所/大商所/郑商所/中金所/广期所  |
| external | 外盘  | CME/ICE/LME/SGX/港交所等 |




### 代录状态 (recordStatus)


| 值   | 含义   |
| --- | ---- |
| 1   | 待审核  |
| 2   | 进行中  |
| 3   | 已完成  |
| 4   | 录会失败 |




### 代录类型 (recordType)


| 值   | 含义   |
| --- | ---- |
| 1   | 腾讯会议 |
| 2   | 进门路演 |
| 3   | zoom |
| 4   | 电话会议 |
| -1  | 未知   |




### 代录来源 (recordSource)


| 值   | 含义   |
| --- | ---- |
| 0   | 单独会话 |
| 1   | 群聊   |
| 2   | APP  |
| 3   | BRM  |




### 会议状态 (status — self_meeting_list)


| 值   | 含义  |
| --- | --- |
| 1   | 待开始 |
| 2   | 进行中 |
| 3   | 已结束 |
| 4   | 已取消 |
| 5   | 其他  |




### 会议类型 (typeForUser — self_meeting_list)


| 值       | 含义   |
| ------- | ---- |
| generic | 常规会议 |
| webinar | 研讨会  |




### 微信群消息类型 (type — wechat_opinion_list)


| 值   | 含义  |
| --- | --- |
| 1   | 活动  |
| 2   | 纪要  |
| 3   | 报告  |




### 公众号文章范围 (wechatArticleScope)


| 值          | 含义   |
| ---------- | ---- |
| all        | 全部文章 |
| subscribed | 我的订阅 |
| featured   | 精选文章 |




### 文件类型 (fileType — document_search/upload)


| 值   | 含义       |
| --- | -------- |
| 1   | PDF      |
| 2   | WORD     |
| 3   | PPT      |
| 4   | TXT      |
| 5   | 图片       |
| 10  | XLSX     |
| 11  | CSV      |
| 12  | Markdown |
| 13  | HTML     |




### 来源类型 (sourceType / sourceList)


| 值   | 含义   |
| --- | ---- |
| 1   | 本地上传 |
| 2   | 用户创建 |
| 3   | AI参会 |
| 4   | AI进宝 |
| 5   | 会议纪要 |
| 6   | 代录   |
| 7   | 翻译   |
| 8   | 笔记   |
| 9   | 转写   |




### research_query 的 type 参数


| 值            | 含义   |
| ------------ | ---- |
| domestic     | 内资研报 |
| oversea      | 外资研报 |
| minutes      | 纪要   |
| comment      | 点评   |
| announcement | 公告   |
| eventSignal  | 事件信号 |
| dailyReport  | 内参   |




### research_hot_data_query 的 contentType


| 值        | 含义   |
| -------- | ---- |
| minutes  | 纪要   |
| domestic | 内资研报 |
| oversea  | 外资研报 |
| comment  | 点评   |




### 回测股票池 (universe)


| 值           | 含义                  |
| ----------- | ------------------- |
| small_scale | 小盘股池                |
| hs300       | 沪深300               |
| csi500      | 中证500               |
| all_a       | 全A约5600只（沪/深/北全市场）  |
| hsi         | 港股恒生成分股（约80只）       |
| sw:行业名      | 申万一级单行业池（如 sw:医药生物） |




### 回测基准指数 (benchmark)


| 值       | 含义       |
| ------- | -------- |
| hs300   | 沪深300    |
| zz500   | 中证500    |
| sz50    | 上证50     |
| csi1000 | 中证1000   |
| csi2000 | 中证2000   |
| hsi     | 恒生指数     |
| hscei   | 恒生中国企业指数 |
| hstech  | 恒生科技指数   |




### 申万一级行业列表

食品饮料、传媒、机械设备、通信、轻工制造、计算机、海外研究、钢铁、电子、电力设备、有色金属、交通运输、汽车、医药生物、建筑材料、房地产、建筑装饰、农林牧渔、纺织服饰、国防军工、社会服务、基础化工、公用事业、煤炭、家用电器、商贸零售、综合、北交所、中小市值、银行、非银金融、宏观、石油石化、美容护理、环保、固收、策略、金融工程