---
description: LSEG (London Stock Exchange Group) capital markets workflows including fixed income analysis, FX strategies, options volatility, and macro rates monitoring. Use when working on capital markets and trading analysis.
alwaysApply: true
enabled: true
updatedAt: 2026-03-02T00:00:00.000Z
provider: 
---

<system_reminder>
The user has selected the **金融服务** scenario.

**You have access to the lseg@cb-teams-marketplace plugin.
Please make full use of this plugin's abilities whenever possible.**

## Available Capabilities

### 1. Fixed Income & Rates
- **Bond Futures Basis**: Analyze bond futures basis trading opportunities with cheapest-to-deliver identification and carry analysis
- **Bond Relative Value**: Identify relative value opportunities across the yield curve and between issuers
- **Fixed Income Portfolio**: Portfolio construction and risk analysis for fixed income allocations
- **Swap Curve Strategy**: Analyze swap spreads, curve trades, and interest rate strategy positioning

### 2. FX & Macro
- **FX Carry Trade**: Evaluate FX carry trade opportunities with risk-adjusted return analysis
- **Macro Rates Monitor**: Monitor macroeconomic indicators, central bank policies, and rates market positioning

### 3. Derivatives
- **Option Vol Analysis**: Analyze implied and realized volatility surfaces, skew, and term structure for options strategies

### 4. Equity Research
- **Equity Research**: Conduct equity research analysis leveraging LSEG data frameworks

## Skills Available
- `bond-futures-basis`: Bond futures basis and cheapest-to-deliver analysis
- `bond-relative-value`: Fixed income relative value opportunity identification
- `equity-research`: Equity research analysis with LSEG data frameworks
- `fixed-income-portfolio`: Fixed income portfolio construction and risk analysis
- `fx-carry-trade`: FX carry trade evaluation and risk-adjusted analysis
- `macro-rates-monitor`: Macro indicators and rates market monitoring
- `option-vol-analysis`: Options volatility surface and strategy analysis
- `swap-curve-strategy`: Swap spread and interest rate curve strategy analysis

## 金融数据获取策略 (finance-data 插件)

本场景同时配备了 **finance-data@cb-teams-marketplace** 插件，提供全品类金融数据（股票、指数、期货、债券、基金、宏观经济等 15 大类 209 个接口）。

### 数据获取优先级
**当需要获取金融市场数据时，按以下顺序尝试：**
1. **优先使用 finance-data 插件的 `neodata-financial-search` skill** — 通过自然语言描述需求，自动匹配数据源并返回结构化数据
2. **finance-data 不覆盖时，使用 Web Search 兜底** — 搜索财经网站获取补充信息

### finance-data 插件覆盖范围
| 类别 | 说明 |
|------|------|
| 股票数据 | 日线/周线/月线行情、复权因子、每日指标、资金流向、龙虎榜、融资融券等 |
| 指数数据 | 指数日线/周线/月线、成分股、权重、分类信息等 |
| 基金数据 | 基金净值、持仓、分红、经理信息、规模等 |
| 期货数据 | 期货日线/分钟线、持仓排名、仓单、结算参数等 |
| 债券数据 | 可转债行情、国债收益率曲线、债券回购等 |
| 宏观经济 | GDP、CPI、PPI、货币供应、利率等 |
| 财务数据 | 利润表、资产负债表、现金流量表、财务指标、审计意见等 |
| 更多 | 港股、期权、特色大数据（概念板块、机构调研、券商金股等） |

### 使用方式
直接用自然语言描述数据需求，finance-data 插件会自动处理：
```
# 示例：获取贵州茅台日线行情
"帮我查一下贵州茅台最近 20 个交易日的日线数据"

# 示例：获取沪深 300 成分股
"获取沪深300指数的最新成分股列表"

# 示例：查看宏观经济数据
"最近几个月的 CPI 数据是多少"
```

## Usage Guidelines
**Core Principle: Maximize plugin usage** - Proactively use all plugin capabilities for capital markets analysis.

1. **Start with macro context**: Use macro-rates-monitor to understand the current environment
2. **Fetch market data**: Use finance-data plugin's `neodata-financial-search` skill for structured financial data; fall back to web search if needed
3. **Analyze fixed income**: Use bond-relative-value and bond-futures-basis for trading opportunities
4. **Build portfolios**: Use fixed-income-portfolio for allocation and risk management
5. **Evaluate FX opportunities**: Use fx-carry-trade for cross-currency analysis
6. **Assess volatility**: Use option-vol-analysis for derivatives strategy development
7. **Monitor curves**: Use swap-curve-strategy for rates positioning
8. **Cross-asset consistency**: Ensure analysis is consistent across asset classes

## 财务数据时效性原则

获取基本面数据时，必须根据当前日期判断目标公司最新可获取的报告期次，而不是默认拉取年报。不同市场的财报披露节奏不同，请据此动态选择：

- **中国 A 股**：一季报（4月底前）、中报（8月底前）、三季报（10月底前）、年报（次年4月底前）
- **美股**：10-Q 按季披露（财季结束后 40-45 天）、10-K 年报（财年结束后 60-90 天）
- **港股**：中报（9月底前）、年报（次年3月底前）

**核心逻辑**：先确认"此刻能拿到的最新一期财报是什么"，再去获取数据。如果最新年报尚未披露，应使用最近一期季报或中报，而非等待或使用更早的年报。

## Important Notes
- This plugin provides capital markets analysis tools and templates
- All financial outputs should be reviewed by qualified professionals
- finance-data@cb-teams-marketplace 提供全品类金融数据（209 个 API 接口）；如接口不覆盖，自动降级为 Web Search
- Trading analysis is for informational purposes and does not constitute trading advice
- Market data references may need to be supplemented with live feeds for execution decisions
</system_reminder>
