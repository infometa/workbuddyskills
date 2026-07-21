# 报告类型模板

## Type A: Acquirer Matching (卖方匹配)

### Use Case
Client is a sell-side company seeking potential acquirers.

### Standard Structure
1. 执行摘要（Executive Summary）— 逻辑概括，不放财务数据
2. 目标公司概况（Target Company Overview）
3. 收购方逐一分析（Acquirer Analysis）— 每家独立章节
   - 公司概况与战略动机
   - 财务能力评估
   - 协同效应分析
   - 交易可行性评估
4. 综合对比表（Comparative Analysis）
5. 交易建议（Deal Recommendations）

### Key Judgment Points
- 收购方排序逻辑（战略契合度 > 财务能力 > 协同效应）
- 估值方法选择（参考通用判断基准第1条：估值方法选择决策树）
- 跨境交易特殊考量

---

## Type B: Target Screening (买方标的筛选)

### Use Case
Client is a buy-side company seeking acquisition targets.

### Standard Structure
1. 买方概况与战略目标（Buyer Profile）
2. 行业分析（Industry Analysis）
3. 标的详细分析（Target Analysis）— 每家独立章节
4. 综合比较（Comparative Analysis）
5. 并购建议（M&A Recommendations）

### Key Judgment Points
- 标的筛选漏斗设计（参考跨场景框架：制造业出海标的筛选漏斗，如适用）
- 行业地图绘制逻辑
- 标的排序权重设计

---

## Type C: Valuation Report (估值报告)

### Use Case
Standalone valuation analysis for a company or transaction.

### Standard Structure
1. 数据假设（Data Assumptions）
2. 估值方法说明（Valuation Methodology）
3. 各方法明细（Method Details）
   - DCF Analysis
   - Comparable Companies
   - Precedent Transactions
   - LBO Analysis (if applicable)
4. 综合估值（Valuation Summary）— football field chart
5. 定价建议（Pricing Recommendation）

### Key Judgment Points
- 估值方法选择（严格参考通用判断基准第1条：估值方法选择）
- WACC参数选取
- 可比公司选择逻辑
- 溢价/折价调整

---

## Type D: Deal Structure Design (交易方案设计)

### Use Case
Design specific transaction structure for a deal.

### Standard Structure
1. 交易概览（Transaction Overview）
2. 战略逻辑（Strategic Rationale）
3. 估值定价（Valuation & Pricing）
4. 交易架构（Deal Architecture）
5. 监管合规（Regulatory Compliance）
6. 整合路线图（Integration Roadmap）

### Key Judgment Points
- 换股 vs 募资收购的区分（参考learnings）
- 早期方案不锁定具体时间节点和估值
- 不替对手方/合作方表态
- 监管先行设计（参考跨场景框架：港股重组监管先行设计，如适用）

---

## Type E: Industry Research (行业研究)

### Use Case
Deep-dive industry analysis for investment decisions.

### Standard Structure
1. 执行摘要（Executive Summary）
2. 宏观环境（Macro Environment）
3. 各目标市场分析（Market Analysis by Segment）
4. 竞争分析（Competitive Landscape）
5. TAM/SAM/SOM Analysis
6. 风险因素（Risk Factors）

### Key Judgment Points
- 行业地图框架选择
- 数据源选择与验证（参考公开数据纪律）
- TAM计算逻辑与假设

---

## Type F: HK Stock Restructuring Target Screening (港股重组标的筛选)

### Use Case
Screen HK-listed targets for shell/restructuring plays.

### Standard Structure
1. 执行摘要（Executive Summary）
2. 客户概况（Client Overview）
3. Top 1标的详细分析
4. Top 2标的详细分析
5. Top 3标的详细分析
6. 综合对比（Comparative Analysis）
7. 交易建议（Deal Recommendations）

### Key Judgment Points
- **停牌状态核实**是硬性要求
- 客户战略转向会使之前所有标的筛选结果失效
- 评分数学必须用脚本验证
- 壳价值评估逻辑（参考交易场景三：港股重组相关经验）

---

## Type G: HK Stock Asset Restructuring Plan (港股资产重组方案设计)

### Use Case
Design restructuring plan for HK-listed company asset restructuring.

### Standard Structure
1. 交易架构（Transaction Architecture）
2. 各方利益全景（Stakeholder Interest Map）
3. 监管合规（Regulatory Compliance）
4. 估值定价（Valuation & Pricing）
5. 资金安排（Funding Arrangement）
6. 风险评估（Risk Assessment）

### Key Judgment Points
- 监管先行设计（参考跨场景框架：港股重组监管先行设计）
- 各方利益平衡逻辑
- 资金闭环设计
- 联交所审批路径

---

## Common Rules Across All Types

### Prohibited
- Bullet point in investment logic sections (must use paragraph form)
- Em dash (—)
- "不是...而是..." sentence pattern
- Financial data in executive summaries (logic only)
- Fabricating any data

### Required
- Web search for latest market data (stock prices, market caps, etc.)
- Cross-reference with transaction experience reference before key decisions
- Backup files before editing (>20 lines: describe plan, wait for approval)
- Watermark on MAI proprietary research (8% opacity, #CCCCCC, "MAI | Date")
