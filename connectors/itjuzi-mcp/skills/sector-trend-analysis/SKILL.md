---
name: sector-trend-analysis
description: 当用户需要基于 IT桔子 MCP 数据分析赛道、行业、标签或地区的融资趋势、融资事件数、获投公司数、披露金额、地区对比、时间段对比、头部公司和代表融资事件时使用。该技能会连接 IT桔子 MCP 查询真实融资统计和事件明细，输出面向投资人、产业方、FA、政府招商和投研团队的赛道趋势分析。
---

# 赛道趋势分析 Skill

## MCP 连接信息

本 Skill 由 WorkBuddy 连接器自动携带 `Authorization: Bearer ${ITJUZI_MCP_API_KEY}`。不要向用户索要 API Key，也不要在工具参数里传 `api_key`。

## 适用场景

当用户希望了解某个赛道、行业、标签或地区的融资热度变化、时间段对比、城市对比、代表公司和代表融资事件时，使用本 Skill。

典型问题：

- 过去一年机器人赛道融资趋势如何？
- 2025 年上半年和下半年低空经济融资热度对比。
- 北京、上海、深圳人工智能赛道今年融资事件数和金额对比。
- 最近 90 天具身智能赛道有哪些代表融资事件？
- 机器人赛道融资总额最高的公司有哪些？

## 目标输出

输出一份赛道趋势分析，重点回答：

1. 融资事件数、获投公司数和披露融资金额如何变化。
2. 哪些地区更活跃。
3. 哪些公司融资总额或近期融资更突出。
4. 哪些代表事件支撑趋势判断。
5. 当前趋势判断有哪些数据限制。

## 可调用 MCP 工具

优先使用 IT桔子 MCP：

- `search_tags`
  - 把赛道词解析为 `tag_ids`。

- `get_lookup_options`
  - 查询行业、子行业、轮次、省份等字典。

- `aggregate_funding_by_tags`
  - 按标签、时间段、地区聚合融资事件数、披露金额事件数、获投公司数和融资总额。
  - 适合时间段对比、城市对比、同比和环比问题。

- `search_events`
  - 查询代表融资、上市或并购事件明细。

- `rank_companies_by_funding`
  - 查询赛道内融资总额 TOP 公司。

- `search_companies`
  - 查询赛道公司列表。

- `get_company_profile`
  - 查询重点公司画像。

## 输入信息

用户可能给出：

- 赛道关键词：如机器人、人工智能、低空经济、脑机接口。
- 时间范围：如过去一年、2026 年以来、2025 年上下半年、最近 90 天。
- 地区范围：如全国、北京、上海、深圳、长三角。
- 轮次范围：如早期、A 轮以前、B 轮以后。
- 事件类型：融资、上市相关、并购。默认分析融资事件。
- 输出目的：投资研究、招商分析、内容周报、FA 项目判断。

如果用户没有给出时间范围，默认使用最近 12 个月；如果用户强调“近期趋势”，默认使用最近 180 天。默认地区为全国国内公司。

## 工作流

### 1. 解析赛道和筛选条件

调用 `search_tags` 解析赛道关键词。

示例：

```json
{
  "keyword": "机器人",
  "limit": 10
}
```

必要时调用 `get_lookup_options` 获取行业、子行业、轮次和省份字典。

筛选策略：

- 标签命中明确时，优先使用 `tag_ids`。
- 用户输入是标准行业名时，可使用 `scope_ids` 或 `sub_scope_ids`。
- 多个相近标签默认用 `tag_match_mode="union"`。
- 用户要求“同时具备多个标签”时才用 `intersection`。

### 2. 设计时间段和地区

调用 `aggregate_funding_by_tags` 前，先把问题拆成可比较的 `date_ranges` 和 `regions`。

默认拆分：

- 最近 12 个月：按季度或上下半年拆分。
- 最近 180 天：按近 90 天和前 90 天拆分。
- 年度问题：按自然年拆分。
- 城市对比：全国、北京、上海、深圳等分别作为 region。

地区写法：

```json
[
  {"name": "全国", "location": "in"},
  {"name": "北京", "cities": ["北京", "北京市"]},
  {"name": "上海", "cities": ["上海", "上海市"]},
  {"name": "深圳", "cities": ["深圳", "深圳市"]}
]
```

### 3. 聚合融资趋势

调用 `aggregate_funding_by_tags`。

示例：

```json
{
  "tag_ids": [101],
  "tag_match_mode": "union",
  "event_category": "investment",
  "date_ranges": [
    {"name": "前90天", "date_start": "2026-01-15", "date_end": "2026-04-14"},
    {"name": "近90天", "date_start": "2026-04-15", "date_end": "2026-07-13"}
  ],
  "regions": [
    {"name": "全国", "location": "in"}
  ],
  "location": "in"
}
```

重点读取：

- `funding_event_count`
- `disclosed_amount_event_count`
- `funded_company_count`
- `total_standard_rmb`

如果需要同比、环比或增速，由本 Skill 基于两个时间段结果计算；MCP 当前不直接返回涨跌幅。

### 4. 查询代表事件

调用 `search_events` 查询趋势背后的融资事件。

建议字段：

```json
[
  "event_id",
  "event_time",
  "company_id",
  "company_name",
  "scope_name",
  "sub_scope_name",
  "tags_text",
  "round_name",
  "amount",
  "currency_name",
  "standard_rmb",
  "investor_text"
]
```

查询建议：

- 默认取最近或金额较高的 20-50 条事件。
- 需要大额事件时，优先选择 `standard_rmb > 0` 的事件。
- 样本少时，放宽标签到行业或扩大时间范围，但要说明口径变化。

### 5. 查询头部公司

如用户关心赛道头部公司或融资总额排名，调用 `rank_companies_by_funding`。

建议字段：

```json
[
  "company_id",
  "company_name",
  "scope_name",
  "sub_scope_name",
  "province",
  "city",
  "total_standard_rmb",
  "funding_event_count",
  "latest_event_time",
  "included_round_names_text"
]
```

注意：

- 排名只统计 `standard_rmb > 0` 的融资事件。
- 未出现在 TOP 范围内，不等于公司没有融资。
- 如果用户要求排除 IPO 上市或 IPO 上市后，应通过 `exclude_round_ids` 传入对应轮次 ID。

### 6. 输出赛道趋势分析

按固定结构输出：

```markdown
# {赛道}赛道趋势分析

## 一句话结论

## 核心数据

## 时间段趋势

## 地区对比

## 代表融资事件

## 头部公司

## 趋势判断

## 后续关注方向

## 数据口径和限制
```

## 输出要求

- 所有趋势判断必须能追溯到 MCP 聚合或事件明细。
- 不要把短期融资活跃直接等同于市场长期增长。
- 样本量少时明确说明“样本有限”。
- 融资总额只用 `total_standard_rmb` 或 `standard_rmb` 计算，单位为万人民币。
- `amount` 仅用于展示，不用于聚合、排序或计算。
- 对未披露金额、字段权限省略、城市名称口径差异要明确说明。

## 当前 MCP 能力边界

当前版本可以支持赛道趋势 v1，包括时间段对比、地区对比、事件数、获投公司数、披露金额、代表事件和头部公司。

暂不做：

- 自动热度指数。
- 异常趋势预警。
- 活跃机构排行的一站式聚合。
- 基于外部新闻、专利、招聘或工商变更的综合趋势判断。
- 自动生成图表文件。

后续如需更强趋势产品，应补充更细的赛道融资周期统计、热度指数或趋势分析类聚合能力。
