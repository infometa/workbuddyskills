---
name: morningstar-tools
description: 晨星数据工具使用指南——全球与中国基金/股票数据查询、筛选、持仓穿透、组合分析、分析师研究
version: "1.0.0"
author: "Morningstar China"
---

# Morningstar 数据工具使用指南

## 通用工作流
1. 全球产品查询先调用 morningstar-id-lookup-tool_v2 将代码/名称/ISIN 与数据点名称
   转换为晨星 ID，再调用其他 Global 工具；中国公募基金直接用 6 位基金代码调用国内工具。
2. 典型链路：筛选（getFilterFund / screener）→ 取数（getFund* / data）→
   研究解释（analyst-research / getFundStrategyAnalysis）→ 持仓与组合
   （fund-holdings / getFundFullHoldings / portfolio-analysis）。
3. 输出结论须附数据截止日与口径，并声明不构成投资建议。
4. 严禁编造数据：所有数字必须来自工具真实返回。

## Global 工具（7 个）

### morningstar-id-lookup-tool_v2　标识符转换（入口工具）
将投资品标识（名称/代码/ISIN）与数据点名称映射为晨星 ID。支持股票 ST、
ETF FE、开放式基金 FO、封闭式基金 FC、集合投资信托 CZ。优先用代码或 ISIN。

### morningstar-data-tool　结构化数据点提取
按 investment_ids × datapoint_ids 提取 500+ 结构化数据点，支持时间序列数据点
的 start_date / end_date 历史区间查询（须成对提供）。

### morningstar-screener-tool　条件筛选
在指定 universe（ST/FE/FO/FC/CZ）内按数据点条件筛选，条件为 AND 逻辑
（datapoint_id + operator[=,>,<] + value），OR 需拆多次调用合并。
每页最多 200 条，用 pagination_token 翻页。默认排序：FO 按规模降序，其余按晨星评级降序。

### morningstar-analyst-research-tool　分析师研究
按 investment_id 获取最新研究报告。股票：公允价值评估、正反方观点（Bulls Say /
Bears Say）、经济护城河、风险与不确定性、资本配置。基金/ETF：奖牌评级支柱
（Process / People / Parent / Performance / Price）。

### morningstar-articles-tool　市场评论与方法论
以自然语言问题检索晨星编辑团队 2022 年以来的市场评论、投资主题、个人理财与
官方方法论内容。content_filter 可选 Methodology / Thematic Research。
适合宏观解读与投教，不适合取具体数据点。

### morningstar-fund-holdings-tool　基金持仓穿透
按 investment_ids（最多 10 只）返回前 N 大持仓（10-100）及权重。
适用 FE/FO/FC/CZ。用户问"这只基金里有什么"必用本工具。

### morningstar-portfolio-analysis-tool　组合分析（X-Ray）
输入自定义组合（各持仓 morningstar_id + weight，合计 100%，最多 100 项，
现金用 CASH）或单只 fund_id，按 analysis_type 输出切片：资产配置、行业、
地区暴露、股票风格、固收风格/久期、重仓重叠（stock_intersection）、
前十持仓、滚动/年度回报、月度增长。

## 中国基金数据工具（15 个）

### fundReviewData

【基金点评专用】根据6位基金代码获取经过清洗和结构化处理的基金点评数据。【适用场景】当用户需要生成基金点评、撰写基金分析报告、或评价某只基金时，必须调用此工具。【不适用】当用户问基金的一些基础维度信息时，禁止调用本工具，可以使用 getFundBasicInfo【重要】必须实际调用此工具获取数据，严禁编造或假装返回基金数据。所有基金信息必须来自工具的真实返回结果，可直接用于点评内容生成。【不适用】此工具不适用于内部测试或原始数据验证，测…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |

### getFundProfile

【基金运作数据查询】获取基金的运作数据概况。返回基金的基本运作信息，包括基金名称、代码、成立日期、投资目标、投资策略、业绩比较基准、基金管理人、基金托管人等。【适用场景】用户询问某只基金的基本概况、运作信息、投资目标、业绩比较基准等时调用。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |

### getFundPerformance

【基金业绩数据查询】获取基金的业绩表现数据。返回基金的区间收益（近1周、1月、3月、6月、1年、3年、5年、成立以来等）、同类排名、晨星评级、净值等。返回基金的quarterlyReturns中有基金的季度业绩数据，包括基金，业绩基准，基金分类和基金分类百分排名等。【适用场景】用户询问某只基金的业绩表现、收益率、同类排名、晨星评级等时调用。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |

### getFundGrowthDataByDateRange

【业绩走势与最大回撤首选工具】获取基金指定日期区间内的业绩走势或最大回撤数据。通过 dataType 参数切换：'return' 获取累计收益曲线（业绩走势），'maxdd' 获取最大回撤曲线。【适用场景】用户问业绩走势、收益走势、表现怎么样、涨了多少、业绩曲线、回报走势时，dataType 传 'return'；用户问最大回撤、回撤走势、回撤幅度时，dataType 传 'maxdd'。包括但不限于：'近三年业绩走势'、'近半个月走势…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| startDate | string | ✅ |  |
| endDate | string | ✅ |  |
| dataType | string | ✅ |  |

### getFundRiskAndReturn

【风险与回报数据首选工具】获取基金的风险与回报数据点。数据来源包含两个部分： 1. fundRisk：来自 fundOverviewSnapshot 接口，包含基金的风险指标数据（标准差、最大回撤、夏普比率等）和同类平均对比数据； 2. fundAttributionInfo：来自 getFundBasicInfo 接口，包含基金的业绩归因数据（各时间段的投资回报、超额收益、配置效应、选股效应等）。【适用场景】用户问基金的波动率、最大回…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| timePeriod | string | ✅ |  |

### getFundFee

【基金费率与成本首选工具】获取基金的费率与成本数据。返回数据点：费用率、管理费、申购费率、赎回费率、隐性费用、显性费用、交易成本、换手率等。【适用场景】用户问基金费率、管理费、申购赎回费用、换手率、交易成本、隐性费用等费率相关数据时调用。【重要】必须实际调用此工具获取数据，严禁编造费率数据。【数据约束】回答时只能基于本工具返回的数据进行分析和解读，严禁补充任何工具未返回的数据点。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| timePeriod | string | ✅ |  |

### getFundFullHoldings

获取基金历史持仓数据。返回基金各报告期的持仓完整记录，包含持仓名称、权重占比(weight)、持股数量、行业归属等，可用于分析持仓变动趋势和风格漂移。【排序规则】本工具返回全量持仓数据，若用户需要前十大持仓，须按weight字段从大到小排序后取前10条返回。【报告期数量】可通过 periodCount 参数控制返回的报告期数量，默认返回全部报告期。【适用场景】用户问基金历史持仓变化、重仓股调仓记录、持仓集中度变化趋势时调用。【重要】必须…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| periodCount | integer | ✅ |  |

### getFundHoldingsStatistics

【基金持仓统计首选工具】获取基金的持仓统计数据。返回数据点：资产配置、行业权重、风格箱权重、换手率、债券分布、配置穿透等。【适用场景】用户问基金资产配置、行业分布、持仓风格、换手率、债券配置等持仓统计相关数据时调用。【重要】必须实际调用此工具获取数据，严禁编造持仓数据。【数据约束】回答时只能基于本工具返回的数据进行分析和解读，严禁补充任何工具未返回的数据点。【截取控制】holdingsPeriodCount 参数可限制 assetAll…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| timePeriod | string | ✅ |  |
| holdingsPeriodCount | integer | ✅ |  |

### getFundSizeAndInvestorReturn

【基金规模与投资者回报首选工具】获取基金的规模和投资者回报数据。返回数据包含两个部分： 1. fundSize：基金最新规模（单位：亿元） 2. investorReturn：投资者回报数据，包括：    - returnDate：数据日期    - threeYear/fiveYear/tenYear：各时间段的投资者回报（investorReturn）和基金总回报（totalReturn），均为比率形式    - cashFlows…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |


### getFundHolderStructure

【基金持有人结构首选工具】获取基金的持有人结构数据。返回数据包含三个部分： 1. fundHolder：来自 fundOverviewSnapshot 接口，包含基金经理人持有、高管持有、内部员工持有等持有人数据 2. fofOwners：来自 getFundBasicInfo 接口的 doVo 节点，包含 FOF 持有人数据 3. holderStructure：来自 getFundBasicInfo 接口的 operationVo …

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| periodCount | integer | ✅ |  |


### getFundStrategyAnalysis

【基金策略分析及经理展望首选工具】获取基金的策略分析及经理展望信息。此工具必须调用两次：第一次获取日期列表，第二次获取具体内容。【第一步】仅传 fundCode 调用，返回可用报告期日期列表（含 strategies 和 outlooks 的 date、isYearly）。【第二步】传入 fundCode、date、isYearly 调用，返回该期的策略和展望正文。【关键流程】1.先只传 fundCode 获取日期列表；2.如果用户已明…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |
| date | string | ✅ |  |
| isYearly | string | ✅ |  |

### getFundManagerFullInfo

【基金经理完整信息首选工具】获取基金的基金经理完整信息。返回数据点：基金经理管理信息、经理变更历史、经理标签、经理任期等。返回数据点中的currentManagedAllFunds是现管基金列表，previousManagedFunds是以前管理的基金列表。【适用场景】用户问基金经理信息、经理变更、经理任期、经理标签等时调用。【重要】必须实际调用此工具获取数据，严禁编造数据。【数据约束】回答时只能基于本工具返回的数据进行分析和解读，严禁…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| managerId | string | ✅ |  |
| timePeriod | string | ✅ |  |

### searchFundManagerByKeyword

【基金经理搜索】根据基金经理中文名称或关键词搜索匹配的基金经理，返回基金经理代码（managerId）、所任职基金公司等信息。【适用场景】搜索结果可用于后续调用 getFundManagerInfo 获取基金经理详细信息。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| keyword | string | ✅ |  |

### getCompanyInfo

【基金公司信息首选工具】获取基金的基金公司信息。返回数据点：基金公司基本信息、旗下基金、规模、评级等。返回数据点中的executiveChanges是基金公司高管变动数据，fundTransfer是基金转型的日期。【适用场景】用户问基金公司信息、基金公司规模、旗下基金等时调用。【重要】必须实际调用此工具获取数据，严禁编造数据。【数据约束】回答时只能基于本工具返回的数据进行分析和解读，严禁补充任何工具未返回的数据点。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundCode | string | ✅ |  |

### getFilterFund

【基金搜索/筛选器】当用户想要查找特定基金、筛选基金、或者查询某类基金的业绩、评级、规模等数据时，必须调用此工具。支持范围（例如"0~15.23"）、小于（例如"<22"）、大于（例如">22"）、精确匹配（例如"categoryId":"001"）和多值匹配（例如"companyName":["贝莱德基金","易方达基金"]）等格式。【重要】必须实际调用此工具获取数据，严禁编造基金列表或筛选结果。所有基金数据必须来自工具的真实返回结果…

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| fundFilterSearch | object | ✅ |  |

## 参数补充说明
- fundCode：6 位基金代码。
- dataType：'return' 累计收益曲线 / 'maxdd' 最大回撤曲线。
- getFundStrategyAnalysis 须两步调用：先仅传 fundCode 取日期列表，再传 date + isYearly 取正文。
- getFundManagerFullInfo 以 managerId 为入参，先经 searchFundManagerByKeyword 或基金经理字段获取。
- getFilterFund 的 fundFilterSearch 支持范围（"0~15.23"）、大小于（">22"）、精确与多值匹配。

## 注意事项
- 需用户完成晨星 OAuth 授权后使用；Token 过期时提示重新授权。
- 中国基金优先走中国基金数据工具；跨市场/全球产品走 Global 工具。
- 涉及评级与研究结论必须注明晨星口径，禁止夸大表述。
