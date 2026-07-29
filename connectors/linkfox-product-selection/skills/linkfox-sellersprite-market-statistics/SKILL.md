---
name: linkfox-sellersprite-market-statistics
description: 使用卖家精灵选市场统计能力，按类目节点输出市场统计看板，包含头部Listing平均评分、均价、BSR、销量、卖家数量与新品相关指标，适合快速判断某类目市场质量与竞争格局。当用户提到类目市场统计、选市场看板、市场基础盘评估、节点市场质量、头部商品统计、SellerSprite market statistics、category statistics时触发此技能。即使用户未明确提及"卖家精灵"，只要需求是按类目节点查看聚合统计结果，也应触发此技能。
---

# 卖家精灵-选市场-统计

## 基本信息

- **业务工具名**：`/sellersprite/market/statistics`
- **所属分组**：卖家精灵 · 亚马逊选品
- **功能说明**：根据指定的亚马逊站点、类目节点ID路径、时间范围，统计该类目市场的核心数据指标，包括头部Listing平均销量、平均评分、平均BSR、新品月均销量、月均销售额、月评论平均增长数等，支持自定义头部Listing数量和新品定义月数，帮助卖家快速评估目标类目的市场规模与竞争态势。
- **关键词**：卖家精灵, 市场统计, 类目分析, 头部Listing, 新品数据, 月均销量, 月均销售额, 市场规模, 竞争分析, 选市场


## 何时使用

当用户意图与“卖家精灵-选市场-统计”匹配，或需要以下能力时使用本工具：根据指定的亚马逊站点、类目节点ID路径、时间范围，统计该类目市场的核心数据指标，包括头部Listing平均销量、平均评分、平均BSR、新品月均销量、月均销售额、月评论平均增长数等，支持自定义头部Listing数量和新品定义月数，帮助卖家快速评估目标类目的市场规模与竞争态势。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `topN` | `integer` | 否 | 默认 `10` | 头部Listing数量 |
| `month` | `string` | 否 | 格式 `^(nearly\|(19\|20)\d{2}(0[1-9]\|1[0-2]))$`；示例：`nearly`, `202507` | 筛选日期。支持两种写法：① nearly — 最近30天；② yyyyMM — 查询具体月份（如 202507），最多支持当前月往前共24个月内的月份 |
| `newProduct` | `integer` | 否 | 默认 `6` | 新品定义(月) |
| `nodeIdPath` | `string` | 是 | 最长 1000 | 节点ID路径字符串，如 1064954:1069242:1069784:1069820:1069838:1069828 |
| `marketplace` | `string` | 是 | 默认 `"US"`；最长 1000；示例：`US`, `JP`, `UK`, `DE`, `FR`, `IT`, `ES`, `CA` | 站点编码(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹) |


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
    "name": "/sellersprite/market/statistics",
    "arguments": {
      "marketplace": "US",
      "nodeIdPath": "example-id"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 统计结果列表(对应第三方 data) |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总条数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `marketplace` | `string` | 否 |  | 站点编码 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `avgBsr` | `integer` | 否 |  | 平均BSR |
| `brands` | `integer` | 否 |  | 品牌数 |
| `sellers` | `integer` | 否 |  | 卖家数 |
| `avgPrice` | `number` | 否 |  | 平均价格 |
| `avgUnits` | `integer` | 否 |  | 月均销量 |
| `currency` | `string` | 否 |  | 该市场的货币类型 |
| `hlAvgBsr` | `integer` | 否 |  | 头部Listing前N名商品平均BSR |
| `products` | `integer` | 否 |  | 样品商品数 |
| `avgProfit` | `number` | 否 |  | 平均利润率 |
| `avgRating` | `number` | 否 |  | 平均星级 |
| `avgVolume` | `number` | 否 |  | 平均体积(in³) |
| `avgWeight` | `number` | 否 |  | 平均重量(pound) |
| `avgRatings` | `integer` | 否 |  | 平均评分数 |
| `avgRevenue` | `number` | 否 |  | 月均销售额 |
| `avgSellers` | `number` | 否 |  | 平均卖家数 |
| `hlAvgPrice` | `number` | 否 |  | 头部Listing前N名商品平均价格 |
| `hlAvgUnits` | `integer` | 否 |  | 头部Listing前N名商品月均销量 |
| `hlProducts` | `integer` | 否 |  | 头部Listing前N名商品样本数 |
| `nodeIdPath` | `string` | 否 |  | 节点ID路径 |
| `countryCode` | `string` | 否 |  | 国家二简码 |
| `hlAvgRating` | `number` | 否 |  | 头部Listing前N名商品平均星级 |
| `marketplace` | `string` | 否 |  | 市场标志 |
| `newAvgPrice` | `number` | 否 |  | 新品平均价格 |
| `newAvgUnits` | `integer` | 否 |  | 新品月均销量 |
| `newProducts` | `integer` | 否 |  | 新品数量 |
| `avgRatingsCv` | `integer` | 否 |  | 月评论平均增长数 |
| `hlAvgRatings` | `integer` | 否 |  | 头部Listing前N名商品平均评论数 |
| `hlAvgRevenue` | `number` | 否 |  | 头部Listing前N名商品月均销售额 |
| `newAvgRating` | `number` | 否 |  | 新品平均星级 |
| `baseAvgVolume` | `number` | 否 |  | 平均体积(cm³) |
| `baseAvgWeight` | `number` | 否 |  | 平均重量(g) |
| `lastShelfDate` | `string` | 否 |  | 商品最新上架日期 |
| `maxNewRatings` | `integer` | 否 |  | 最高新品评分数 |
| `minNewRatings` | `integer` | 否 |  | 最低新品评分数 |
| `newAvgRatings` | `integer` | 否 |  | 新品平均评分数 |
| `newAvgRevenue` | `number` | 否 |  | 新品月均销售额 |
| `nodeLabelPath` | `string` | 否 |  | 节点名称路径 |
| `totalProducts` | `integer` | 否 |  | 商品总数 |
| `firstShelfDate` | `string` | 否 |  | 商品首次上架日期 |
| `hlAvgRatingsCv` | `integer` | 否 |  | 头部Listing前N名商品月评论平均增长数 |
| `nodeLabelLocale` | `string` | 否 |  | 节点名称翻译 |
| `nodeLabelPathLocale` | `string` | 否 |  | 节点名称路径翻译 |
| `newProductProportion` | `number` | 否 |  | 新品数量占比 |

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
