---
name: yingmi-skill
description: 当用户需要查询基金、策略、公告、财经资讯，做资产配置、组合诊断、风险回测、现金流分析，或生成图表、PDF 时，优先使用本 Skill 获取真实数据与可执行能力。
description_zh: 基金查询、组合诊断、资产配置与财富规划的金融数据助手
description_en: Fund search, portfolio diagnosis, asset allocation & wealth planning assistant
version: 0.1.5
license: MIT
---

# yingmi-skill

本 Skill 是且慢金融能力的本地公开入口：负责完成前置检查、判断该用 MCP 还是云端子 Skill，并提供统一 HTML 报告模板入口。它不承载各金融场景的完整执行细节；进入子 Skill 后，应以远端子 Skill 的 `SKILL.md` 为准。

## 1. 前置检查

首次安装或执行任何 MCP / remote-skill 调用前，必须完成：

1. 环境检查：确认 `node -v`、`git --version` 可正常执行；缺失时先引导用户安装。
2. 执行 [CLI前置检查工作流](references/CLI前置检查.md)，确认 `yingmi-skill-cli` 已安装、已更新且环境已初始化。
3. 执行 `scripts/check-upgrade.sh` 检查 Skill 更新。

## 2. 决策原则：MCP 还是子 Skill

一句话判断：**MCP 是原子工具，云端子 Skill 是场景工作流。**

优先用 MCP：

- 用户只要一个明确数据点、指标、详情或单次输出。
- 用户已给出完整参数，不需要固定分析流程。
- 任务可以由一个或少量工具直接完成。

优先进入云端子 Skill：

- 用户要“分析、诊断、规划、评估、生成报告”。
- 任务需要多步编排、业务约束、固定章节或统一交付物。
- 用户明确指定了某个子 Skill 或明显命中下方场景清单。

补充规则：

- 已进入子 Skill 后，如仍需真实数据，继续按 MCP 的 `list -> schema -> call` 规则取数。
- 子 Skill 的章节、流程、字段、表格、图表和结论边界，全部以远端子 Skill 的 `SKILL.md` 为准。
- `design-data-visualization` 若只交付独立图表 / 单图 HTML，可不套完整报告壳；若交付完整报告页，仍遵守统一 HTML 模板。

## 3. MCP 原子能力

使用流程：

```bash
# 1. 查看工具列表
yingmi-skill-cli mcp list

# 2. 查看目标工具入参 Schema
yingmi-skill-cli mcp schema <toolName>

# 3. 按 Schema 调用工具
yingmi-skill-cli mcp call <toolName> --input '<json>'
```

常见示例：

```bash
yingmi-skill-cli mcp schema GetCurrentTime
yingmi-skill-cli mcp call GetCurrentTime --input '{}'

yingmi-skill-cli mcp schema SearchFunds
yingmi-skill-cli mcp call SearchFunds --input '{"keyword":"易方达蓝筹","size":3}'

yingmi-skill-cli mcp schema BatchGetFundsDetail GetFundDiagnosis GetFundsBackTest
```

能力分组仅用于快速路由；完整工具列表以 `yingmi-skill-cli mcp list` 的实时输出为准。

| 能力分组 | 什么时候使用 | 常用工具 |
| --- | --- | --- |
| 基础时间能力 | 当前时间、交易日范围 | `GetCurrentTime`、`GetTxnDayRange` |
| 基金检索与资料 | 搜基金、确认代码、查详情、公告、交易规则 | `SearchFunds`、`GuessFundCode`、`BatchGetFundsDetail`、`GetPopularFund`、`GetFundAnnouncements`、`GetAnnouncementContent`、`BatchGetFundTradeLimit`、`BatchGetFundTradeRules` |
| 单只基金分析 | 业绩、风险、持仓、归因、行业、风格、债基指标 | `GetFundDiagnosis`、`AnalyzeFundRisk`、`GetBatchFundPerformance`、`BatchGetFundNavHistory`、`BatchGetFundsHolding`、`GetFundAssetClassAnalysis`、`getFundBenchmarkInfo`、`getFundBrinsonIndicator`、`getFundCampisiIndicator`、`getFundIndustryAllocation`、`getFundIndustryConcentration`、`getFundIndustryPreference`、`getFundIndustryReturns`、`getFundTurnoverRate`、`fund-equity-position`、`fund-recovery-ability`、`fund-sector-preference`、`getMarketTimingIndicator`、`getStockAllocationAndMetricsByFundCode`、`getQdFundAreaAllocation`、`getBondAllocationByFundCode`、`getBondFundCreditRatingLevel`、`getBondIndicator`、`getBondFundWithAlertRecord`、`getFundDiveCount` |
| 组合与策略 | 多基金组合、相关性、回测、风险、穿透配置、策略查询 | `GetFundsCorrelation`、`GetFundsBackTest`、`DiagnoseFundPortfolio`、`AnalyzePortfolioRisk`、`GetAssetAllocation`、`MonteCarloSimulate`、`GetPortfolioNavHistory`、`GetFundRelatedStrategies`、`StrategySearchByKeyword`、`GetStrategyDetails`、`GetStrategyRiskInfo`、`BatchGetStrategyRiskInfo`、`BatchGetStrategiesComposition`、`BatchGetPoTradeComposition`、`GetStrategyAssetClassAnalysis`、`GetStrategyBenchmark` |
| 财富规划与资产配置 | 家庭成员、收支、资产负债、现金流、配置测算 | `AnalyzeFamilyMembers`、`AnalyzeIncomeExpense`、`AnalyzeAssetLiability`、`AnalyzeCashFlow`、`AnalyzeFinancialIndicators`、`GetAssetAllocationPlan`、`GetCompositeModel`、`AnalyzeInvestmentPerformance` |
| 基金筛选与排雷 | 选基、债基排雷、按条件筛选基金 | `filterBondFundByBondType`、`filterBondFundByCreditRating`、`filterStockFundByStockTurnover` |
| 市场资讯与素材 | 行情、财经资讯、热点、基金经理观点、投顾素材 | `GetLatestQuotations`、`SearchFinancialNews`、`SearchHotTopic`、`SearchManagerViewpoint`、`searchInvestAdvisorContent`、`searchRealtimeAiAnalysis` |
| 图表与报告输出 | 渲染图表、图片或导出 PDF | `RenderEchart`、`RenderHtmlToPdf` |

## 4. 云端子 Skill

使用流程：

```bash
# 1. 查看当前可用子 Skill
yingmi-skill-cli remote-skill list

# 2. 进入子 Skill，上下文名称必须以 list 输出为准
yingmi-skill-cli remote-skill enter <skillName>

# 3. 先读取远端子 Skill 说明，再执行后续任务
yingmi-skill-cli remote-skill exec --script 'cat SKILL.md'
```

约束：

- 下方清单只用于路由；真实可用名称以 `remote-skill list` 为准，不要凭目录名猜测。
- 进入后必须先读远端 `SKILL.md`，再按其要求执行。
- 本入口不规定子 Skill 内部“怎么做”，只说明“什么时候进入”。

| 子 Skill 目录 | 什么时候进入 |
| --- | --- |
| `fund-analyst` | 用户明确基金代码或名称，想知道“这只基金怎么样”、是否值得关注、同类对比等 |
| `portfolio-doctor` | 用户提供基金组合，想诊断是否合理、是否需要优化、风险收益是否匹配 |
| `fund-screener` | 用户不知道买什么，想筛选基金、推荐基金或排查问题基金 |
| `market-morning-brief` | 用户要市场早报、行情速报、热点汇总、基金经理观点摘要 |
| `advisor-content-studio` | 用户要写市场解读、基金推荐文案、投教内容、热点评论或内容排版 |
| `wealth-family-advisor` | 用户要做家庭财务规划、财务体检、收支梳理、退休目标或配置方案 |
| `wealth-goalmatch` | 用户不知道该设什么财富目标，希望推荐优先目标 |
| `wealth-goalcalc` | 用户要测算每月投多少、几年后有多少、目标能否达成 |
| `wealth-healthcheck` | 用户已有结构化财务数据，想快速计算健康指标和评级 |
| `wealth-report` | 用户已完成规划分析，接下来要生成完整书面报告 |
| `design-data-visualization` | 用户要做图表、仪表板、交互式可视化或导出 HTML / PNG / SVG / PDF |

## 5. 统一 HTML 报告模板

生成完整 HTML 报告页时，必须使用公共模板：

- 规范说明：[HTML视觉模板.md](references/HTML视觉模板.md)
- 公共模板：[demo-report.html](references/demo-report.html)

执行顺序：

1. 读取当前场景远端 `SKILL.md` 及其任务相关 `references/*`，确定报告内容、章节、字段和图表。
2. 读取 `demo-report.html` 全文，复用其视觉壳、整段 `<style>`、class、`report-header`、水印、主题切换脚本等。
3. 内容以场景 Skill 为准，视觉壳以 `demo-report.html` 为准。

禁止：未读模板即输出 HTML；照抄 demo 占位内容；自造整页 CSS / class；删除水印、顶栏图标或主题切换。
