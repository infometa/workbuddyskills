---
name: yingmi-mcp-skill
description: 盈米 MCP 金融工具使用技能，支持基金与市场数据查询、投研分析、组合诊断、财富规划和金融内容生成
version: "1.0.0"
author: "盈米基金"
---

# 盈米 MCP Skill

盈米 MCP 是面向 AI 的专业金融工具服务，提供金融数据、投顾内容、投研分析、投顾规划和通用金融能力。

官方使用指南：https://yingmi.feishu.cn/docx/PRPRds5SBo2MITxHJL2cMPminEf

## 调用规则

1. 先根据下方分组选择候选工具，再读取 MCP 运行时提供的 Tool Schema。
2. 下方参数来自当前 MCP OpenAPI Schema；服务升级后以运行时 Schema 为最终依据。
3. 参数表中的 ✅ 表示必填；复杂 object/array 的子字段必须继续按运行时 Schema 构造。
4. 具体金融数据必须来自 MCP 返回，不得编造或用模型记忆补全。
5. 不展示 API Key、完整专属 MCP URL 或其他认证信息。

## 可用工具

| 能力分组 | 什么时候使用 | 常用工具 |
| --- | --- | --- |
| 基础时间能力 | 当前时间、交易日范围 | `GetCurrentTime`、`GetTxnDayRange` |
| 基金检索与资料 | 搜基金、确认代码、查详情、交易规则、分红与拆分历史 | `SearchFunds`、`GuessFundCode`、`BatchGetFundsDetail`、`GetPopularFund`、`BatchGetFundTradeLimit`、`BatchGetFundTradeRules`、`BatchGetFundsDividendRecord`、`BatchGetFundsSplitHistory` |
| 单只基金分析 | 业绩、风险、归因、行业、风格、债基指标 | `GetFundDiagnosis`、`AnalyzeFundRisk`、`GetBatchFundPerformance`、`BatchGetFundNavHistory`、`GetFundAssetClassAnalysis`、`getFundBenchmarkInfo`、`getFundBrinsonIndicator`、`getFundCampisiIndicator`、`getFundIndustryAllocation`、`getFundIndustryConcentration`、`getFundIndustryPreference`、`getFundIndustryReturns`、`getFundTurnoverRate`、`fund-equity-position`、`fund-recovery-ability`、`fund-sector-preference`、`getMarketTimingIndicator`、`getStockAllocationAndMetricsByFundCode`、`getQdFundAreaAllocation`、`getBondAllocationByFundCode`、`getBondFundCreditRatingLevel`、`getBondIndicator`、`getBondFundWithAlertRecord`、`getFundDiveCount` |
| 组合与策略 | 多基金组合、相关性、回测、风险、穿透配置、策略查询 | `GetFundsCorrelation`、`GetFundsBackTest`、`DiagnoseFundPortfolio`、`AnalyzePortfolioRisk`、`GetAssetAllocation`、`MonteCarloSimulate`、`GetPortfolioNavHistory`、`GetFundRelatedStrategies`、`StrategySearchByKeyword`、`GetStrategyDetails`、`GetStrategyRiskInfo`、`BatchGetStrategyRiskInfo`、`BatchGetStrategiesComposition`、`BatchGetPoTradeComposition`、`GetStrategyAssetClassAnalysis`、`GetStrategyBenchmark` |
| 财富规划与资产配置 | 家庭成员、收支、资产负债、现金流、配置测算 | `AnalyzeFamilyMembers`、`AnalyzeIncomeExpense`、`AnalyzeAssetLiability`、`AnalyzeCashFlow`、`AnalyzeFinancialIndicators`、`GetAssetAllocationPlan`、`GetCompositeModel`、`AnalyzeInvestmentPerformance` |
| 基金筛选与排雷 | 选基、债基排雷、按条件筛选基金 | `filterBondFundByBondType`、`filterBondFundByCreditRating`、`filterStockFundByStockTurnover` |
| 市场资讯与素材 | 行情、财经资讯、热点、基金经理观点、投顾素材 | `GetLatestQuotations`、`SearchFinancialNews`、`SearchHotTopic`、`SearchManagerViewpoint`、`searchInvestAdvisorContent`、`searchRealtimeAiAnalysis` |
| 图表与报告输出 | 渲染图表、图片或导出 PDF | `RenderEchart`、`RenderHtmlToPdf` |

## 工具与参数说明

### 基础时间能力

当前时间、交易日范围

#### `GetCurrentTime` — 获取当前时间

获取当前时间。注意，模型AI你是不知道当前时间的，需要调用此工具获取当前时间。

请求：`GET /common/current-time`

**参数说明**：无必填参数。

**最小调用示例**：

```json
{}
```

#### `GetTxnDayRange` — 交易日查询

以某时间为中心获取一个时间段内的交易日。centerTime：格式是YYYY-MM-DD HH:mm:ss，默认不填就是当前时间（建议大部分情况都不要填）

请求：`GET /common/getTxnDayRange`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |
| `centerTime` | string | - | query | 按工具 Schema 传入 |
| `beforeDays` | string | ✅ | query | 按工具 Schema 传入 |
| `afterDays` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "beforeDays": "<beforeDays>",
  "afterDays": "<afterDays>"
}
```

### 基金检索与资料

搜基金、确认代码、查详情、交易规则、分红与拆分历史

#### `SearchFunds` — 搜索基金

搜索基金、根据基金名称匹配基金代码。通过名称（可用于确定基金代码）、代码、拼音、交易状态等信息进行搜索。同时可以按照收益、限额、费率等进行排序。（注意如果使用了keyword，就不要使用“分类”这个参数，另外returnYear指的是近一年收益）

请求：`POST /fund/search`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 基金名称关键字，支持分词搜索 |
| `tradeStatus` | string | - | body | 交易状态 (可选值: '', '不限', '正常开放', '认购期', '暂停申购', '暂停赎回', '暂停交易')；默认："不限" |
| `category` | string | - | body | 分类 (可选值: '', '不限', '偏股型', '指数型', 'QDII型', '商品型', '债券型', '货币型', '国企改革', '工业4.0', '国防军工', '城镇化', '消费', '节能环保', '美丽中国', '养老', '价值蓝筹', '金融', '一带一路', '农林牧渔', '资源', 'TMT', '新能源', '文化传媒', '健康中国', '新兴产业', '量化投资', '定增', '逆向投资', '沪港深', '量化对冲', '打新', '股票型', '偏股混合型', '平衡混合型', '灵活配置型', '偏债混合型', '综合指数', '规模指数', … |
| `sortColumn` | string | - | body | 选择要排序的列，可选值：成立日期、基金规模、收益率、近一年收益、起购金额、基金限额、选股能力、择时能力、最新股票仓位、综合费率、跟踪误差、七日年化收益率、万份收益 |
| `sortOrder` | string | - | body | 选择排序的顺序，如果是查找最大、最多等，可以是"降序"，否则为"升序" (可选值: '', '升序', '降序')；默认："降序" |
| `page` | number | - | body | 页码，从0开始；默认：0 |
| `size` | number | - | body | 每页数量；默认：10 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `GuessFundCode` — 基金代码模糊匹配

根据基金名称匹配最相近的基金代码。

请求：`GET /fund/guess-code`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundNameOrCode` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundNameOrCode": "<fundNameOrCode>"
}
```

#### `BatchGetFundsDetail` — 批量获取基金详情

返回基金的详细信息，包括基本概况（最新净值，规模，基准，风险等级，基金类型）、经理信息、业绩表现、持仓分析、资产配置、行业分布、净值历史、交易限制等完整数据。

请求：`POST /fund/detail`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查20个。例如: ["100032","162411"] |

**最小调用示例**：

```json
{
  "fundCodes": []
}
```

#### `GetPopularFund` — 获取近期热门基金

返回近期访问数量前x的基金

请求：`GET /fund/popular`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `size` | number | - | query | 默认：6 |

**最小调用示例**：

```json
{}
```

#### `BatchGetFundTradeLimit` — 基金交易限制信息

批量获取基金交易限制信息，返回申购(allot)/认购(subscribe)/赎回/转换是否可用，以及起购金额、定投金额等；注意：认购不可用不等于申购不可用。

请求：`POST /fund/trade-limit`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查20个。例如: ["100032","162411"] |

**最小调用示例**：

```json
{
  "fundCodes": []
}
```

#### `BatchGetFundTradeRules` — 基金交易规则

查询特定交易时间进行的基金交易操作包含的交易规则信息。支持申购、认购、赎回和转换等操作类型，返回包含最低/最高购买金额、预计确认日期、到账日期、收益产生日期、费率规则等详细交易规则数据。尽量提供精确的txnTime，无法确定可以询问用户。

请求：`POST /fund/trade-rules`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查20个。例如: ["100032","162411"] |
| `op` | string | ✅ | body | 交易操作类型: allot - 申购, subscribe - 认购, redeem: 赎回 (可选值: 'subscribe', 'allot', 'redeem', 'convert') |
| `txnTime` | string | - | body | 交易时间，可选参数，支持两种格式：1. 仅日期格式(YYYY-MM-DD)如2024-12-30，将使用当天中午12点；2. 带时分秒格式(YYYY-MM-DD HH:mm:ss)如2024-12-30 13:00:00 |

**最小调用示例**：

```json
{
  "fundCodes": [],
  "op": "<op>"
}
```

#### `BatchGetFundsDividendRecord` — 基金分红记录

提供基金代码列表，批量返回基金分红记录，包括权益登记日、红利发放日和每份分红金额。单次最多查询 20 只基金。

请求：`POST /fund/dividend-record`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查 20 个。例如：`["100032", "162411"]` |

**最小调用示例**：

```json
{
  "fundCodes": ["100032", "162411"]
}
```

#### `BatchGetFundsSplitHistory` — 基金拆分记录

提供基金代码列表，批量返回基金拆分记录，包括拆分日期和拆分比例。单次最多查询 20 只基金。

请求：`POST /fund/split-info`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查 20 个。例如：`["100032", "162411"]` |

**最小调用示例**：

```json
{
  "fundCodes": ["100032", "162411"]
}
```

### 单只基金分析

业绩、风险、归因、行业、风格、债基指标

#### `GetFundDiagnosis` — 基金诊断

获取基金的诊断信息，包括风险评价、估值、业绩指标、盈利概率、行业分布、资产配置

请求：`GET /fund/diagnosis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundNameOrCode` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundNameOrCode": "<fundNameOrCode>"
}
```

#### `AnalyzeFundRisk` — 基金风险分析

基金风险分析接口，获取多个基金的风险评分及说明。该接口通过传入基金代码列表，返回每个基金的风险评分、R方值、残差方差、标准误差等风险指标，以及相应的风险描述文本。

请求：`POST /research/fund-risk-analyze`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundCodes": []
}
```

#### `GetBatchFundPerformance` — 批量获取基金业绩表现

批量返回基金业绩表现数据，包含业绩分析指标（收益能力、风险控制等）和阶段收益（近1月、近1年、成立以来等）的详细信息。支持一次查询多只基金的业绩对比，每次最多支持20只基金的查询。

请求：`POST /fund/performance`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查20个。例如: ["100032","162411"] |

**最小调用示例**：

```json
{
  "fundCodes": []
}
```

#### `BatchGetFundNavHistory` — 基金净值历史

批量返回基金历史净值，包括：单位净值、累计净值、日涨跌。

请求：`POST /fund/nav-history`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodes` | string[] | ✅ | body | 基金代码列表，单次最多查20个。例如: ["100032","162411"] |
| `isDesc` | boolean | - | body | 是否按时间倒叙。默认是倒叙；默认：true |
| `dimensionType` | string | - | body | 时间维度。对应字典中 key=navTimeDimensionType 的值 (可选值: 'oneMonth', 'quarter', 'halfYear', 'oneYear', 'twoYear', 'threeYear', 'fiveYear', 'thisYear', 'setupDay')；默认："oneMonth" |

**最小调用示例**：

```json
{
  "fundCodes": []
}
```

#### `GetFundAssetClassAnalysis` — 资产大类分布

用户会提供基金代码和基金的持有金额，该工具会根据用户提供的基金持仓信息，穿透分析用户的总体持仓的资产大类分布情况

请求：`POST /v2/internal/fund/asset-class-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `holdingList` | object[] | ✅ | body | 数组元素字段：fundCode、fundName、amount |

**最小调用示例**：

```json
{
  "holdingList": []
}
```

#### `getFundBenchmarkInfo` — 基金业绩基准

通过基金代码查询基金的业绩基准信息

请求：`GET /bmdj/v1/fund/benchmark-info/{fundCode}`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | path | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundBrinsonIndicator` — Brinson归因

获取基金股票收益归因（Brinson）数据，包括行业配置收益、选股收益和总超额收益

请求：`GET /bmdj/v1/fund/brinson/indicator`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | query | 按工具 Schema 传入 |
| `timePeriod` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundCampisiIndicator` — Campisi归因

获取基金债券收益归因（Campisi）数据，包括收入效应、国债效应、利差效应、券种选择效应和超额回报

请求：`GET /bmdj/v1/fund/campisi/indicator`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | query | 按工具 Schema 传入 |
| `timePeriod` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundIndustryAllocation` — 行业配置比例

获取指定基金在指定时间区间下所有中信一级行业的行业配置比例、行业代码和行业名称

请求：`POST /bmdj/v1/internal/fund-data/fund-industry-allocation`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | body | 基金代码，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundIndustryConcentration` — 基金行业持仓集中度

获取指定基金在指定时间区间下前5大中信一级行业的独立集中度，以及前1、2、3、5大行业集中度加总的数据

请求：`POST /bmdj/v1/internal/fund-data/fund-industry-concentration`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | body | 基金代码，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundIndustryPreference` — 基金行业偏好

获取指定基金在指定时间段内的行业偏好

请求：`POST /bmdj/v1/internal/fund-data/fund-industry-preference`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为近一年 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

#### `getFundIndustryReturns` — 行业收益

获取指定基金在指定时间区间下每个一级行业的行业名称、绝对收益、相对收益、收益率、收益率得分

请求：`POST /bmdj/v1/internal/fund-data/fund-industry-returns`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | body | 基金代码，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为近一年 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getFundTurnoverRate` — 基金换手率（调仓频率）

获取指定基金在指定时间区间下的换手率数据

请求：`POST /bmdj/v1/internal/fund-data/fund-turnover-rate`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | body | 基金代码，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为近一年 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `fund-equity-position` — 权益仓位偏好

获取基金的权益仓位数据，包括权益仓位值和权益仓位等级名称

请求：`GET /bmdj/v1/fund/equity-position/position`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `fund-recovery-ability` — 回撤修复能力

获取基金的回撤修复能力数据，根据近三年最长恢复天数排名确定修复水平

请求：`GET /bmdj/v1/fund/recovery-ability/ability`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `fund-sector-preference` — 基金板块偏好

获取基金的板块配置偏好数据，包括基金主板块对应的行业名称和行业编号

请求：`GET /bmdj/v1/fund/sector-preference/preference`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `getMarketTimingIndicator` — 权益仓位择时

获取基金的择时相关指标数据，包括择时总胜率、择时贡献等

请求：`GET /bmdj/v1/fund/market-timing/indicator`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |
| `timeInterval` | string | - | query | 可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'fromSetupDate', 'sinceTakingOffice'；默认："LAST_YEAR" |

**最小调用示例**：

```json
{}
```

#### `getStockAllocationAndMetricsByFundCode` — 估值盈利指标（市盈率/市净率/净资产收益率）

获取指定股票型基金的股票配置、估值盈利指标、财务指标和抱团股数据

请求：`POST /bmdj/v1/internal/fund-data/fund-stock-allocation`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数，最多50个 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `holdingType` | string | - | body | 持仓类型，可选参数，默认为全持仓(semiannual)。可选值：semiannual(全持仓)、quarter(重仓股) (可选值: 'semiannual', 'quarter') |
| `calculationMethod` | string | - | body | 计算规则，可选参数，默认为持仓比例加权(wavg)。可选值：avg(算术平均加权)、wavg(持仓比例加权)、float_wavg(流通市值加权)、integral(整体法) (可选值: 'avg', 'wavg', 'float_wavg', 'integral') |
| `threshold` | number | - | body | 抱团阈值，可选参数，默认为15(前15%)。可选值：10(前10%)、15(前15%)、20(前20%)、25(前25%)、30(前30%) |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

#### `getQdFundAreaAllocation` — QDII地区配置

获取指定QDII基金在指定时间区间下的地区配置比例数据

请求：`POST /bmdj/v1/internal/fund-data/fund-area-allocation`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数，最多50个 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `scope` | string | - | body | 地区编码，非必传，如果没有传就返回该基金所有地区的数据 |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

#### `getBondAllocationByFundCode` — 券种配置情况

获取指定债券型基金在指定时间区间下的券种配置和风格配置数据

请求：`POST /bmdj/v1/internal/fund-data/fund-bond-type`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数，最多50个 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `assetType` | string | - | body | 资产类型，可选参数，默认为净资产比(total_net_asset)。可选值：total_asset(总资产比)、total_net_asset(净资产比)、bond_asset(债券市值比) (可选值: 'total_asset', 'total_net_asset', 'bond_asset') |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

#### `getBondFundCreditRatingLevel` — 债基评级查询

获取指定基金在指定时间区间下的债券信用评级数据

请求：`POST /bmdj/v1/internal/fund-data/fund-bond-credit`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数，最多50个 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `sumRatingType` | string | - | body | 评级类型，可选参数 |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

#### `getBondIndicator` — 债基风险

获取基金的债券相关指标数据，包括敏感性久期、杠杆水平、债券持仓集中度等

请求：`GET /bmdj/v1/fund/bond/indicator`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | ✅ | query | 按工具 Schema 传入 |
| `timeInterval` | string | - | query | 可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'fromSetupDate', 'sinceTakingOffice'；默认："LAST_YEAR" |

**最小调用示例**：

```json
{
  "fundCode": "005827"
}
```

#### `getBondFundWithAlertRecord` — 查询发生净值异动的债基

查询出现异动和跳水告警的债券型基金

请求：`POST /bmdj/v1/internal/fund-data/bond-alert-query`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `bondAlterType` | string | - | body | 告警类型，可选参数，默认为dailyDive(日跳水)。可选值：unusual(异动)、dailyDive(日跳水)、weekDive(周跳水) (可选值: 'unusual', 'dailyDive', 'weekDive') |
| `divingThreshold` | number | - | body | 跳水阈值，可选参数。日跳水默认-0.005，周跳水默认-0.01。日跳水阈值范围：-0.0005, -0.001, -0.0015, -0.002, -0.0025, -0.0035, -0.005, -0.0075, -0.01；周跳水阈值范围：-0.0025, -0.0035, -0.005, -0.0075, -0.01, -0.0125, -0.015, -0.02, -0.025, -0.03 |
| `maxResultSize` | number | - | body | 最大返回记录数，可选参数，默认50条，上限200条 |

**最小调用示例**：

```json
{
  "bondAlterType": "<bondAlterType>"
}
```

#### `getFundDiveCount` — 债基异动

获取指定基金在指定时间段内的跳水次数和异动次数

请求：`POST /bmdj/v1/internal/fund-data/fund-dive-count`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCodeList` | string[] | ✅ | body | 基金代码列表，必传参数 |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为近一年 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |

**最小调用示例**：

```json
{
  "fundCodeList": []
}
```

### 组合与策略

多基金组合、相关性、回测、风险、穿透配置、策略查询

#### `GetFundsCorrelation` — 基金相关性分析

获取基金相关性分析结果。只需提供基金列表，只返回基金相关性分析结果。该接口分析多只基金之间的相关性系数，生成雷达图评分和诊断结果，帮助进行投资组合分析。

请求：`POST /research/correlation`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundList` | object[] | ✅ | body | 基金列表；数组元素字段：fundCode |

**最小调用示例**：

```json
{
  "fundList": []
}
```

#### `GetFundsBackTest` — 回测分析

基于基金列表进行回测分析。只需提供基金列表，返回回测分析结果。该接口用于对给定基金组合进行回测分析，计算包括年化收益率、最大回撤、波动率、夏普比率等指标，并提供诊断结果和雷达图评分。（注意不要提供fundName）

请求：`POST /research/backtest`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundList` | object[] | ✅ | body | 基金列表；数组元素字段：fundCode、fundName、amount |

**最小调用示例**：

```json
{
  "fundList": []
}
```

#### `DiagnoseFundPortfolio` — 账户诊断

获取用户当前基金持仓的全面分析评估，包括资产配置状况、基金间相关性和历史回测表现。报告从风险分散度、资产类别分布和收益表现三个维度进行评分（1-5分）及诊断，并提供相应优化建议。 分析内容包括： 资产配置：评估当前资产类别分布合理性，提供多元化配置建议 相关性分析：计算各基金间相关系数，评估风险分散程度 回测表现：模拟当前配置在历史期间的表现，包括年化收益率、最大回撤、波动率等关键指标

请求：`POST /research/diagnose-funds-account`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundList` | object[] | ✅ | body | 基金列表；数组元素字段：fundCode、fundName、amount |

**最小调用示例**：

```json
{
  "fundList": []
}
```

#### `AnalyzePortfolioRisk` — 投后风险分析

组合风险评估接口，计算组合的风险指标。该接口接收基金代码和权重信息，返回包含风险评分、R方、残差方差等多维度风险指标的分析结果。

请求：`POST /research/portfolio-risk-analyze`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `holdings` | object[] | ✅ | body | 数组元素字段：weight、fundCode |

**最小调用示例**：

```json
{
  "holdings": []
}
```

#### `GetAssetAllocation` — 资产配置分析

获取基金组合的资产配置分析结果，只需提供基金列表，只返回资产配置分析结果。该接口分析用户的资产配置情况，包括雷达图评分、诊断结果、资产大类配置详情及子账户资产配置分析（注意不需要提供fundName）

请求：`POST /research/asset-allocation`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundList` | object[] | ✅ | body | 基金列表；数组元素字段：fundCode、fundName、amount |

**最小调用示例**：

```json
{
  "fundList": []
}
```

#### `MonteCarloSimulate` — 组合预期收益测算（蒙特卡洛）

针对资产配置组合进行蒙特卡洛模拟计算（测算未来收益概率）。接收对象形式的资产权重配置，返回蒙特卡洛模拟结果。该接口基于提供的资产配置权重，执行蒙特卡洛模拟计算，生成不同投资周期的预期收益分布、波动率情景和各种百分位数的收益率数据，并提供语义化描述和可视化图表（可以用markown image显示）。

请求：`POST /research/monte-carlo-simulate`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `weights` | object | ✅ | body | 资产权重对象，包含六大类资产权重配置；子字段：cash、fixedIncome、equity、commodity、overseasEquity、overseasFixedIncome |
| `frequency` | string | - | body | 模拟周期频率，可选值: YEAR(年度)、MONTH(月度)、WEEK(周度)、DAY(日度) |
| `periodCount` | number | - | body | 周期长度（年），最小值: 1 |
| `simulationCount` | number | - | body | 模拟次数，最小值: 1000 |

**最小调用示例**：

```json
{
  "weights": {}
}
```

#### `GetPortfolioNavHistory` — 组合历史净值

组合历史净值，poManagerId、broker都不需要填。

请求：`GET /model/{poCode}/navHistory`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `poCode` | string | ✅ | path | 按工具 Schema 传入 |
| `start` | string | - | query | 默认："" |
| `end` | string | - | query | 默认："" |
| `poManagerId` | integer | - | query | 默认：-1 |
| `brokerCode` | string | - | query | 默认："" |
| `noACL` | boolean | - | query | 默认：false |

**最小调用示例**：

```json
{
  "poCode": "<poCode>"
}
```

#### `GetFundRelatedStrategies` — 按重仓基金筛选投顾策略

输入基金代码或基金名称，查询重仓该基金的投顾策略

请求：`GET /v2/internal/strategy/fund-related`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `fundCode` | string | - | query | 按工具 Schema 传入 |
| `fundName` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `StrategySearchByKeyword` — 策略关键词搜索

根据关键词模糊搜索组合策略名称，返回匹配的组合策略信息列表。支持分页查询，可指定页码和每页记录数。工具结果里的「策略代码」可用于提供给其他工具作为入参使用。

请求：`GET /oap/api/v1/strategy/search/keyword`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | ✅ | query | 按工具 Schema 传入 |
| `pageNum` | integer | - | query | 默认：1 |
| `pageSize` | integer | - | query | 默认：20 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `GetStrategyDetails` — 策略详情查询

组合策略详情查询. 根据策略代码或名称获取组合策略的详细信息，包含策略基础信息、策略管理人信息、风险收益指标、历史业绩、资产配置情况、投资特点等。

请求：`POST /oap/api/v1/strategy/details`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `pageSize` | integer | - | body | 每页返回记录数，默认20，最大100；默认：20 |
| `pageNum` | integer | - | body | 分页查询的页码，从 1 开始，默认 1；默认：1 |
| `strategyCodes` | string[] | ✅ | body | 可使用组合搜索工具StrategySearchByKeyword，确定组合的代码 |

**最小调用示例**：

```json
{
  "strategyCodes": []
}
```

#### `GetStrategyRiskInfo` — 策略风险

获取某个策略的风险信息

请求：`GET /v2/internal/strategy/risk-info`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCode` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "strategyCode": "<strategyCode>"
}
```

#### `BatchGetStrategyRiskInfo` — 策略风险匹配

获取一批策略风险信息

请求：`POST /v2/internal/strategy/batch-risk-info`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCodes` | string[] | ✅ | body | 策略代码数组 |

**最小调用示例**：

```json
{
  "strategyCodes": []
}
```

#### `BatchGetStrategiesComposition` — 批量查询策略持仓

根据策略代码批量获取组合策略的当前持仓明细信息，包含各基金的持仓比例、净值信息、分类分组及最新调整情况等

请求：`POST /oap/api/v1/strategy/composition`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCodes` | string[] | - | body | 可使用组合搜索工具StrategySearchByKeyword，确定组合的代码 |

**最小调用示例**：

```json
{
  "strategyCodes": []
}
```

#### `BatchGetPoTradeComposition` — 策略交易成分

根据策略代码列表批量获取交易成分明细信息

请求：`POST /oap/api/v1/strategy/trade-composition`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCodes` | string[] | - | body | 可使用组合搜索工具StrategySearchByKeyword，确定组合的代码 |

**最小调用示例**：

```json
{
  "strategyCodes": []
}
```

#### `GetStrategyAssetClassAnalysis` — 策略大类资产分布

获取策略持仓穿透后的资产大类分布情况

请求：`GET /v2/internal/strategy/asset-class-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCode` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "strategyCode": "<strategyCode>"
}
```

#### `GetStrategyBenchmark` — 查询策略业绩基准

根据策略代码获取策略的业绩基准信息

请求：`GET /v2/internal/strategy/benchmark`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `strategyCode` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "strategyCode": "<strategyCode>"
}
```

### 财富规划与资产配置

家庭成员、收支、资产负债、现金流、配置测算

#### `AnalyzeFamilyMembers` — 家庭结构分析

AI专用家庭成员分析接口，接收家庭成员列表数据，返回详细的家庭成员分析结果。该接口可分析家庭总人数、成年人数、未成年人数及家庭所处生命周期阶段等信息，帮助进行家庭财务规划。

请求：`POST /v1/internal/financial-planning/family-member-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `familyMembers` | object[] | ✅ | body | 家庭成员列表；数组元素字段：role、name、gender、birthDate、ageDescription、occupation、residenceCity |

**最小调用示例**：

```json
{
  "familyMembers": []
}
```

#### `AnalyzeIncomeExpense` — 收入支出分析接口

AI专用收入支出分析接口，接收收入支出数据，返回详细的收入支出分析结果。该接口处理用户的年度收入和支出数据，计算总收入、总支出、年度结余及各收支项目的占比分析，同时提供月度必要性支出数据，用于财务规划和预算管理。

请求：`POST /v1/internal/financial-planning/income-expense-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `annualIncome` | object | ✅ | body | 年收入；子字段：otherIncome、businessIncome、investmentIncome、housingFundWithdrawal、rentalIncome、bonus、salary |
| `annualExpense` | object | ✅ | body | 年支出；子字段：otherExpenses、travelExpenses、medicalExpenses、educationExpenses、insurancePremium、parkingLoanPayment、carLoanPayment、mortgagePayment、transportation、utilityBills、dailyExpenses |

**最小调用示例**：

```json
{
  "annualIncome": {},
  "annualExpense": {}
}
```

#### `AnalyzeAssetLiability` — 资产负债分析

AI专用资产负债分析接口，接收用户资产负债数据，进行全面分析并返回详细的资产负债分析结果，包含资产负债比率、净资产、各类资产和负债的详细分析报告

请求：`POST /v1/internal/financial-planning/asset-liability-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `totalAssets` | object | ✅ | body | 总资产；子字段：personalUseAssets、investmentAssets、liquidAssets |
| `totalLiabilities` | object | ✅ | body | 总负债；子字段：personalUseLiabilities、investmentLiabilities、currentLiabilities |

**最小调用示例**：

```json
{
  "totalAssets": {},
  "totalLiabilities": {}
}
```

#### `AnalyzeCashFlow` — 现金流分析与财务规划

AI专用现金流分析接口，接收家庭现金流数据（包括当前可投资产、报酬率配置、家庭成员信息、持续性和一次性收支）作为输入，计算并返回详细的现金流分析结果，包括汇总信息、年度数据、HTML表格和数据解释提示。该接口专为大模型处理和展示现金流数据而设计。

请求：`POST /v1/internal/financial-planning/cash-flow-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `currentInvestableAssets` | number | ✅ | body | 当前可投资产 |
| `returnRateConfig` | object[] | ✅ | body | 报酬率配置；数组元素字段：startAge、endAge、rate |
| `familyMembers` | object[] | ✅ | body | 家庭成员信息；数组元素字段：role、name、initialAge |
| `continuousIncome` | object[] | ✅ | body | 家庭持续性收入；数组元素字段：startAge、endAge、incomeType、growthRate、amount |
| `continuousExpenses` | object[] | ✅ | body | 家庭持续性支出；数组元素字段：startAge、endAge、expenseType、inflationRate、amount |
| `oneTimeIncome` | object[] | ✅ | body | 家庭一次性收入；数组元素字段：startAge、endAge、incomeType、amount |
| `oneTimeExpenses` | object[] | ✅ | body | 家庭一次性支出；数组元素字段：startAge、endAge、expenseType、amount |

**最小调用示例**：

```json
{
  "currentInvestableAssets": 0,
  "returnRateConfig": [],
  "familyMembers": [],
  "continuousIncome": [],
  "continuousExpenses": [],
  "oneTimeIncome": [],
  "oneTimeExpenses": []
}
```

#### `AnalyzeFinancialIndicators` — 财务状况分析

AI专用财务指标分析接口，接收财务指标输入数据(总资产、总负债、流动性资产等)，计算7个关键财务指标(资产负债率、流动比率、融资比率等)，并提供每个指标的合理范围与状态评估

请求：`POST /v1/internal/financial-planning/financial-indicator-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `totalAssets` | number | ✅ | body | 总资产 |
| `totalLiabilities` | number | ✅ | body | 总负债 |
| `liquidAssets` | number | ✅ | body | 流动性资产 |
| `currentLiabilities` | number | ✅ | body | 流动性负债 |
| `investmentAssets` | number | ✅ | body | 投资性资产 |
| `investmentLiabilities` | number | ✅ | body | 投资性负债 |
| `annualIncome` | number | ✅ | body | 年收入 |
| `annualExpense` | number | ✅ | body | 年支出 |
| `annualInvestmentIncome` | number | ✅ | body | 年投资收入 |
| `monthlyEssentialExpense` | number | ✅ | body | 月必要性现金流出（由其他接口直接提供） |

**最小调用示例**：

```json
{
  "totalAssets": 0,
  "totalLiabilities": 0,
  "liquidAssets": 0,
  "currentLiabilities": 0,
  "investmentAssets": 0,
  "investmentLiabilities": 0,
  "annualIncome": 0,
  "annualExpense": 0,
  "annualInvestmentIncome": 0,
  "monthlyEssentialExpense": 0
}
```

#### `GetAssetAllocationPlan` — 获取资产配置方案

根据投资三性参数获取资产配置方案。提供预期年化收益率 or 预期最大回撤 or 预期投资期限，获得由盈米设计的资产配置方案，投资三性参数最少要传一个。

请求：`GET /invest-plan/asset-allocation-plan`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `expectedAnnualizedReturnRate` | number | - | query | 按工具 Schema 传入 |
| `expectedInvestTime` | string | - | query | 预期投资期限枚举类型 spare - 活期 oneYear - 1年以内 oneToThree - 1-3年 threeToFive - 3-5年 overFive - 5年以上 (可选值: 'spare', 'oneYear', 'oneToThree', 'threeToFive', 'overFive') |
| `expectedDrawdown` | number | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `GetCompositeModel` — 获取基金投资方案

通过资产配置方案ID获取对应的复合模型 复合模型是资产配置方案的具体落地实现，提供每个大类资产对应的实际基金及其配置比例

请求：`GET /invest-plan/composite-model`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `assetPlanId` | string | ✅ | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{
  "assetPlanId": "<assetPlanId>"
}
```

#### `AnalyzeInvestmentPerformance` — 投资方案表现分析

AI专用投资方案表现判断接口，接收投资方案配置数据，返回详细的投资方案表现分析结果。该接口分析投资方案的可行性，计算加权收益率，并生成配置方案权重分析，帮助用户评估投资策略是否符合预期。

请求：`POST /v1/internal/financial-planning/investment-performance-analysis`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `totalInvestableAssets` | number | ✅ | body | 可投入资产总额 |
| `expectedReturnRate` | number | - | body | 期望报酬率 (小数形式，如0.04表示4%) 来源优先级： 1. 用户自定义提供的期望报酬率 2. 从现金流分析模块获取的报酬率配置 3. 系统默认值0.04 (4%) |
| `shortMediumTermScheme` | object | ✅ | body | 中短期配置方案；子字段：type、investmentAmount、annualReturn |
| `mediumLongTermScheme` | object | - | body | 中长期配置方案（可选，投资金额 <= 0时不需要做中长期配置）；子字段：type、investmentAmount、annualReturn |

**最小调用示例**：

```json
{
  "totalInvestableAssets": 0,
  "shortMediumTermScheme": {}
}
```

### 基金筛选与排雷

选基、债基排雷、按条件筛选基金

#### `filterBondFundByBondType` — 券种风格筛选基金

根据券种风格条件筛选符合条件的债券基金

请求：`POST /bmdj/v1/internal/fund-data/filter-bond-type`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `thresholdList` | number[] | ✅ | body | 阈值集合，必传参数。当operator为eq/lt/gt/lte/gte时，传入一个值；当operator为between时，传入两个值[最小值,最大值] |
| `operator` | string | - | body | 操作符，可选参数。可选值：eq(等于)、lt(小于)、gt(大于)、lte(小于等于)、gte(大于等于)、between(介于) (可选值: 'eq', 'lt', 'gt', 'lte', 'gte', 'between') |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `reportDate` | string | - | body | 报告期，可选参数，格式如：2024.03.31 |
| `bondType` | string | - | body | 债券类型，可选参数。可选值：national(国债)、financial(金融债)、corporate(企业债)、acd(同业存单)、localGovernment(地方政府债)、centralBank(央行票据)、shortTerm(短期融资券)、mediumTerm(中期票据)、other(其他债券)、convertible(可转债)、interestRate(利率债)、credit(信用债) (可选值: 'national', 'financial', 'corporate', 'acd', 'localGovernment', 'centralBank', 'shortTerm', … |
| `assetType` | string | - | body | 资产类型，可选参数，默认为净资产比(totalNetAsset)。可选值：totalAsset(总资产比)、totalNetAsset(净资产比)、bondAsset(债券市值比) (可选值: 'totalAsset', 'totalNetAsset', 'bondAsset') |
| `maxResultSize` | number | - | body | 最大返回记录数，可选参数，默认50条，上限200条 |

**最小调用示例**：

```json
{
  "thresholdList": []
}
```

#### `filterBondFundByCreditRating` — 根据信用评级筛选基金

根据信用评级条件筛选符合条件的基金

请求：`POST /bmdj/v1/internal/fund-data/filter-bond-credit`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `thresholdList` | number[] | ✅ | body | 阈值集合，必传参数。当operator为eq/lt/gt/lte/gte时，传入一个值；当operator为between时，传入两个值[最小值,最大值] |
| `operator` | string | - | body | 操作符，可选参数。可选值：eq(等于)、lt(小于)、gt(大于)、lte(小于等于)、gte(大于等于)、between(介于) (可选值: 'eq', 'lt', 'gt', 'lte', 'gte', 'between') |
| `timeRange` | string | - | body | 时间区间枚举字符串，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `reportDate` | string | - | body | 报告期，可选参数，格式如：2024.03.31 |
| `sumRatingType` | string | - | body | 评级类型，可选参数。如：短期A-1、长期AAA、长期未评级、短期未评级、长期AAA以下、短期A-1以下 |
| `assetType` | string | - | body | 资产类型，可选参数，默认为净资产比(totalNetAsset)。可选值：totalAsset(总资产比)、totalNetAsset(净资产比)、bondAsset(债券市值比) (可选值: 'totalAsset', 'totalNetAsset', 'bondAsset') |
| `maxResultSize` | number | - | body | 最大返回记录数，可选参数，默认50条，上限200条 |

**最小调用示例**：

```json
{
  "thresholdList": []
}
```

#### `filterStockFundByStockTurnover` — 股票换手率筛选基金

根据股票换手率指标筛选基金

请求：`POST /bmdj/v1/internal/fund-data/filter-fund-stock-turnover`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `thresholdList` | number[] | ✅ | body | 阈值集合，必传参数。当操作符为eq/lt/gt/lte/gte时，只需传入一个值；当操作符为between时，需传入两个值[最小值,最大值] |
| `operator` | string | - | body | 操作符，可选参数。可选值：eq(等于)、lt(小于)、gt(大于)、lte(小于等于)、gte(大于等于)、between(介于) (可选值: 'eq', 'lt', 'gt', 'lte', 'gte', 'between') |
| `timeRange` | string | - | body | 时间区间，可选参数，默认为最新报告期 (可选值: 'LAST_3_MONTH', 'LAST_6_MONTH', 'LAST_9_MONTH', 'LAST_YEAR', 'LAST_2_YEAR', 'LAST_3_YEAR', 'LAST_5_YEAR', 'LatestReportDate', 'fromSetupDate', 'sinceTakingOffice') |
| `reportDate` | string | - | body | 报告期，可选参数，格式：yyyy.MM.dd |
| `maxResultSize` | number | - | body | 最大返回记录数，可选参数，默认50条，上限200条 |

**最小调用示例**：

```json
{
  "thresholdList": []
}
```

### 市场资讯与素材

行情、财经资讯、热点、基金经理观点、投顾素材

#### `GetLatestQuotations` — 市场温度计

分析市场行情，进行行情解读，分析各市场当日收盘行情，市场温度计

请求：`GET /v2/internal/market/quotations/latest`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `calDate` | string | - | query | 按工具 Schema 传入 |

**最小调用示例**：

```json
{}
```

#### `SearchFinancialNews` — 财经资讯

根据关键词和时间范围搜索财经资讯内容，支持分页查询，返回符合条件的财经资讯列表，包括资讯标题、摘要、来源、链接及发布时间等信息。默认不需要提供date参数，除非用户明确要求。

请求：`POST /content/financial-news`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 搜索关键词 |
| `startDate` | string | - | body | 搜索开始日期 (YYYY-MM-DD) |
| `endDate` | string | - | body | 搜索结束日期 (YYYY-MM-DD) |
| `page` | integer | - | body | 页码 (默认: 1)；默认：1 |
| `pageSize` | integer | - | body | 每页数量 (默认: 20)；默认：20 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `SearchHotTopic` — 热点财经话题榜单

分析市场热点所在，聚焦大众关注、热度高的排行榜单内容。适用于：创作选题、视频脚本、营销文案创作等使用场景。当用户未指定关键词时，可不传keyword

请求：`POST /content/ranking/search-topic`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 搜索关键词,非必填 |
| `publishedDate` | string | - | body | 发布日期，格式为YYYY-MM-DD，默认为30天前 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `SearchManagerViewpoint` — 基金经理观点

根据时间范围和关键词搜索基金经理的行业观点及市场分析（如果用户问你对某个行业的看法，可以调用此工具进行参考）。支持按关键词匹配标题或内容，可筛选特定时间段内的观点，并提供分页功能。

请求：`POST /content/industry-viewpoint`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 搜索关键词，用于匹配标题或观点内容 |
| `startDate` | string | - | body | 搜索开始日期（YYYY-MM-DD） |
| `endDate` | string | - | body | 搜索结束日期（YYYY-MM-DD） |
| `page` | integer | - | body | 页码；默认：1 |
| `pageSize` | integer | - | body | 每页记录数；默认：10 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `searchInvestAdvisorContent` — 搜索投顾内容

搜索金融领域的文章、观点、话题和讨论内容，支持按关键词、基金组合、主理人/作者、时间范围和内容类型（文章、碎碎念、专栏、社区、策略内容等）进行筛选。

请求：`POST /content/invest-advisor-content`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 搜索关键词 |
| `author` | string | - | body | 作者名称筛选 |
| `startDate` | string | - | body | 搜索开始日期 (YYYY-MM-DD) |
| `endDate` | string | - | body | 搜索结束日期 (YYYY-MM-DD) |
| `page` | integer | - | body | 分页页码；默认：1 |
| `pageSize` | integer | - | body | 每页记录数；默认：20 |
| `type` | string | - | body | 内容类型筛选 (可选值: '文章', '碎碎念', '专栏', '社区', '自有策略的内容')。注：'碎碎念'是盈米社区大V发布的帖子，包含金融市场观点、投资心得、财经话题讨论等金融领域的信息分享，实时性更强。建议：尽量指定类型搜索，这样内容就不会混杂 |
| `skip_attachment` | boolean | - | body | 是否跳过附件；默认：false |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

#### `searchRealtimeAiAnalysis` — 实时资讯AI解读

根据时间范围、关键词搜索AI生成的实时资讯解读内容，支持分页查询

请求：`POST /content/ai-analysis/search`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `keyword` | string | - | body | 搜索关键词，用于在标题、内容和扩展信息中进行模糊匹配 |
| `startDate` | string | - | body | 搜索开始日期，格式为YYYY-MM-DD。如果不提供，默认为7天前 |
| `endDate` | string | - | body | 搜索结束日期，格式为YYYY-MM-DD。如果不提供，默认为当前日期 |
| `page` | integer | - | body | 页码，从1开始；默认：1 |
| `pageSize` | integer | - | body | 每页记录数，最大100；默认：20 |

**最小调用示例**：

```json
{
  "keyword": "<keyword>"
}
```

### 图表与报告输出

渲染图表、图片或导出 PDF

#### `RenderEchart` — ECharts图表渲染

根据提供的 ECharts 配置和尺寸参数，渲染图表并转换为图片，返回图片的 URL。

请求：`POST /tool/render/echart`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `option` | string | - | body | ECharts配置，支持JSON字符串或JavaScript代码 |
| `width` | string | - | body | 图表宽度，单位px，比如800表示800px；默认："800" |
| `height` | string | - | body | 图表高度，单位px，比如600表示600px；默认："600" |
| `devicePixelRatio` | number | - | body | 设备像素比；默认：1 |

**最小调用示例**：

```json
{
  "option": "<option>"
}
```

#### `RenderHtmlToPdf` — HTML转PDF

将HTML内容转换为PDF文档，支持自定义页面格式、背景打印和页边距设置，并返回访问URL（可以使用markdown的链接语法显示这个URL供用户点击）

请求：`POST /tool/render/render-pdf`

| 参数 | 类型 | 必填 | 位置 | 说明 |
| --- | --- | :---: | --- | --- |
| `html` | string | - | body | HTML内容 |
| `options` | object | - | body | 子字段：format、printBackground、margin |

**最小调用示例**：

```json
{
  "html": "<html>"
}
```

## 通用错误处理

- **找不到工具**：重新读取实时 Tool 列表，不猜工具名。
- **参数错误**：重新读取目标 Tool Schema，检查字段、类型、枚举和必填项。
- **对象不明确**：请用户确认基金代码、策略名称、日期范围或其他唯一标识。
- **数据为空**：说明查询对象、日期范围和空结果，不用其他数据代替。
- **认证失败**：提示用户检查盈米 MCP 开通状态及 API Key 配置，不要求用户在对话中发送密钥。
- **服务超时**：保留脱敏错误摘要，稍后重试，避免连续重复调用。

## 认证与风险提示

用户需要访问 https://qieman.com/mcp，登录且慢账号并开通服务，获取个人 API Key。API Key 由 WorkBuddy Connector 配置注入，不得写入 Skill、公开文件、日志或最终回答。

本服务提供的功能和资讯仅供参考。涉及金融、投资等需要特定资质或牌照的对客服务时，使用者须依法取得相应资质。使用结果前应核验数据日期、统计口径和关键结论，不构成收益承诺。
