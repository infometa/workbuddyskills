---
name: dzh-mcp
description: 大智慧金融 MCP 连接器（`dzh-mcp`），提供 A股/港股/美股/期货/基金 的行情、财务、公司简况、股东与分红、技术指标、龙虎榜与资金流向、指数板块、资讯公告、多维选股等证券结构化数据。当用户查询 A股/美股/港股/期货/基金行情、基本面与估值、财务、题材板块、公告研报、新闻舆情、机构调研、盈利预测、资金流向、北向资金、龙虎榜、融资融券、大宗交易、股东持股、分红送转、技术指标、条件选股时，优先调用本连接器的 MCP 工具获取数据。
version: "3.0.0"
author: "大智慧"
metadata:
  mcp_server_name: dzh-mcp
  tags: ["stock", "a股", "dzh", "finance", "港股", "美股", "港美股", "期货", "基金", "选股", "北向资金"]
---
# 大智慧DZH MCP连接器 Skill
> 重要：本Skill对应WorkBuddy MCP连接器`dzh-mcp`，该MCP Server对外提供行情、财务、新闻、公告、研报、股东、分红、资金、选股等证券查询工具。

## 前置约束（全部工具统一生效）
1. 鉴权：使用 WorkBuddy OAuth2 授权获取访问权限；鉴权失败、凭证过期，直接提示用户检查 MCP 连接器凭证配置，禁止自行重试调用。
2. 限流：大智慧行情接口存在QPS限制，禁止循环高频批量调用工具。
3. 参数约束：枚举入参**必须传入枚举字符串字面量，禁止传入中文、数字、Java枚举对象**。
4. 股票代码规范：必须使用大智慧标准代码格式，如`SH600000`、`SZ000001`、`HK00669`、`NSAAPL`（美股需带交易所前缀）、`OF519666`、`DCjd2609`，不能仅输入6位数字。
5. 时间格式：时间类参数严格遵循接口定义格式（K线/指标为`yyyyMMdd-HHmmss`，交易日/报告期为`yyyyMMdd`），格式错误返回空数据集。
6. 复权标记：`split` 全局约定 `0`=不复权，`1`=前复权，`2`=后复权；默认值各工具不同，见对应参数表（K线类默认`0`，技术指标默认`1`）。
7. 行筛选：`start` 为行偏移，字符串型`start`负数表示从末尾向前取（如`-20`取最新20条）；技术指标类`start`为起始行号，`0`/`1`/空均表示从第1行开始。
8. 工具架构：本连接器为「合并查询」型工具——除`getAnnounceInfo`（公告，无`methods`入参，直接返回唯一子方法）外，其余14个工具各自通过`methods`参数按需返回多个子方法数据；`methods`不传或传空数组即返回该工具全部子方法。子方法名继承后端接口命名（含拼音缩写与接口编号，如`Ffjgrg`=卖方研报、`TbGg`=公告、`LhbGpmx`=龙虎榜个股明细、`Gsjs`=公司简况），完整含义见各工具子方法说明；只能调用本文档列出的15个工具及其子方法（`methods`）名称。
9. 批量能力：`stockCodes`类参数支持1~100个代码，返回按股票代码分组嵌套，各子方法结构失败时该key为`{"error":说明}`对象。
10. 合规：本连接器数据仅供参考，不构成投资建议；回答涉及具体标的时应在末尾附股市风险提示（如“以上内容仅供参考，股市有风险，投资需谨慎。”）。

## 错误处理（AI 应对策略）

大智慧接口返回后，AI 必须按下表判断并处理异常场景，**禁止**向用户暴露底层错误码、堆栈或内部地址：

| 场景 | 表现 | AI 应对策略 |
|------|------|-------------|
| 鉴权失败 / 凭证过期 | 鉴权错误 | 直接提示用户检查 MCP 连接器凭证配置；禁止自行重试调用 |
| 股票代码格式错误 | 空数据集或报错 | 检查代码是否为大智慧标准格式（`SH600000`/`SZ000001`/`HK00669`/`NSAAPL`/`OF519666`/`DCjd2609`），补全市场前缀后重查 |
| 时间格式错误 | 返回空数据集 | 时间参数严格按文档格式（`yyyyMMdd-HHmmss` / `yyyyMMdd`），修正后重查 |
| 枚举参数非法 | 参数校验失败 | 枚举必须使用文档列出的字面量（如`period`、`methods`、`operator`、`split`），禁止传中文或数字 |
| 子方法缺必选入参 | 该子方法返回`{"error":说明}` | 按子方法说明补齐必选参数（如期货`tradedate`、指数板块`industry`），其余子方法数据仍可正常使用 |
| 限流（QPS） | 请求被拒绝/节流提示 | 避免循环高频批量调用；如需重试，间隔一段时间后再试 |
| 网络超时 | 请求超时 | 提示用户“数据源暂时不可用，请稍后重试”，禁止无间隔反复重试 |
| 空结果（数据不存在） | 返回空数据集 | 向用户说明“暂未查询到相关数据”，并给出可能原因（代码错误、新股无历史数据、非交易日等） |

通用原则：查询结果为空 ≠ 工具报错，先确认代码、时间、参数是否合理再解释；不暴露底层实现细节；只呈现客观数据，不基于结果做投资建议。

## 可用MCP工具列表

> 下面是本MCP连接器提供的全部工具，AI只能调用这里文档列出的工具名称。
> 除`getAnnounceInfo`（公告，无`methods`入参，直接返回唯一子方法）外，各工具均为「合并查询」型：通过`methods`参数按需查询子方法；`methods`不传或传空数组时返回全部子方法。

### 工具总览（15个，按功能分组）

| 分组 | 工具 | 功能简述 |
|------|------|---------|
| 行情·A股 | `getAShareQuoteData` | A股K线/实时快照/五档盘口/交易统计/估值指标（含个股/板块/指数） |
| 行情·港股 | `getHkStockData` | 港股K线/实时行情/港股新闻/资产负债表/利润表/现金流量表 |
| 行情·美股 | `getUsStockData` | 美股K线/实时行情/美股新闻/现金流量表/利润表/资产负债表 |
| 行情·期货 | `getFuturesData` | 期货实时行情/历史K线/仓单/会员持仓/基本面知识/合约规格 |
| 基金 | `getFundData` | 基金基本信息/持仓明细/业绩与排名/主题关系 |
| 指数·板块 | `getIndexBlockData` | 北向板块统计/北向全市场统计/板块成分股 |
| 公司简况 | `getCompanyProfile` | 公司概况/主营构成/题材概念 |
| 股东 | `getAShareHolderData` | 股东户数/股本结构/股东持股/高管持股/机构持股/限售解禁 |
| 分红 | `getAShareDividendData` | 分红融资股息率/分红简况 |
| 财务 | `getAShareFinanceData` | 主要指标/单季/TTM/六大能力分析/三大报表 |
| 技术指标 | `getAShareTechIndicator` | 智能诊股压力支撑/常用技术指标 |
| 资金·龙虎榜 | `getAShareLhbData` | 大宗交易/融资融券/龙虎榜/北向持仓/资金流向 |
| 资讯 | `getNewsInfo` | 个股/行业/宏观新闻、事件提醒、互动易、社区资讯、机构调研、研报、美股新闻、盈利预测 |
| 公告 | `getAnnounceInfo` | 上市公司公告 |
| 选股 | `findMultiDimStockCodes` | 按指标类别+筛选条件反查满足条件的股票代码 |

### 意图路由速查

| 用户意图 | 选用工具 | 常用 `methods` 示例 |
|------|------|------|
| A股K线/实时快照/五档盘口/交易统计/估值（含个股/板块/指数） | `getAShareQuoteData` | `getQuoteKline`、`getQuoteDyna`、`getQuoteStkdataOrderBook`、`getF10SkFinindicData` |
| 港股行情/新闻/三大报表 | `getHkStockData` | `getGmQuoteKline`、`getGmQuoteDyna`、`getHkBalanceSheetData` |
| 美股行情/新闻/三大报表 | `getUsStockData` | `getGmQuoteKline`、`getGmQuoteDyna`、`getUsProfitData` |
| 期货行情/K线/仓单/会员持仓/合约知识 | `getFuturesData` | `getFuturesQuoteKline`、`getMemberDaily`、`getFuturesKnowledge` |
| 基金基本信息/持仓/业绩排名/主题 | `getFundData` | `getF10FdBasicinfo`、`getF10FdGpmx`、`getF10FdNetworthData` |
| 北向资金板块/全市场统计、板块成分股 | `getIndexBlockData` | `getNorthboundSectorStats`、`getBlockIndustryObj`（需`block`+`industry`） |
| 公司概况/主营构成/题材概念 | `getCompanyProfile` | `getF10GsjsData`、`getF10BusiinfoData`、`getF10Information` |
| 股东户数/股本结构/持股/高管/机构/解禁 | `getAShareHolderData` | `getF10ShareHolderNumData`、`getF10HolderDetailsData`、`getF10XsjjData` |
| 分红/股息率 | `getAShareDividendData` | `getF10FhrzGxlData`、`getF10DividentsData` |
| 财务指标/三大报表/能力分析 | `getAShareFinanceData` | `getStockFinanceData`、`getBalanceSheetMetrics`、`getStockCorpProfit` |
| 技术指标/智能诊股 | `getAShareTechIndicator` | `getIndexevaluation`、`getIndicatorCalc`（`name=MA/MACD/KDJ`…） |
| 龙虎榜/融资融券/大宗交易/北向持仓/资金流向 | `getAShareLhbData` | `getF10LhbGpmxData`、`getFinanceRzrq`、`getNorthboundStockInfo` |
| 新闻/研报/机构调研/互动易/盈利预测 | `getNewsInfo` | `getNewsTextStockData`、`getFfjgrgYbmxData`、`getGgYlycData` |
| 上市公司公告 | `getAnnounceInfo` | （无`methods`，直接返回公告列表） |
| 条件选股（按财务/指标反查代码） | `findMultiDimStockCodes` | `findStockCodesByF10FhrzGxl`、`findStockCodeByZbjgfxParam` |

---

### getAShareQuoteData - 获取A股行情与基础数据

**功能描述**：合并查询A股行情与基础数据（K线/实时快照/五档盘口/交易统计/估值指标），包括个股、板块和指数；时间参数仅作用于K线；支持1~100个代码，返回按股票代码分组嵌套。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SH601519"]`或`["SH601519","SZ000423"]` |
| period | `string` | - | K线周期，默认`DAY_1`；允许值：`MIN_1`,`MIN_5`,`MIN_15`,`MIN_30`,`MIN_60`,`DAY_1`,`WEEK_1`,`MONTH_1`,`SEASON_1`,`HALFYEAR_1`,`YEAR_1` |
| beginTime | `string` | - | 开始时间，格式严格`yyyyMMdd-HHmmss` |
| endTime | `string` | - | 结束时间，格式严格`yyyyMMdd-HHmmss` |
| start | `string` | - | 行筛选偏移，例如`"-10"`表示返回最新10条 |
| count | `integer` | - | 最大返回行数，≥0，默认100 |
| split | `string` | - | 除权标记；`0`=不复权，`1`=前复权，`2`=后复权，默认`0` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getQuoteKline` A股K线行情 ｜ `getQuoteDyna` A股实时行情快照 ｜ `getQuoteStkdataOrderBook` 五档买卖盘及盘后行情 ｜ `getQuoteTradeAndStat` 交易状态与衍生统计 ｜ `getF10SkFinindicData` 估值指标

**返回字段**：详见 `references/getAShareQuoteData.md`。

**调用示例**：

- 查询 SH601519 最新20根日线K线：`stockCodes=["SH601519"]`, `period="DAY_1"`, `start="-20"`, `methods=["getQuoteKline"]`
- 查询 SH601519 实时快照与五档盘口：`stockCodes=["SH601519"]`, `methods=["getQuoteDyna","getQuoteStkdataOrderBook"]`
- 批量查询 SH601519、SZ000423 最新一套估值指标：`stockCodes=["SH601519","SZ000423"]`, `methods=["getF10SkFinindicData"]`
- 查询 SH601519 指定区间前复权日线：`stockCodes=["SH601519"]`, `period="DAY_1"`, `beginTime="20250801-000000"`, `endTime="20250825-150000"`, `split="1"`, `methods=["getQuoteKline"]`

### getHkStockData - 获取港股行情与基础数据

**功能描述**：根据港股代码合并查询港股行情与基础数据（K线/实时快照/港股新闻/资产负债表/利润表/现金流量表）；时间参数仅作用于K线。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCode | `string` | ✅ | 港股代码 例如：`HK00669` |
| period | `string` | - | K线周期，默认`DAY_1`；允许值：`MIN_1`,`MIN_5`,`MIN_15`,`MIN_30`,`MIN_60`,`DAY_1`,`WEEK_1`,`MONTH_1`,`SEASON_1`,`HALFYEAR_1`,`YEAR_1` |
| beginTime | `string` | - | 开始时间，格式严格`yyyyMMdd-HHmmss` |
| endTime | `string` | - | 结束时间，格式严格`yyyyMMdd-HHmmss` |
| start | `string` | - | 行筛选偏移，例如`"-10"`表示返回最新10条 |
| count | `integer` | - | 最大返回行数，≥0，默认100 |
| split | `string` | - | 除权标记；`0`=不复权，`1`=前复权，`2`=后复权，默认`0` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getGmQuoteKline` 港股历史行情 ｜ `getGmQuoteDyna` 港股实时行情 ｜ `getYqXqHkData` 港股新闻雪球 ｜ `getHkBalanceSheetData` 港股资产负债表 ｜ `getHkIncomeStatementData` 港股利润表 ｜ `getHkCashFlowStatementData` 港股现金流量表

**返回字段**：详见 `references/getHkStockData.md`。

**调用示例**：

- 查询 HK00669 最新20根日线K线：`stockCode="HK00669"`, `period="DAY_1"`, `start="-20"`, `methods=["getGmQuoteKline"]`
- 查询 HK00669 实时行情与港股新闻：`stockCode="HK00669"`, `methods=["getGmQuoteDyna","getYqXqHkData"]`
- 查询 HK00669 港股三大报表：`stockCode="HK00669"`, `methods=["getHkBalanceSheetData","getHkIncomeStatementData","getHkCashFlowStatementData"]`

### getUsStockData - 获取美股行情与基础数据

**功能描述**：根据美股代码合并查询美股行情与基础数据（K线/实时快照/美股新闻/现金流量表/利润表/资产负债表，三大报表均为最新报告期）；时间参数仅作用于K线。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCode | `string` | ✅ | 美股代码，需带交易所前缀 例如：`NSAAPL` |
| period | `string` | - | K线周期，默认`DAY_1`；允许值：`MIN_1`,`MIN_5`,`MIN_15`,`MIN_30`,`MIN_60`,`DAY_1`,`WEEK_1`,`MONTH_1`,`SEASON_1`,`HALFYEAR_1`,`YEAR_1` |
| beginTime | `string` | - | 开始时间，格式严格`yyyyMMdd-HHmmss` |
| endTime | `string` | - | 结束时间，格式严格`yyyyMMdd-HHmmss` |
| start | `string` | - | 行筛选偏移，例如`"-10"`表示返回最新10条 |
| count | `integer` | - | 最大返回行数，≥0，默认100 |
| split | `string` | - | 除权标记；`0`=不复权，`1`=前复权，`2`=后复权，默认`0` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getGmQuoteKline` 美股历史行情 ｜ `getGmQuoteDyna` 美股实时行情 ｜ `getYqXqUsData` 美股新闻雪球 ｜ `getUsCashFlowData` 美股现金流量表 ｜ `getUsProfitData` 美股利润表 ｜ `getUsBalanceSheetData` 美股资产负债表

**返回字段**：详见 `references/getUsStockData.md`。

**调用示例**：

- 查询 NSAAPL 最新20根日线K线：`stockCode="NSAAPL"`, `period="DAY_1"`, `start="-20"`, `methods=["getGmQuoteKline"]`
- 查询 NSAAPL 实时行情与美股新闻：`stockCode="NSAAPL"`, `methods=["getGmQuoteDyna","getYqXqUsData"]`
- 查询 NSAAPL 最新一期三大报表：`stockCode="NSAAPL"`, `methods=["getUsBalanceSheetData","getUsProfitData","getUsCashFlowData"]`

### getFuturesData - 获取期货行情与数据

**功能描述**：合并查询期货行情与数据（实时行情/历史K线/仓单明细/会员持仓概览/会员持仓明细/品种持仓汇总/持仓变化趋势/基本面知识/合约规格）；**各子方法必选入参见下方说明，缺省时该组返回error**。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCode | `string` | - | 期货/合约代码 例如：`DCjd2609`，兼作会员持仓类的品种代码 |
| period | `string` | - | K线周期，默认`DAY_1`；允许值：`MIN_1`,`MIN_5`,`MIN_15`,`MIN_30`,`MIN_60`,`DAY_1`,`WEEK_1`,`MONTH_1`,`SEASON_1`,`HALFYEAR_1`,`YEAR_1` |
| beginTime | `string` | - | 开始时间，格式严格`yyyyMMdd-HHmmss` |
| endTime | `string` | - | 结束时间，格式严格`yyyyMMdd-HHmmss` |
| start | `string` | - | 行筛选偏移，例如`"-10"`表示返回最新10条 |
| count | `integer` | - | 最大返回行数，≥0，默认100 |
| split | `string` | - | 除权标记；`0`=不复权，`1`=前复权，`2`=后复权，默认`0` |
| varietycode | `string` | - | 仓单明细品种代码 例如：`CU` |
| exchange | `string` | - | 仓单明细市场代码 例如：`001008` |
| tradedate | `string` | - | 交易日期，格式`YYYYMMDD`；会员持仓类必选，仓单不传则取最新交易日 |
| warehousetype | `integer` | - | 仓单明细仓库类型：`1`完税，`2`保税，不传则全部 |
| days | `integer` | - | 概览/趋势最近N天，概览默认1最大30，趋势默认5最大20 |
| compcode | `string` | - | 会员代码，精确匹配 例如：`80050220` |
| compsname | `string` | - | 会员简称，模糊匹配 例如：`中信` |
| sesname | `string` | - | 期货简称，模糊匹配 例如：`豆粕` |
| topN | `integer` | - | 会员持仓明细按净持仓绝对值返回前N名 |
| signalDirection | `string` | - | 持仓趋势筛选会员方向：`正向`/`负向`/`中性` |
| productCodes | `List<string>` | - | 品种代码列表，知识必选、规格可选 例如：`["LC","AU"]` |
| clauseTypes | `List<string>` | - | 知识类型代码列表 例如：`["1","2"]`，不传返回所有类型 |
| keyword | `string` | - | 知识标题或内容模糊匹配关键词 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getFuturesQuoteDyna` 期货实时行情（需期货代码） ｜ `getFuturesQuoteKline` 期货历史K线（需期货代码） ｜ `queryWarehouseReceiptDetail` 仓单明细仓库（需`varietycode`如CU与`exchange`如001008，`tradedate`默认最新交易日） ｜ `getMarketSummary` 会员持仓概览（需`tradedate`，`days`默认1最大30） ｜ `getMemberDaily` 会员持仓明细（需`tradedate`，`compcode`精确/`compsname`模糊/期货代码筛选/`topN`净持仓前N，均可选） ｜ `getDailyStats` 品种持仓汇总（需`tradedate`，期货代码精确/期货简称模糊可选，均不传返回全品种TOP20/聪明钱/散户汇总） ｜ `getSymbolTrend` 持仓变化趋势（期货代码或期货简称至少一个，`days`默认5最大20，`signalDirection`可选，可指定单一会员） ｜ `getFuturesKnowledge` 基本面知识（需`productCodes`；`clauseTypes`：1品种概况2影响因素3交易规则4相关计算5外盘合约6限仓制度7大额未平仓合约8交割交易9交割单位10结算细则11风控办法，可选；`keyword`可选） ｜ `getContractSpecs` 合约规格（期货代码或`productCodes`至少一个）

**返回字段**：详见 `references/getFuturesData.md`。

**调用示例**：

- 查询 DCjd2609 最新20根日线K线：`stockCode="DCjd2609"`, `period="DAY_1"`, `start="-20"`, `methods=["getFuturesQuoteKline"]`
- 查询 DCjd2609 实时行情：`stockCode="DCjd2609"`, `methods=["getFuturesQuoteDyna"]`
- 查询铜（CU）在 001008 市场的仓单明细：`varietycode="CU"`, `exchange="001008"`, `methods=["queryWarehouseReceiptDetail"]`
- 查询 2025-08-25 全市场会员持仓概览（近3天）：`tradedate="20250825"`, `days=3`, `methods=["getMarketSummary"]`
- 查询 2025-08-25 中信持仓明细净持仓前10：`tradedate="20250825"`, `compsname="中信"`, `topN=10`, `methods=["getMemberDaily"]`
- 查询豆粕持仓变化趋势（近5日、正向）：`sesname="豆粕"`, `days=5`, `signalDirection="正向"`, `methods=["getSymbolTrend"]`
- 查询 LC、AU 品种概况与交易规则：`productCodes=["LC","AU"]`, `clauseTypes=["1","3"]`, `methods=["getFuturesKnowledge"]`
- 查询 DCjd2609 合约规格：`stockCode="DCjd2609"`, `methods=["getContractSpecs"]`

### getFundData - 获取基金行情与数据

**功能描述**：根据基金代码合并查询基金行情与数据（基本信息/持仓明细/业绩与排名/主题关系）。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| fsymbol | `string` | ✅ | 基金代码 例如：`OF519666` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getF10FdBasicinfo` 基金基本信息 ｜ `getF10FdGpmx` 基金持仓明细 ｜ `getF10FdNetworthData` 基金业绩与排名 ｜ `getF10FdTopicRelations` 基金主题关系

**返回字段**：详见 `references/getFundData.md`。

**调用示例**：

- 查询 OF519666 基金基本信息：`fsymbol="OF519666"`, `methods=["getF10FdBasicinfo"]`
- 查询 OF519666 最新一期持仓明细与各周期收益排名：`fsymbol="OF519666"`, `methods=["getF10FdGpmx","getF10FdNetworthData"]`
- 查询 OF519666 基金主题关系：`fsymbol="OF519666"`, `methods=["getF10FdTopicRelations"]`

### getIndexBlockData - 获取指数与板块数据

**功能描述**：合并查询指数与板块数据（北向板块统计/北向全市场统计/板块成分股）。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| block | `string` | ✅ | 板块代码 例如：参考`blockCodeParamRule`（本工具统一必填） |
| industry | `string` | - | 行业或分类名称，查询板块成分股时配合`block`一起传入 例如：证监会行业、大智慧行业 |
| beginTime | `string` | - | 开始时间，格式`yyyyMMdd-HHmmss`，默认3个月内，作用于北向全市场统计 |
| endTime | `string` | - | 结束时间，格式`yyyyMMdd-HHmmss` |
| start | `integer` | - | 行筛选，`0`/`1`/空都表示第1行开始 |
| count | `integer` | - | 行筛选，≥0的整数，`0`或空表示取所有 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getNorthboundSectorStats` 北向板块统计（需`block`） ｜ `getNorthboundFundFullStats` 北向全市场统计（时间区间默认3个月内） ｜ `getBlockIndustryObj` 板块成分股（需`industry`，缺省时该组返回error）

**返回字段**：详见 `references/getIndexBlockData.md`。

**调用示例**：

- 查询某板块北向资金统计：`block="<板块代码>"`, `methods=["getNorthboundSectorStats"]`
- 查询近3个月北向全市场统计：`block="<板块代码>"`, `methods=["getNorthboundFundFullStats"]`（可加`beginTime`/`endTime`限定区间）
- 查询大智慧行业-保险业板块成分股（`block`与`industry`同时传入）：`block="<板块代码>"`, `industry="大智慧行业"`, `methods=["getBlockIndustryObj"]`

### getCompanyProfile - 获取A股公司简况数据

**功能描述**：根据股票代码合并查询A股公司简况（公司概况/主营构成/题材概念）；`typeStyle`仅作用于主营构成。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCode | `string` | ✅ | 股票代码 例如：`SH601519` |
| typeStyle | `integer` | - | 主营构成类型：`1`行业、`2`产品、`3`地区，不传取所有类型 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getF10GsjsData` 公司概况 ｜ `getF10BusiinfoData` 主营构成（1行业/2产品/3地区，不传取全部） ｜ `getF10Information` 题材概念

**返回字段**：详见 `references/getCompanyProfile.md`。

**调用示例**：

- 查询 SH601519 公司概况：`stockCode="SH601519"`, `methods=["getF10GsjsData"]`
- 查询 SH601519 按产品分主营收入情况：`stockCode="SH601519"`, `typeStyle=2`, `methods=["getF10BusiinfoData"]`
- 查询 SZ000423 题材概念：`stockCode="SZ000423"`, `methods=["getF10Information"]`

### getAShareHolderData - 获取A股股东持股数据

**功能描述**：合并查询A股股东持股数据（股东户数/股本结构变动/股东持股明细/高管持股变动/机构持股明细/限售解禁）；`type`仅作用于股东持股明细；支持1~100个代码。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SH601519"]`或`["SH601519","SZ000423"]` |
| type | `integer` | - | 股东持股明细类型：`1`十大股东、`2`十大流通股东，不传取所有类型 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getF10ShareHolderNumData` 股东户数 ｜ `getF10ShareStruchgData` 股本结构变动 ｜ `getF10HolderDetailsData` 股东持股明细（1十大股东/2十大流通股东） ｜ `getF10GgholderchgData` 高管持股变动 ｜ `getF10JgccmxData` 机构持股明细 ｜ `getF10XsjjData` 限售解禁

**返回字段**：详见 `references/getAShareHolderData.md`。

**调用示例**：

- 查询 SH601519 十大股东：`stockCodes=["SH601519"]`, `type=1`, `methods=["getF10HolderDetailsData"]`
- 批量查询 SH601519、SZ000423 股东户数与股本结构变动：`stockCodes=["SH601519","SZ000423"]`, `methods=["getF10ShareHolderNumData","getF10ShareStruchgData"]`
- 查询 SH601519 高管持股变动与限售解禁：`stockCodes=["SH601519"]`, `methods=["getF10GgholderchgData","getF10XsjjData"]`

### getAShareDividendData - 获取A股分红数据

**功能描述**：合并查询A股分红数据（分红融资股息率/分红简况）；`yearDate`年度条件仅作用于分红简况，默认最新；支持1~100个代码。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SH601519"]`或`["SH601519","SZ000423"]` |
| yearDate | `List<object>` | - | 分红简况年度范围条件列表，默认最新；子对象`{"operator":"枚举值","value":yyyy}`；`operator`允许值：`EQ`等于,`GT`大于,`GTE`大于等于,`LT`小于,`LTE`小于等于 例如：`[{"operator":"EQ","value":2024}]` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getF10FhrzGxlData` 分红融资股息率 ｜ `getF10DividentsData` 分红简况

**返回字段**：详见 `references/getAShareDividendData.md`。

**调用示例**：

- 查询 SH601519 2025 年度分红数据：`stockCodes=["SH601519"]`, `yearDate=[{"operator":"EQ","value":2025}]`, `methods=["getF10DividentsData"]`
- 查询 SH601519 2022 年及以后各年度分红数据：`stockCodes=["SH601519"]`, `yearDate=[{"operator":"GTE","value":2022}]`, `methods=["getF10DividentsData"]`
- 查询 SH601519 最新股息率：`stockCodes=["SH601519"]`, `methods=["getF10FhrzGxlData"]`

### getAShareFinanceData - 获取A股深度财务数据

**功能描述**：合并查询A股深度财务数据（主要指标/单季/TTM/盈利/偿债/成长/资本结构/营运/收益质量/资产负债表/现金流量表/利润表）；`endDate`报告期条件对所有子方法统一生效，不传默认最新；支持1~100个代码。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SH601519"]`或`["SH601519","SZ000423"]` |
| endDate | `List<object>` | - | 报告期范围查询条件列表，支持操作符与数值组合，范围查询支持条件重复，默认最新；子对象`{"operator":"枚举值","value":yyyyMMdd}`；`operator`允许值：`EQ`,`GT`,`GTE`,`LT`,`LTE` 例如：`[{"operator":"EQ","value":20241231}]` |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getStockFinanceData` 财务主要指标 ｜ `getDjcwData` 单季财务指标 ｜ `getTtmcwData` TTM财务指标 ｜ `getStockYlnlfx` 盈利能力分析 ｜ `getStockCznlfx` 偿债能力分析 ｜ `getStockCenznlfx` 成长能力分析 ｜ `getZbjgfx` 资本结构分析 ｜ `getStockYynlfx` 营运能力分析 ｜ `getStockSyzlfx` 收益质量分析 ｜ `getBalanceSheetMetrics` 资产负债表 ｜ `getStockXjllData` 现金流量表 ｜ `getStockCorpProfit` 利润表一般企业 ｜ `getStockPrgbincstatement` 利润表银行（仅银行类股票有数据） ｜ `getStockInsProfit` 利润表保险（仅保险类股票有数据） ｜ `getStockSecuProfit` 利润表证券（仅证券类股票有数据）

**返回字段**：详见 `references/getAShareFinanceData.md`。

**调用示例**：

- 查询 SH601519 最新一期财务主要指标：`stockCodes=["SH601519"]`, `methods=["getStockFinanceData"]`
- 查询 SH601519 2024 年年报三大报表：`stockCodes=["SH601519"]`, `endDate=[{"operator":"EQ","value":20241231}]`, `methods=["getBalanceSheetMetrics","getStockCorpProfit","getStockXjllData"]`
- 查询 SH601519 2024-01-01 之后所有报告期的资产负债数据：`stockCodes=["SH601519"]`, `endDate=[{"operator":"GTE","value":20240101}]`, `methods=["getBalanceSheetMetrics"]`
- 查询 SH601519 成长能力与盈利能力分析：`stockCodes=["SH601519"]`, `methods=["getStockCenznlfx","getStockYlnlfx"]`
- 查询某银行股利润表（银行口径）：`stockCodes=["SH601398"]`, `methods=["getStockPrgbincstatement"]`

### getAShareTechIndicator - 获取A股技术指标分析

**功能描述**：根据股票代码合并查询A股技术指标（智能诊股压力支撑/常用技术指标MA/BOLL/VOL/KDJ/MACD/RSI/DDX/DDY/DDZ）；时间参数仅作用于常用技术指标。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCode | `string` | ✅ | 股票代码 例如：`SH601519` |
| name | `string` | - | 常用技术指标名称，可选，不传返回全部指标；允许值：`MA`移动平均线,`BOLL`布林带,`VOL`成交量,`KDJ`随机指标,`MACD`指数平滑异同平均指标,`RSI`相对强弱指标,`DDX`大单动向,`DDY`大单买入比例,`DDZ`大单卖出比例 |
| beginTime | `string` | - | 开始时间，格式`yyyyMMdd-HHmmss`，常用指标默认半年内 |
| endTime | `string` | - | 结束时间，格式`yyyyMMdd-HHmmss` |
| split | `string` | - | 除权字段；`0`=不复权，`1`=前复权，`2`=后复权，默认`1`，仅作用于常用技术指标 |
| start | `integer` | - | 行筛选，`0`/`1`/空都表示第1行开始 |
| count | `integer` | - | 行筛选，≥0的整数，`0`或空表示取所有 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getIndexevaluation` 智能诊股压力支撑 ｜ `getIndicatorCalc` 常用技术指标MA/BOLL/VOL/KDJ/MACD/RSI/DDX/DDY/DDZ

**返回字段**：详见 `references/getAShareTechIndicator.md`。

**调用示例**：

- 查询 SH601519 智能诊股压力支撑：`stockCode="SH601519"`, `methods=["getIndexevaluation"]`
- 查询 SH601519 默认时间范围内 MA 均线指标（前复权）：`stockCode="SH601519"`, `name="MA"`, `methods=["getIndicatorCalc"]`
- 查询 SH601519 2025-01-01 09:30 至 2025-08-25 15:00 区间 MACD 指标，前复权：`stockCode="SH601519"`, `name="MACD"`, `beginTime="20250101-093000"`, `endTime="20250825-150000"`, `split="1"`, `methods=["getIndicatorCalc"]`
- 查询 SH601519 KDJ 指标最新20条、后复权：`stockCode="SH601519"`, `name="KDJ"`, `split="2"`, `start=0`, `count=20`, `methods=["getIndicatorCalc"]`

### getAShareLhbData - 获取A股龙虎榜大宗交易及资金流向数据

**功能描述**：合并查询龙虎榜、大宗交易及资金流向数据（大宗交易/融资融券/龙虎榜/北向持仓/资金流向分时与历史）；时间参数作用于北向持仓与资金流向历史；支持1~100个代码。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SH601519"]`或`["SH601519","SZ000423"]` |
| beginTime | `string` | - | 开始时间，格式`yyyyMMdd-HHmmss`，默认3个月内，作用于北向持仓与资金流向历史 |
| endTime | `string` | - | 结束时间，格式`yyyyMMdd-HHmmss` |
| tradeDate | `string` | - | 龙虎榜交易日，格式`yyyyMMdd`，可选，不传取最近一个月 |
| chgType | `integer` | - | 龙虎榜涨跌类型，可选（具体取值以接口返回为准） |
| start | `integer` | - | 行筛选，`0`/`1`/空都表示第1行开始 |
| count | `integer` | - | 行筛选，≥0的整数，`0`或空表示取所有 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getF10BlocktradeXwtj` 大宗交易明细 ｜ `getFinanceRzrq` 融资融券 ｜ `getF10LhbGpmxData` 龙虎榜明细（最近一个月内，`tradeDate`为单日yyyyMMdd） ｜ `getNorthboundStockInfo` 北向资金个股持仓（时间区间默认3个月内） ｜ `getCapitalinflowMin` 资金流向分时（最新交易日） ｜ `getCapitalinflowKline` 资金流向历史走势（`beginTime`与`endTime`跨度最大10天，`count`默认5最大10）

**返回字段**：详见 `references/getAShareLhbData.md`。

**调用示例**：

- 查询 SH601519 在 2025-08-25 的龙虎榜明细：`stockCodes=["SH601519"]`, `tradeDate="20250825"`, `methods=["getF10LhbGpmxData"]`
- 查询 SH601519 融资融券与大宗交易明细：`stockCodes=["SH601519"]`, `methods=["getFinanceRzrq","getF10BlocktradeXwtj"]`
- 查询 SH601519 近3个月北向资金持仓变化：`stockCodes=["SH601519"]`, `methods=["getNorthboundStockInfo"]`
- 查询 SH601519 最新交易日资金流向分时：`stockCodes=["SH601519"]`, `methods=["getCapitalinflowMin"]`
- 查询 SH601519 资金流向历史走势（近5个交易日）：`stockCodes=["SH601519"]`, `beginTime="20250818-000000"`, `endTime="20250825-150000"`, `count=5`, `methods=["getCapitalinflowKline"]`

### getNewsInfo - 获取资讯信息

**功能描述**：合并查询资讯信息（个股新闻/行业新闻/宏观新闻/事件提醒/互动易/社区资讯/机构调研/研报明细/美股新闻/盈利预测）；**行业/宏观新闻仅单代码查询时返回**；支持1~100个代码。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SZ000423"]`或`["SZ000423","SH601519"]` |
| newssource | `string` | - | 新闻来源，可选 例如：`新华社`/`财联社`，用于行业新闻与宏观新闻过滤 |
| methods | `List<string>` | - | 按需加载，可多选；不传或空数组=查询全部 |

**子方法（methods）**：`getNewsTextStockData` 个股新闻 ｜ `getNewsTextIndData` 行业新闻（仅单代码查询时返回） ｜ `getNewsTextMeData` 宏观新闻（仅单代码查询时返回） ｜ `getF10SjtxData` 事件提醒 ｜ `getF10TnwData` 互动易董秘爆料 ｜ `getJiuyanBkcfgData` 社区资讯韭研公社 ｜ `getTrs0031Data` 机构调研记录 ｜ `getFfjgrgYbmxData` 研报明细 ｜ `getYqXqUsData` 美股新闻雪球（需美股代码） ｜ `getGgYlycData` 盈利预测

**返回字段**：详见 `references/getNewsInfo.md`。

**调用示例**：

- 查询 SZ000423 个股新闻与事件提醒：`stockCodes=["SZ000423"]`, `methods=["getNewsTextStockData","getF10SjtxData"]`
- 查询 SZ000423 机构调研与研报明细：`stockCodes=["SZ000423"]`, `methods=["getTrs0031Data","getFfjgrgYbmxData"]`
- 查询 SH601519 盈利预测：`stockCodes=["SH601519"]`, `methods=["getGgYlycData"]`
- 查询 SZ000423 行业新闻与宏观新闻（仅单代码查询时返回）：`stockCodes=["SZ000423"]`, `methods=["getNewsTextIndData","getNewsTextMeData"]`
- 查询 NSAAPL 美股新闻雪球：`stockCodes=["NSAAPL"]`, `methods=["getYqXqUsData"]`

### getAnnounceInfo - 获取公告信息

**功能描述**：查询上市公司公告列表；支持1~100个代码，返回按股票代码分组嵌套。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| stockCodes | `List<string>` | ✅ | 股票代码列表，1~100个 例如：`["SZ000423"]`或`["SZ000423","SH601519"]` |

**子方法**：`getF10TbGgMoData` 公告列表（本工具无`methods`入参，直接返回该子方法）

**返回字段**：详见 `references/getAnnounceInfo.md`。

**调用示例**：

- 查询 SZ000423 近期公告：`stockCodes=["SZ000423"]`
- 批量查询 SZ000423、SH601519 公告：`stockCodes=["SZ000423","SH601519"]`

### findMultiDimStockCodes - 多维条件选股

**功能描述**：多维条件选股——按指标类别+筛选条件反查满足条件的股票代码集合，返回按方法分组嵌套；可筛字段见下方各指标类别说明。

**参数说明**：

| 参数名 | 类型 | 必填 | 描述 |
|------|------|:----:|------|
| methods | `List<string>` | ✅ | 指标类别，必选，可多选；每个类别可选值及其可筛字段见下表 |
| filters | `List<object>` | ✅ | 筛选条件数组，字段须属于所选指标类别，例如：`[{"field":{"gxl":3},"operator":"GT"},{"field":{"negotiablemv":1000000},"operator":"LT"}]`；数值字段支持`EQ`/`GT`/`GTE`/`LT`/`LTE`，文本字段仅`EQ`；同字段范围查询传多条 |

**指标类别（methods）及可筛字段**：

| 可选值 | 说明（可筛字段） |
|--------|------|
| `findStockCodeByBalanceSheetMetrics` | 资产负债表选股(元)：`enddate`报告期yyyyMMdd,`curfds`货币资金,`tradfinasset`交易性金融资产,`accorece`应收账款,`prep`预付款项,`inve`存货,`totcurrasset`流动资产合计,`goodwill`商誉,`totasset`资产总计,`shorttermborr`短期借款,`accopaya`应付账款,`advapaym`预收款项,`totalcurrliab`流动负债合计,`longborr`长期借款,`longpaya`长期应付款,`totliab`负债合计,`paresharrigh`归母股东权益,`contractliab`合同负债,`notesaccorece`应收票据及应收账款,`contractasset`合同资产 |
| `findStockCodesByCorpProfitParam` | 利润表选股(一般企业,元)：`enddate`报告期yyyyMMdd,`reporttype`报告类型1合并期末2母公司期末,`bizinco`营业总收入,`salesexpe`销售费用,`manaexpe`管理费用,`finexpe`财务费用,`inveinco`投资收益,`perprofit`营业利润,`totprofit`利润总额,`biztotinco`营业收入,`biztotcost`营业成本,`deveexpe`研发费用,`npcut`扣非净利润,`bizcost`营业总成本 |
| `findStockCodesByPrgbincstatement` | 银行利润表选股：`enddate`截止日期yyyyMMdd,`begindate`报告开始日期,`netprofit`净利润,`netparecompprof`归母净利润,`basiceps`基本每股收益,`reportyear`报告年度,`npcut`扣非净利润 |
| `findStockCodesByInsProfitParam` | 保险利润表选股(元)：`enddate`报告期yyyyMMdd,`inveinco`投资收益,`valuechgloss`公允价值变动损益,`finexpe`财务费用,`operprofit`营业利润,`totprofit`利润总额,`netprofit`净利润,`netparesharprof`归母净利润,`basiceps`每股收益 |
| `findStockCodesBySecuProfitParam` | 证券利润表选股(元)：`enddate`公告截止日期yyyyMMdd,`bizinco`营业收入,`netinvinco`投资收益,`valuechgnetinco`公允价值变动收益,`netexchggain`汇兑净收益,`bizexpe`营业支出,`operprofit`营业利润,`totprofit`利润总额,`netprofit`净利润,`basiceps`每股收益,`creditimplosse`信用减值损失 |
| `findStockCodesByYlnlfx` | 盈利能力选股(%)：`enddate`报告期yyyyMMdd,`roediluted`摊薄ROE,`roedilutedcut`扣非ROE,`cbb`营业总成本/营业总收入,`roeweighted`加权ROE,`ebitdamargin`息税折旧摊销前利润率,`scostrt`销售成本率,`sgpmargin`销售毛利率,`snpmarginconms`销售净利率,`roa`总资产报酬率,`roic`投入资本回报率,`triexprt`三项费用比重,`opexprt`营业费用率,`opprort`营业利润率,`mgtexprt`管理费用率,`finlexprt`财务费用率 |
| `findStockCodesByCznlfx` | 偿债能力选股(%)：`enddate`报告期yyyyMMdd,`ldbl`流动比率,`sdbl`速动比率,`xjbl`现金比率,`fzqybl`负债权益比率,`gdqybl`股东权益比率,`gdqydfz`股东权益对负债比率 |
| `findStockCodesByCenznlfx` | 成长能力选股(%)：`enddate`报告期yyyyMMdd,`epsdiluted`摊薄EPS增长率,`epsdilutedcut`扣非EPS增长率,`naps`每股净资产增长率,`opncfps`每股经营现金流增长率,`tagrt`营业总收入增长率,`bizinco`营业收入增长率,`totprofit`利润总额增长率,`perprofit`营业利润增长率,`npgrt`净利润增长率,`npcut`扣非净利润增长率,`parenetp`归母净利润增长率,`mananetr`经营净现金增长率,`totasset`总资产增长率,`totliab`总负债增长率 |
| `findStockCodeByZbjgfxParam` | 资本结构选股(%)：`enddate`报告期yyyyMMdd,`zcfzl`资产负债率,`gdqybl`股东权益比率,`cqfzbl`长期负债比率,`ldzczb`流动资产/总资产,`fldzczb`非流动资产/总资产,`zwzczb`总债务/总资产(倍),`ldfzzb`流动负债/总负债,`fldfzzb`非流动负债/总负债 |
| `findStockCodesByYynlfx` | 营运能力选股：`enddate`报告期yyyyMMdd,`opcycle`经营周期(天),`cashconvcycle`现金循环周期(天),`invturnrt`存货周转率(次),`invturndays`存货周转天数(天),`accrecgturnrt`应收账款周转率(次),`accrecgturndays`应收账款周转天数(天),`accpayrt`应付账款周转率(次),`accpaytdays`应付账款周转天数(天),`curassturnrt`流动资产周转率(次),`curassturndays`流动资产周转天数(天),`faturnrt`固定资产周转率(次),`faturndays`固定资产周转天数(天),`taturnrt`总资产周转率(次),`taturndays`总资产周转天数(天),`equturnrt`股东权益周转率(次),`nopcapturnrt`净营运资本周转率(次) |
| `findStockCodesBySyzlfx` | 收益质量选股(%)：`enddate`报告期yyyyMMdd,`npcuttonp`扣非净利润/净利润 |
| `findStockCodesByFinance` | 最新财务指标选股：`enddate`报告期yyyyMMdd,`roeweighted`加权ROE(%),`naps`每股净资产(元),`crps`每股资本公积金(元),`upps`每股未分配利润(元),`oprevps`每股主营收入(元),`epsdilutedcut`扣非每股收益(元),`parenetp`净利润(元),`npgrt`净利润增长率(%),`npcut`扣非净利润(元),`biztotinco`营业总收入(元),`tagrt`营业总收入增长率(%),`sgpmargin`毛利率(%),`snpmarginconms`销售净利率(%),`opprort`营业利润率(%),`assliabrt`资产负债率(%),`currentrt`流动比率(%),`quickrt`速动比率(%),`epsbasic`每股收益(元),`invturndays`存货周转天数(天),`accrecgturndays`应收账款周转天数(天),`opncfps`每股经营现金流(元) |
| `findStockCodesByF10Dividents` | 分红选股：`diviyear`年度yyyy,`publishdate`公告日期yyyyMMdd,`fpya`方案,`divipayratio`股利支付率(%),`xdrdate`除权除息日yyyyMMdd |
| `findStockCodesByF10FhrzGxl` | 股息率选股：`gxl`股息率(%),`negotiablemv`流通市值(万元),`totmktcap`总市值(万元) |

**调用示例**：

- 筛选股息率>3%的A股：`methods=["findStockCodesByF10FhrzGxl"]`, `filters=[{"field":{"gxl":3},"operator":"GT"}]`
- 筛选资产负债率<50%的A股：`methods=["findStockCodeByZbjgfxParam"]`, `filters=[{"field":{"zcfzl":50},"operator":"LT"}]`
- 筛选资产总计>100亿(10000000000元)的A股：`methods=["findStockCodeByBalanceSheetMetrics"]`, `filters=[{"field":{"totasset":10000000000},"operator":"GT"}]`
- 筛选加权ROE>15% 且 净利润增长率>20%的A股：`methods=["findStockCodesByYlnlfx","findStockCodesByCenznlfx"]`, `filters=[{"field":{"roeweighted":15},"operator":"GT"},{"field":{"npgrt":20},"operator":"GT"}]`

## 投资风险提示与免责声明

- 本连接器数据来源于大智慧官方金融数据接口，数据可能存在延迟、不完整或与官方发布不一致的情况，**仅供参考，不构成任何投资建议**。
- AI 使用本连接器数据回答问题时，仅呈现客观数据，**不得**据此给出买入、卖出、加仓、减仓等投资决策建议。
- 用户基于本数据做出的任何投资决策，风险由用户自行承担；请以交易所及上市公司官方披露为准。
- 涉及具体标的时，建议在回复末尾附上股市风险提示，例如“以上内容仅供参考，股市有风险，投资需谨慎。”。
