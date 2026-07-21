# CBTeamsMarketplace 插件库分析报告

## 执行摘要

CBTeamsMarketplace 共有 27 个插件，其中**13 个插件**直接或间接适合商业公司分析（Company Analysis）场景。这些插件涵盖财务建模、数据分析、投资研究、尽职调查等核心能力。

---

## 第一部分：所有插件列表（27 个）

### 技术开发工具（6 个）
1. **agent-sdk-dev** - CodeBuddy Agent SDK 开发
2. **codebuddy-chat-web** - Web 聊天应用
3. **design-to-code** - Figma 设计转代码
4. **dockerfile-gen** - Dockerfile 生成
5. **modern-webapp** - 现代 Web 应用框架
6. **webapp-testing** - Web 应用测试

### 营销和内部运营（3 个）
7. **executing-marketing-campaigns** - 营销活动管理
8. **internal-comms** - 内部沟通
9. **product-management** - 产品管理

### 文件处理和通用工具（3 个）
10. **document-skills** - 文档处理
11. **general-skills** - 通用技能集
12. **ppt-implement** - PowerPoint 实现
13. **remotion-video-generator** - 视频生成
14. **skill-creator** - 自定义技能创建

### 金融和商业分析（13 个）✓✓✓
15. **data** - 数据分析平台
16. **data-analysis** - Excel/数据分析
17. **deep-research** - 深度研究框架
18. **equity-research** - 股票研究
19. **finance** - 财务与会计
20. **finance-data** - 金融数据检索（209 个 API）
21. **financial-analysis** - 财务建模（DCF、LBO、Comps）
22. **investment-banking** - 投资银行（M&A、融资）
23. **lseg** - 资本市场分析
24. **private-equity** - 私募股权投资
25. **spglobal** - 公司分析和财报
26. **trading-agent** - 投资分析和交易决策
27. **wealth-management** - 财务规划和投资组合

---

## 第二部分：适合商业公司分析的插件（13 个）

### 核心数据和基础设施（3 个）

#### ⭐ **finance-data**（最重要）
- **功能**：金融数据检索，209 个 API 接口
- **覆盖范围**：股票（98 API）、指数、期货、债券、ETF、基金、宏观经济、港股、美股、期权、外汇、大宗商品
- **适配理由**：数据源，其他所有财务分析都依赖此插件
- **核心能力**：自然语言查询 → 自动匹配 API → 返回结构化数据

#### ⭐ **data**（通用数据分析）
- **功能**：SQL 查询、数据探索、可视化、仪表板、洞察生成
- **适配理由**：用于处理公司内部数据、财务数据、业务数据
- **核心能力**：6 种完整数据分析工作流程，支持多种数据库方言

#### **data-analysis**
- **功能**：数据分析和 Excel 工作流程
- **适配理由**：补充数据分析能力
- **核心能力**：Excel 数据处理

---

### 财务建模和估值（3 个）

#### ⭐⭐ **financial-analysis**（最关键）
- **功能**：财务建模、估值、竞争分析
- **主要技能**：
  - DCF 模型（折现现金流估值）
  - Comps 分析（可比公司分析）
  - LBO 模型（杠杆收购模型）
  - 3-Statement 模型（三表整合）
  - 竞争分析
  - Deck 审查、模型审查
- **适配理由**：完整的财务建模工具链，是公司估值和财务分析的核心
- **应用场景**：上市公司估值、企业收购价格、投资决策、并购分析

#### ⭐ **finance**（财务分析和报表）
- **功能**：财务报表生成、差异分析、SOX 审计
- **主要技能**：
  - 日记账分录
  - 账户核对
  - 差异分析
  - 财务报表生成
  - 审计支持
- **适配理由**：生成标准财务报表，分解财务差异
- **应用场景**：财务报表分析、期间对比、原因分析

#### ⭐ **investment-banking**（并购和融资）
- **功能**：交易材料、并购模型、融资分析
- **主要技能**：
  - CIM 建立（融资备忘录）
  - 并购模型（加成/稀释分析）
  - 融资流程管理
  - 买方筛选
  - 交易追踪
- **适配理由**：M&A 交易分析、融资决策、交易执行
- **应用场景**：并购估值、融资结构、交易执行

---

### 研究和分析（4 个）

#### ⭐⭐ **equity-research**（股票研究）
- **功能**：股票覆盖研究、财报分析、投资论文
- **主要技能**：
  - 覆盖初始化（Initiating Coverage）
  - 财报分析和预告
  - 晨间笔记
  - 行业概览
  - 创意生成
  - 论文追踪
  - 模型更新
- **适配理由**：专业的股票研究框架，适用于上市公司分析
- **应用场景**：上市公司研究报告、投资论证、财报分析

#### ⭐ **deep-research**（深度研究）
- **功能**：系统性研究框架，生成详细报告
- **主要特性**：
  - 多 Agent 并行研究（3-20 个子任务并行执行）
  - 深度优先和广度优先研究策略
  - WeChat Official Account 搜索
  - 结构化报告生成
- **适配理由**：适合深度的行业研究、竞争对手分析、市场研究
- **应用场景**：行业研究、市场动态分析、商业机会评估

#### ⭐ **spglobal**（S&P Global 市场情报）
- **功能**：公司分析、财报预告、融资分析
- **主要技能**：
  - 公司撕页表（Tear Sheet）
  - 财报预告分析
  - 融资活动分析
- **适配理由**：标准的公司分析工具，提供快速的公司画像
- **应用场景**：公司基础信息、财报预期、融资动态

#### **lseg**（伦敦交易所资本市场）
- **功能**：资本市场分析、固定收益、外汇、期权
- **主要技能**：
  - 债券分析
  - 外汇交易分析
  - 期权波动率分析
  - 宏观经济监控
- **适配理由**：资本市场分析，补充股票研究
- **应用场景**：企业债券分析、融资成本评估、市场宏观分析

---

### 投资分析和决策（3 个）

#### ⭐⭐ **trading-agent**（投资分析和交易决策）
- **功能**：多角色辩论式投资分析，系统性决策支持
- **主要特性**：
  - 11 个专业 Agent（技术分析师、基本面分析师、情绪分析师、风险分析师等）
  - 5 阶段 SOP：数据收集 → 多空辩论 → 交易决策 → 风险评估 → 报告
  - 技术面、基本面、情绪面、风险面分析
  - 最终 BUY/SELL/HOLD 建议
  - 可视化分析报告（HTML 格式）
- **适配理由**：完整的投资分析流程，适合股票/基金/指数评估
- **应用场景**：股票投资决策、估值判断、风险评估

#### ⭐ **private-equity**（私募股权投资）
- **功能**：PE 投资全流程，交易执行和投资组合管理
- **主要技能**：
  - 交易来源和筛选
  - 尽职调查（DD）清单
  - 投资委员会备忘录
  - 投资组合监控和价值创造计划
  - 收益分析（IRR、MOIC、DPI）
  - 单元经济学分析
- **适配理由**：PE 投资决策、尽职调查、投资组合管理
- **应用场景**：PE 投资分析、企业评估、收购前分析

#### **wealth-management**（财务规划和投资组合）
- **功能**：财务规划、投资组合管理、客户报告
- **主要技能**：
  - 客户财务规划
  - 投资提案
  - 投资组合再平衡
  - 税损收割（Tax-Loss Harvesting）
  - 客户报告
- **适配理由**：投资组合分析和优化
- **应用场景**：企业投资组合评估、资产配置分析

---

## 第三部分：适合商业公司分析的核心工作流程

### 工作流程 1：上市公司完整分析（9 个插件组合）

```
用户提问："分析贵州茅台，我应该买吗？"

使用插件链：
1. finance-data（获取茅台财报数据、行情数据）
2. equity-research（生成股票研究报告）
3. financial-analysis（DCF 估值、同行 Comps）
4. data（数据分析和可视化）
5. trading-agent（投资论证 + 多角色分析 + 最终建议）

输出：完整的投资分析报告
```

### 工作流程 2：私募股权投资评估（5 个插件组合）

```
用户提问："我们应该收购 XYZ 公司吗？"

使用插件链：
1. spglobal（获取公司基础信息）
2. finance-data（获取财务数据）
3. financial-analysis（财务建模、LBO 模型）
4. private-equity（尽职调查、IC 备忘录、收益分析）
5. trading-agent 或 deep-research（深度分析）

输出：并购估值、尽职调查清单、投资建议
```

### 工作流程 3：行业和市场研究（4 个插件组合）

```
用户提问："电动车行业的发展前景和主要参与者对比分析"

使用插件链：
1. deep-research（多 Agent 并行研究行业）
2. finance-data（获取行业相关数据）
3. data（数据分析和可视化）
4. spglobal 或 equity-research（公司级分析）

输出：详细的行业研究报告
```

### 工作流程 4：企业财务健康分析（3 个插件组合）

```
用户提问："该公司财务状况如何？有哪些风险？"

使用插件链：
1. finance-data（获取最新财务数据）
2. finance（生成财务报表、差异分析）
3. financial-analysis（竞争分析）

输出：财务报表分析、风险评估
```

---

## 第四部分：按功能分类的推荐使用

### 财务数据获取
- **首选**：finance-data（覆盖最广，209 个 API）
- **补充**：lseg（资本市场数据）

### 财务建模和估值
- **DCF 估值**：financial-analysis (dcf-model skill)
- **可比公司**：financial-analysis (comps-analysis skill)
- **LBO 模型**：financial-analysis (lbo-model skill)、private-equity
- **并购模型**：investment-banking (merger-model skill)

### 财务报表和差异分析
- **报表生成**：finance（财务报表生成）
- **差异分解**：finance（variance-analysis skill）

### 股票研究和投资分析
- **股票研究报告**：equity-research
- **投资决策**：trading-agent（多角色系统分析）
- **快速公司分析**：spglobal

### 深度分析和研究
- **行业研究**：deep-research（多 Agent 并行）
- **市场研究**：deep-research + data
- **竞争对手分析**：product-management 或 deep-research

### 私募投资分析
- **投资前分析**：private-equity (deal-screening)
- **尽职调查**：private-equity (dd-checklist)
- **投资委员会**：private-equity (ic-memo)
- **投资组合管理**：private-equity (portfolio-monitoring)

### 数据处理和可视化
- **通用数据分析**：data（SQL、可视化、仪表板）
- **Excel 处理**：data-analysis

---

## 第五部分：建议的组合方案

### 方案 A：快速分析（适合快速决策）
**核心 3 插件**
- finance-data（数据源）
- spglobal（快速公司分析）
- trading-agent（投资建议）
**特点**：快速、可操作、适合快速决策

### 方案 B：专业分析（适合深度研究）
**核心 5 插件**
- finance-data（数据源）
- financial-analysis（财务建模）
- equity-research（研究报告）
- trading-agent（投资论证）
- deep-research（补充研究）
**特点**：深度、专业、适合投研团队

### 方案 C：并购和 PE 投资分析
**核心 6 插件**
- finance-data（数据源）
- financial-analysis（财务建模）
- private-equity（PE 全流程）
- investment-banking（M&A 执行）
- spglobal（公司分析）
- trading-agent（风险评估）
**特点**：并购完整流程、PE 投资全链条

### 方案 D：企业数据分析
**核心 4 插件**
- finance-data（金融数据）
- data（通用数据分析）
- finance（财务分析）
- financial-analysis（财务建模）
**特点**：企业内部数据分析、财务分析

---

## 第六部分：特别推荐（Top 5）

### 🥇 **finance-data**
- **为什么**：所有财务分析的数据源，209 个 API
- **使用频率**：最高（几乎每个分析都需要）
- **优先级**：必装

### 🥈 **financial-analysis**
- **为什么**：完整的财务建模工具链（DCF、LBO、Comps）
- **使用频率**：非常高
- **优先级**：必装

### 🥉 **equity-research**
- **为什么**：专业股票研究框架
- **使用频率**：高（股票分析）
- **优先级**：必装

### 4️⃣ **trading-agent**
- **为什么**：系统性投资分析 + 多角色辩论 + 最终建议
- **使用频率**：高（投资决策）
- **优先级**：强烈推荐

### 5️⃣ **private-equity**
- **为什么**：PE 投资全流程
- **使用频率**：高（PE 投资）
- **优先级**：强烈推荐

---

## 结论

CBTeamsMarketplace 提供了**完整的企业分析工具链**：

1. **数据层**：finance-data（209 个 API）+ data（数据分析）
2. **建模层**：financial-analysis（DCF、LBO、Comps）+ investment-banking
3. **分析层**：equity-research、trading-agent、private-equity
4. **研究层**：deep-research（系统性研究框架）

**建议**：
- 如果预算有限，至少安装：finance-data、financial-analysis、equity-research
- 如果需要完整的投资决策支持，加上：trading-agent、private-equity
- 如果需要通用数据分析，加上：data、deep-research

这 13 个插件可以覆盖从快速分析到深度研究、从股票分析到 PE 投资、从财务报表到并购估值的完整商业分析场景。
