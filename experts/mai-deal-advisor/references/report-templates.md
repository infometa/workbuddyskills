# 报告类型模板

## 默认产物

任何报告类型都先生成 `outputs/report-draft.md` 作为标准底稿，并同时生成 `outputs/report-qc.md` 记录已读取文件、来源状态、机器校验范围和待确认项。DOCX/PDF 只按 `references/file-intake-and-output.md` 作为可选衍生产物生成。

## Type A: Public Acquirer Candidate Framework (公开候选买方框架)

### Use Case
Client is a sell-side company building a public-information candidate universe for further validation.

### Standard Structure
1. 执行摘要（Executive Summary）— 逻辑概括，不放财务数据
2. 目标公司概况（Target Company Overview）
3. 公开候选方逐一分析（Candidate Analysis），每家独立章节
   - 公司概况与战略动机
   - 财务能力评估
   - 协同效应分析
   - 交易可行性评估
4. 综合对比表（Comparative Analysis）
5. 优先核查顺序与下一步补证

### Key Judgment Points
- 候选方优先核查逻辑（战略契合度、财务能力、协同效应和可验证性）
- 估值方法选择必须写明适用条件、数据来源和用户确认的关键假设
- 跨境交易特殊考量
- 公开候选买方框架不代表已匹配或已有交易意愿，不访问 MAI 私有买方网络

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
- 标的筛选漏斗必须基于用户确认的战略目标、地域、规模和交易可行性约束
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
   - Public Precedent Transactions（公开先例交易，仅使用可定位的公开交易资料）
   - LBO Analysis (if applicable)
4. 综合估值（Valuation Summary）— football field chart
5. 定价建议（Pricing Recommendation）

### Key Judgment Points
- 估值方法选择必须说明为什么适用于当前公司与交易场景
- WACC参数选取
- 可比公司选择逻辑
- 溢价/折价调整

---

## Type D: Deal Structure Options (交易结构备选方案)

### Use Case
Compare transaction structure options against the user's stated objectives and constraints.

### Standard Structure
1. 交易概览（Transaction Overview）
2. 战略逻辑（Strategic Rationale）
3. 估值定价（Valuation & Pricing）
4. 交易架构（Deal Architecture）
5. 监管合规（Regulatory Compliance）
6. 整合路线图（Integration Roadmap）

### Key Judgment Points
- 换股、现金收购与募资收购必须区分资金来源、稀释和控制权影响
- 早期方案不锁定具体时间节点和估值
- 不替对手方/合作方表态
- 涉及上市规则或收购守则时先列监管待确认项，不自动下法律结论
- 每个结构备选方案写清适用条件、利弊和待核查事项，最终结构由用户决定

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
- 评分数学必须用 `calculation_gate.py` 验证
- 壳价值评估必须列出公开来源、关键假设和监管不确定性

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
- 监管路径只形成待核查清单，关键结论交由具备资质的专业人士确认
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
- 最新市场数据只使用可定位的一手或可信公开来源，并记录信息截止日
- 关键判断调用 `source-governance.md` 和 `deal-viability-review.md`，明确证据、假设与待确认项
- Save the canonical draft as `outputs/report-draft.md`
- Save the check record as `outputs/report-qc.md`
- 显式公式、评分或估值测算使用 `calculation_gate.py` 复算，并在质检记录中保留退出码
