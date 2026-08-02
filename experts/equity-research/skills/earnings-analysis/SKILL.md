---
name: earnings
description: |
  盈利分析技能，支持两种模式：
  - Preview 模式：业绩发布前的前瞻分析、情景假设、关键观测指标
  - Analysis 模式：业绩发布后的深度解读、Beat/Miss 分析、估计修正
  触发词：earnings analysis、earnings preview、业绩分析、业绩前瞻、财报分析、季报解读、pre-earnings、post-earnings、Q1/Q2/Q3/Q4 results
---

# 盈利分析（Earnings）

## 功能说明

统一的盈利分析技能，根据业绩发布时间自动选择模式：
- **Preview 模式**：业绩尚未发布 → 前瞻分析
- **Analysis 模式**：业绩已发布 → 深度解读

## 模式判断

1. 确认公司和报告季度
2. 搜索该季度业绩是否已发布
3. 已发布 → Analysis 模式；未发布 → Preview 模式

---

## Preview 模式（业绩前瞻）

### 工作流

**Step 1: 采集共识估计**
- 公司名、报告季度、业绩日期（盘前/盘后）
- 共识估计：收入、EPS、关键分部指标
- 前一季度管理层指引

**Step 2: 关键观测框架**

| 维度 | 指标 |
|------|------|
| 财务 | 收入/EPS vs 共识、毛利率/营业利润率变化、FCF、前瞻指引 |
| 运营 | 行业特定 KPI（SaaS: ARR/NRR; 零售: 同店; 工业: 订单簿） |

**Step 3: 情景分析**

| 情景 | 收入 | EPS | 关键驱动 | 股价反应预估 |
|------|------|-----|---------|------------|
| 牛市 | | | | |
| 基本 | | | | |
| 熊市 | | | | |

**Step 4: 催化清单**
- 3-5 个决定股价反应的关键因素
- 期权隐含波动率 vs 历史业绩日波动

### 输出
一页纸 Preview：共识估计表 + 关键观测排序 + 情景表 + 催化清单 + 交易设置

---

## Analysis 模式（业绩深度分析）

### 工作流

**🚨 数据时效性检查**：
1. 确认今日日期
2. 搜索最新业绩（"[Company] latest earnings results"）
3. 验证业绩发布日在 3 个月以内

**Step 1: Beat/Miss 判定**
- 收入 vs 共识（金额和百分比）
- EPS vs 共识
- 关键分部/KPI vs 预期
- 前瞻指引 vs 共识

**Step 2: 深度分析**
- 分部/区域/产品拆解
- 毛利率和费用率变动原因
- 管理层电话会关键表态
- 一次性项目 vs 可持续趋势

**Step 3: 估计修正**
- 更新前瞻 EPS/收入预测
- 展示旧估计 vs 新估计 + 变动原因
- 对目标价的影响

**Step 4: 论点影响评估**
- 原投资逻辑是否强化/弱化
- 评级是否需要调整
- 下一个关键验证点

### 输出
8-12 页 DOCX 报告（详见 `references/workflow.md`）：
- P1: 摘要（评级/目标价/关键数据）
- P2-3: 业绩详解
- P4-5: KPI 与指引
- P6-7: 论点更新
- P8-10: 估值与估计修正
- 8-12 图表

**文件名**: `[Company]_Q[X]_[Year]_Earnings_Update.docx`

## 引用标准

- 每个数据点标注来源和日期
- 必须引用：业绩公告、10-Q、电话会纪录、投资者材料、共识来源
- 所有引用须为可点击超链接

## Resources

- `references/workflow.md` — Analysis 模式详细步骤
- `references/report-structure.md` — 报告页面模板
- `references/best-practices.md` — 质量清单
