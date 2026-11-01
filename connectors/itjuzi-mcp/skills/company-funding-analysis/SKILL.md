---
name: company-funding-analysis
description: 当用户需要基于 IT桔子 MCP 数据分析某家公司融资历史、最新融资、投资方、轮次变化、融资金额、融资节奏、同赛道融资位置和后续融资观察点时使用。该技能会连接 IT桔子 MCP 查询真实公司画像和融资事件，输出面向投资人、FA、创业者和产业研究人员的公司融资分析。
---

# 公司融资分析 Skill

## MCP 连接信息

本 Skill 由 WorkBuddy 连接器自动携带 `Authorization: Bearer ${ITJUZI_MCP_API_KEY}`。不要向用户索要 API Key，也不要在工具参数里传 `api_key`。

## 适用场景

当用户希望分析某家公司的融资情况、投资方背景、融资节奏、最新融资状态或同赛道融资位置时，使用本 Skill。

典型问题：

- 帮我分析智元机器人的融资历史。
- 某家公司最近一次融资是什么时候？投资方是谁？
- 这家公司融资节奏怎么样，有没有长期未融资？
- 帮我整理某公司的投资方和每轮融资情况。
- 某家公司在机器人赛道融资水平大概处于什么位置？

## 目标输出

输出一份公司融资分析，重点回答：

1. 公司基本画像和所在赛道。
2. 最新融资状态。
3. 历史融资时间线。
4. 投资方变化和资金进入节奏。
5. 融资金额、轮次和同赛道位置。
6. 后续应关注的问题和风险信号。

## 可调用 MCP 工具

优先使用 IT桔子 MCP：

- `resolve_companies`
  - 把公司简称或工商全称解析为 `company_id`。
  - 用户给出公司名时优先使用，不要用标签条件反推公司。

- `get_company_profile`
  - 查询公司画像、行业、标签、地区、发展阶段、最新融资等。

- `get_company_funding_events`
  - 查询公司融资历史。

- `search_events`
  - 用户要求看同赛道近期融资事件时使用。

- `rank_companies_by_funding`
  - 用户要求判断公司在赛道内融资总额位置时使用。

- `search_tags`
  - 解析公司所在或用户指定赛道标签。

- `get_lookup_options`
  - 查询行业、轮次、地区等字典。

## 输入信息

用户可能给出：

- 公司简称或工商全称。
- 分析重点：融资历史、最新融资、投资方、融资节奏、同赛道对比。
- 时间范围：如最近 3 年、成立以来、2026 年以来。
- 输出目的：投前初筛、FA 项目判断、竞品研究、产业研究。

如果用户没有给出分析重点，默认输出“公司画像 + 最新融资 + 融资时间线 + 投资方观察 + 后续关注点”。

## 工作流

### 1. 解析公司

先调用 `resolve_companies`。

示例：

```json
{
  "names": ["智元机器人"],
  "limit_per_name": 5,
  "exact_only": false,
  "fields": [
    "company_id",
    "company_name",
    "registered_name",
    "scope_name",
    "sub_scope_name"
  ]
}
```

如果返回多个候选，结合工商名称、行业、地区、成立年份和用户上下文选择最匹配公司；无法判断时，把候选列出让用户确认。

### 2. 查询公司画像

调用 `get_company_profile`。

建议字段：

```json
[
  "company_id",
  "company_name",
  "registered_name",
  "website",
  "slogan",
  "scope_name",
  "sub_scope_name",
  "tags_text",
  "province",
  "city",
  "born_year",
  "born_month",
  "fund_status_name",
  "latest_event_time",
  "latest_round_name",
  "latest_amount",
  "total_standard_rmb",
  "all_investors_text",
  "qualification_names_text"
]
```

如果套餐权限省略 `registered_name`、`total_standard_rmb` 或 `all_investors_text`，在报告中说明字段受权限限制。

### 3. 查询融资历史

调用 `get_company_funding_events`。

建议字段：

```json
[
  "event_id",
  "event_time",
  "company_id",
  "company_name",
  "round_name",
  "amount",
  "currency_name",
  "standard_rmb",
  "investor_text",
  "fa_text"
]
```

查询建议：

- 默认按时间倒序展示。
- 如果用户需要完整时间线，输出时按时间正序整理。
- `page_size` 第一版建议 50，套餐允许时可到 100。

### 4. 归纳融资时间线

基于融资事件整理：

- 最新融资时间、轮次、金额、投资方。
- 历史轮次演进。
- 每轮融资间隔。
- 披露金额事件和未透露金额事件。
- 累计披露融资额，必须只用 `standard_rmb` 汇总。
- 投资方是否出现连续跟投或头部机构进入。

金额规则：

- `amount`、`latest_amount` 是展示字段，按原文写。
- `standard_rmb`、`total_standard_rmb` 是数值字段，单位为万人民币，可用于统计。
- 不要把“未透露”或“数千万”转换成精确金额。

### 5. 做同赛道位置判断

只有当用户要求对比或判断位置时，再调用 `rank_companies_by_funding` 或 `search_events`。

推荐流程：

1. 从公司画像或用户输入中确定标签、行业、地区。
2. 用 `search_tags` 解析关键赛道词。
3. 调用 `rank_companies_by_funding` 获取同赛道融资总额 TOP 公司。
4. 判断目标公司是否出现在结果中；如果未出现，只说明“在当前 TOP 范围内未出现”，不要推断其绝对排名。

### 6. 输出公司融资分析

按固定结构输出：

```markdown
# {公司名称}融资分析

## 一句话结论

## 公司画像

## 最新融资

## 融资历史时间线

## 投资方观察

## 融资节奏和金额观察

## 同赛道位置

## 后续关注点

## 数据口径和限制
```

## 输出要求

- 所有结论必须基于 MCP 查询结果。
- 不要把融资事件解读为当前估值或最新估值，除非返回字段明确包含。
- 不要编造投资方、FA、金额或工商信息。
- 样本较少、金额未披露、字段被权限省略时要明确说明。
- 对公司风险使用“需要关注”“可能提示”，不要做确定性法律或财务判断。
- 如果用户要报告风格，保持投研 memo 口吻，不写成营销软文。

## 当前 MCP 能力边界

当前版本适合分析公开可见融资历史和公司画像，不适合完整尽调。

暂不做：

- 股权穿透和真实控制人判断。
- 财务报表分析。
- 法律诉讼、舆情和知识产权风险。
- 当前估值精确判断。
- 自动生成正式尽调报告附件。
