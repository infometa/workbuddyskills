---
name: linkfox-junglescout-keyword-share-of-voice
description: Jungle Scout关键词市场份额（Share of Voice）分析，返回亚马逊搜索结果前3页的品牌声量占比（自然/广告/综合）、30天精确搜索量、PPC竞价中位数及TOP3 ASIN点击转化数据，覆盖10个站点。当用户提到品牌市场份额、品牌声量占比、搜索结果品牌分布、Share of Voice、SOV分析、品牌竞争格局、广告位占比、自然排名品牌占比、PPC竞价分析、品牌垄断分析、keyword share of voice, brand visibility, organic vs sponsored share, brand dominance, PPC bid analysis, search result brand distribution, competitive landscape, weighted SOV, top ASIN clicks conversions时触发此技能。即使用户未明确提及"Share of Voice"或"SOV"，只要其需求涉及分析某个亚马逊关键词搜索结果中各品牌的市场占有率或竞争格局，也应触发此技能。
---

# 关键词市场份额(Share of Voice)

## 基本信息

- **业务工具名**：`/tool-jungle-scout/keywords/share-of-voice`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：关键词市场份额(Share of Voice)：GET share_of_voice，返回前三页各品牌自然/赞助/综合声量份额、精确匹配30天搜索量、PPC建议竞价中位数及TOP3 ASIN近一周转化


## 何时使用

当用户意图与“关键词市场份额(Share of Voice)”匹配，或需要以下能力时使用本工具：关键词市场份额(Share of Voice)：GET share_of_voice，返回前三页各品牌自然/赞助/综合声量份额、精确匹配30天搜索量、PPC建议竞价中位数及TOP3 ASIN近一周转化

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `keyword` | `string` | 是 | 最长 1000；示例：`golf` | 要分析的亚马逊搜索关键词 |
| `marketplace` | `string` | 是 | 最长 1000；示例：`us`, `uk`, `de`, `in`, `ca`, `fr`, `it`, `es` | 目标市场代码 |


## MCP 调用示例

向以下地址发起 HTTP `POST`：

```text
https://mcp-tool-gateway.linkfox.com/mcp/any-tool
```

请求体：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "/tool-jungle-scout/keywords/share-of-voice",
    "arguments": {
      "marketplace": "us",
      "keyword": "golf"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `shareOfVoice` | `object` | 否 |  |  |

### 嵌套输出结构：`shareOfVoice`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `id` | `string` | 否 |  | 数据标识(市场/关键词) |
| `type` | `string` | 否 |  | 响应资源类型(固定 share_of_voice) |
| `brands` | `array<object>` | 否 |  | 各品牌在前三页的声量与排名、价格等指标 |
| `topAsins` | `array<object>` | 否 |  | TOP3 ASIN的点击、购买与转化率；可为空 |
| `updatedAt` | `string` | 否 |  | 数据刷新时间(ISO 8601) |
| `productCount` | `integer` | 否 |  | 返回数据中包含的ASIN数量(搜索结果产品总数) |
| `topAsinsModelEndDate` | `string` | 否 |  | TOP3 ASIN点击与转化统计区间终点(YYYY-MM-DD)；可为空 |
| `topAsinsModelStartDate` | `string` | 否 |  | TOP3 ASIN点击与转化统计区间起点(YYYY-MM-DD)；可为空 |
| `exactSuggestedBidMedian` | `number` | 否 |  | 所选市场货币下，赢得竞价的中位估算成本(PPC) |
| `estimated30DaySearchVolume` | `integer` | 否 |  | 该关键词精确匹配30天搜索量估算(次) |

### 嵌套输出结构：`shareOfVoice.brands`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `brand` | `string` | 否 |  | 品牌名称 |
| `organicBasicSov` | `number` | 否 |  | 自然基础声量份额；可为空 |
| `organicProducts` | `integer` | 否 |  | 自然搜索结果中该品牌产品数；可为空 |
| `combinedBasicSov` | `number` | 否 |  | 综合基础声量份额(出现次数/总结果) |
| `combinedProducts` | `integer` | 否 |  | 综合(自然+赞助)前三页内该品牌产品数 |
| `sponsoredBasicSov` | `number` | 否 |  | 赞助基础声量份额；可为空 |
| `sponsoredProducts` | `integer` | 否 |  | 赞助位中该品牌产品数；可为空 |
| `organicWeightedSov` | `number` | 否 |  | 自然加权声量份额；可为空 |
| `combinedWeightedSov` | `number` | 否 |  | 综合加权声量份额(0–1，含Amazon Choice徽标与位次权重) |
| `organicAveragePrice` | `number` | 否 |  | 自然结果平均价格；可为空 |
| `combinedAveragePrice` | `number` | 否 |  | 综合平均价格(市场货币) |
| `sponsoredWeightedSov` | `number` | 否 |  | 赞助加权声量份额；可为空 |
| `sponsoredAveragePrice` | `number` | 否 |  | 赞助结果平均价格；可为空 |
| `organicAveragePosition` | `number` | 否 |  | 自然结果平均排名；可为空 |
| `combinedAveragePosition` | `number` | 否 |  | 综合平均排名位置 |
| `sponsoredAveragePosition` | `number` | 否 |  | 赞助结果平均排名；可为空 |

### 嵌套输出结构：`shareOfVoice.topAsins`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `name` | `string` | 否 |  | 商品标题/描述；可为空 |
| `brand` | `string` | 否 |  | 品牌；可为空 |
| `clicks` | `integer` | 否 |  | 统计区间内点击次数 |
| `conversions` | `integer` | 否 |  | 统计区间内购买次数 |
| `conversionRate` | `number` | 否 |  | 转化率(购买/点击)；可为空 |

## 响应处理建议

1. 先检查 JSON-RPC 外层是否包含 `error`。
2. 成功时读取 `result`，并继续解析其中的 `content`、`data`、`products`、`items` 或其他业务字段。
3. 如果响应为 `text/event-stream`，按 SSE 事件读取 `data:` 内容，再解析 JSON。
4. 保留分页字段、总数、失败明细及 `costToken`。
5. 向用户输出分析结论，不要直接倾倒大段原始 JSON。

## 原始 Schema

原始的Input Schema 和 Output Schema 参考 references/schema.md

## 解决认证和积分问题

异常情况：未配置 `LINKFOX_AGENT_API_KEY` 和 `LINKFOXAGENT_API_KEY`；响应 401 或 402；消息含"积分余额不足/quota exceeded/insufficient balance/套餐到期/需充值"等。

措施：优先用 skill 内 onboarding.md 引导；找不到则加载 /linkfox-onboarding skill。 根据它的指引操作。

**注意**：你是workbuddy，并且渠道是workbuddy，使用linkfox-onboarding登录注册时**必须**传递channel为 workbuddy。这非常重要！
