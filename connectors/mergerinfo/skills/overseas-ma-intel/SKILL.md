---
name: overseas-ma-intel
display_name: 海外并购情报
display_name_en: Cross-border M&A Intelligence
description: 查询海外待售标的与跨境并购事件（含巨头动向）。当用户问「今天有什么在卖的」「最近某行业/某地区有哪些并购」「某巨头最近有什么动作」时使用。依赖 MergerInfo 连接器提供的 MCP 工具。
description_zh: 查询海外待售标的、跨境并购事件与巨头动向。
description_en: Search overseas assets for sale, cross-border M&A events and large-acquirer activity.
version: 0.2.0
author: MergerInfo
---

# 海外并购情报

覆盖两个工具：`get_sale_opportunities`（今日待售标的）与 `search_overseas_events`（并购事件与巨头动向）。

## 前置条件

两个工具由 MergerInfo 连接器提供。若当前会话不存在这两个工具，说明连接器尚未安装或未连接，请提示用户先在「专家·技能·连接器 → 连接器」中安装 MergerInfo，**不要凭模型知识编造查询结果**。

## 选择哪个工具

| 用户意图 | 用哪个 | 说明 |
|---|---|---|
| 今天/某一天新增的出售线索 | `get_sale_opportunities` | 按单个自然日查询，默认北京时间今日 |
| 一段时间内的事件、某公司相关事件、某类事件 | `search_overseas_events` | 默认最近 7 天，可用 `since_days` 调整 |
| 巨头/大型企业的动向 | `search_overseas_events`，传 `event_type: "giant_moves"` | 这是筛选项，不是独立工具 |

用户只说「有什么并购」而没有时间词时，用 `search_overseas_events` 的默认 7 天，不要擅自扩大范围。

## 参数

`get_sale_opportunities`
- `date`：`today` 或 `YYYY-MM-DD`，默认 `today`
- `industry`、`region`：字符串数组，可省略
- `limit`：条数上限，实际返回受会员等级限制

`search_overseas_events`
- `query` 或 `company`：关键词，匹配标题、摘要与标的名称
- `industry`、`region`：字符串数组
- `event_type`：`giant_moves` | `for_sale` | `completed` | `blocked`
- `since_days`：回溯天数，默认 7；超出等级上限时服务端会自动收窄并在 `notes` 中说明
- `limit`：条数上限

## 回答时必须遵守

**日期语义。** `event_date` 是信息发布或更新日期，**不代表标的当天才挂牌，也不保证现在仍在出售**。转述时不要说成「今天刚挂牌」或「目前正在出售」。`stage` 字段才是当前交易阶段。

**没有数据就说没有。** 当天无新增时如实回答「今日暂无新增出售线索」，可建议改看最近 7 天，**不要**把旧数据说成今日数据，也不要用模型知识补齐。

**出处要分清。** `source.name` 与 `source.url` 是原始报道来源；`next_actions` 里的链接是 MergerInfo 站内页面。不要把站内链接说成原始出处。

**覆盖范围要如实转述。** `coverage.matched` 是符合条件的总数，`coverage.returned` 是本次实际返回数。两者不等时告诉用户「共找到 N 条，本次展示 M 条」。`coverage.industry_scope` 为 `selected` 表示结果已被限制在用户订阅的行业内，需要说明这一点。

**行动提示最多一个。** 结果里的 `next_actions` 最多一条，原样转达即可，不要为每条结果都附加链接或宣传语。

## 额度与引导

`quota` 给出剩余额度与重置时间。当 `notes` 提示额度用尽时，直接转达 `next_actions` 中的链接引导用户登录连接或申请会员。

**不要向用户索取 API Key。** 本服务未登录即可试用，会员通过会员区的连接码连接，不存在需要用户去找 API 的场景。

## 示例

用户：今天有哪些海外待售的工业制造标的？
调用：`get_sale_opportunities({ "industry": ["Industrial & Manufacturing"] })`

用户：最近两周半导体行业有什么跨境并购？
调用：`search_overseas_events({ "industry": ["Technology & Digitalization"], "query": "半导体", "since_days": 14 })`

用户：最近有哪些巨头在出手？
调用：`search_overseas_events({ "event_type": "giant_moves" })`
