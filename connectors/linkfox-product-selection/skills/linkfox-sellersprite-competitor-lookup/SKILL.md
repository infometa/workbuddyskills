---
name: linkfox-sellersprite-competitor-lookup
description: 使用卖家精灵数据在亚马逊上查找和分析竞品，覆盖12个站点，包含销量、BSR、定价、评分和增长趋势等商品指标。当用户提到竞品查询、竞品分析、ASIN反查、竞争商品研究、查找相似商品、市场竞品发现、商品对标、竞品销量估算、分析竞争Listing、competitor analysis, ASIN reverse lookup, competitor sales, competitor research, SellerSprite, market competitor discovery, competitor trends时触发此技能。即使用户未明确提及"卖家精灵"或"竞品查询"，只要其需求涉及通过ASIN、关键词、卖家名称、品牌或品类发现和分析亚马逊竞品，也应触发此技能。
---

# 卖家精灵-查竞品

## 基本信息

- **业务工具名**：`/sellersprite/competitor-lookup`
- **所属分组**：卖家精灵 · 亚马逊选品
- **功能说明**：支持按亚马逊站点、多个asin、关键词、卖家名称来 查询 亚马逊的商品。
- **关键词**：卖家精灵, 查竞品, 竞品分析, ASIN反查, 销量趋势, 流量来源, 竞品工具


## 何时使用

当用户意图与“卖家精灵-查竞品”匹配，或需要以下能力时使用本工具：支持按亚马逊站点、多个asin、关键词、卖家名称来 查询 亚马逊的商品。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `uid` | `string` | 否 | 最长 1000 | 用户id |
| `page` | `integer` | 否 | 默认 `1` | 页码，从1开始 |
| `size` | `integer` | 否 | 默认 `50`；最小 10 | 每页条数,返回10-100条数据 |
| `brand` | `string` | 否 | 最长 1000 | 品牌 |
| `order` | `object` | 否 |  |  |
| `chatId` | `string` | 否 | 最长 1000 | 对话id |
| `teamId` | `string` | 否 | 最长 1000 | 团队id |
| `keyword` | `string` | 否 | 最长 1000 | 关键字；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等 |
| `asinList` | `string` | 否 | 格式 `^[A-Z0-9]+(,[A-Z0-9]+){0,39}$`；示例：`B072MQ5BRX,B08N5WRWNW` | asin,多个asin使用英文逗号分隔,最多40个 |
| `matchType` | `integer` | 否 | 默认 `1`；示例：`1`, `2`, `3` | 匹配方式，1词组匹配 2模糊匹配 3精准匹配；默认1 |
| `nodeLabel` | `string` | 否 | 最长 1000 | 亚马逊类目名称 |
| `requestId` | `string` | 否 | 最长 1000 | 推送id |
| `nodeIdPath` | `string` | 否 | 最长 1000 | 亚马逊类目id |
| `sellerName` | `string` | 否 | 最长 1000 | 卖家名称 |
| `marketplace` | `string` | 否 | 默认 `"US"`；最长 1000；示例：`US`, `UK`, `DE`, `FR`, `JP`, `CA`, `IT`, `ES` | 市场 |
| `showVariation` | `string` | 否 | 默认 `"N"`；最长 1000；示例：`Y`, `N` | 是否查询变体 |
| `dataSnapshotMonth` | `string` | 否 | 默认 `"nearly"`；最长 1000；示例：`nearly`, `202412`, `202501` | 亚马逊商品数据快照年月。指定查询特定历史时间点的商品数据快照，每个快照包含该月份所有在售商品的完整数据。格式：yyyyMM（如202412表示2024年12月所有在售商品的数据快照）。默认值 'nearly' 表示查询最近30天的实时数据。注意：数据快照是对特定月份亚马逊市场上所有在售商品的完整记录，用于历史分析和同期对比。仅支持查询已存在的历史快照，不支持未来日期。建议季节性分析时查询去年同期快照进行对比 |

### 嵌套输入结构：`order`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `desc` | `string` | 是 | 默认 `"true"`；最长 1000 | true为降序 false为升序 |
| `field` | `string` | 是 | 默认 `"total_units"`；最长 1000；示例：`total_units`, `total_amount`, `bsr_rank`, `price`, `rating`, `reviews`, `profit`, `reviews_rate` | 排序字段 |

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
    "name": "/sellersprite/competitor-lookup",
    "arguments": {
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总行数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `message` | `string` | 否 |  | 执行消息 |
| `products` | `array<object>` | 否 |  | 竞品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `nodeLabel` | `string` | 否 |  | nodeLabel |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `bsr` | `integer` | 否 |  | BSR 排名 |
| `fba` | `number` | 否 |  | fba运费 |
| `sku` | `string` | 否 |  | sku |
| `asin` | `string` | 否 |  | asin |
| `badge` | `object` | 否 |  |  |
| `brand` | `string` | 否 |  | 品牌 |
| `bsrId` | `string` | 否 |  | BSR id |
| `price` | `number` | 否 |  | 价格 |
| `title` | `string` | 否 |  | 商品标题 |
| `nodeId` | `integer` | 否 |  | 节点id |
| `parent` | `string` | 否 |  | 父体ASIN |
| `profit` | `number` | 否 |  | 利润率 |
| `rating` | `number` | 否 |  | 评分 |
| `weight` | `string` | 否 |  | 重量 |
| `keyword` | `string` | 否 |  | 对应筛选的关键词，如果有值，则表示这批数据是通过 这个关键词 keyword 搜索出来的 |
| `ratings` | `integer` | 否 |  | 评分数 |
| `badgeEbc` | `string` | 否 |  | A+页面(Y/N) |
| `brandUrl` | `string` | 否 |  | 品牌URL |
| `currency` | `string` | 否 |  | 币种 |
| `imageUrl` | `string` | 否 |  | 图片URL |
| `sellerId` | `string` | 否 |  | BuyBox卖家id |
| `dimension` | `string` | 否 |  | 尺寸 |
| `sellerNum` | `integer` | 否 |  | 卖家数 |
| `badgeVideo` | `string` | 否 |  | 视频介绍(Y/N) |
| `nodeIdPath` | `string` | 否 |  | 节点id路径字符串 |
| `primePrice` | `number` | 否 |  | prime价格 |
| `sellerName` | `string` | 否 |  | BuyBox卖家 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |
| `fulfillment` | `string` | 否 |  | 配送方式(AMZ,FBA,FBM) |
| `ratingsRate` | `number` | 否 |  | 留评率 |
| `averagePrice` | `number` | 否 |  | 平均价格 |
| `sellerNation` | `string` | 否 |  | BuyBox卖家国籍 |
| `variationNum` | `integer` | 否 |  | 变体数 |
| `availableDate` | `string` | 否 | 格式 `date` | 上架时间(日期) |
| `bsrGrowthRate` | `number` | 否 |  | BSR 增长率 |
| `deliveryPrice` | `number` | 否 |  | 卖家运费 |
| `nodeLabelPath` | `string` | 否 |  | 类目路径 |
| `packageWeight` | `string` | 否 |  | 包装重量 |
| `ratingsGrowth` | `integer` | 否 |  | 月度增长数 |
| `subcategories` | `array<object>` | 否 |  | 子类目 |
| `bsrGrowthCount` | `integer` | 否 |  | BSR 增长数 |
| `dimensionsType` | `string` | 否 |  | 尺寸类型 |
| `badgeBestSeller` | `string` | 否 |  | Best Seller标识(Y/N) |
| `badgeNewRelease` | `string` | 否 |  | release标识(Y/N) |
| `amzUnitDateString` | `string` | 否 |  | 子体销量更新日期(时间戳) |
| `badgeAmazonChoice` | `string` | 否 |  | amazon choice标识(Y/N) |
| `dataSnapshotMonth` | `string` | 否 |  | 数据查询月份 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `packageDimensions` | `string` | 否 |  | 包装尺寸 |
| `variant30DayUnits` | `integer` | 否 |  | 子体月销量(件数) |
| `availableDateString` | `string` | 否 |  | 上架日期(日期字符串) |
| `listingQualityScore` | `number` | 否 |  | listing质量得分 |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额 |
| `variant30DayRevenue` | `number` | 否 |  | 子体月销售额(金额) |
| `packageDimensionType` | `string` | 否 |  | 包装尺寸类型 |
| `variant30DayUpdatedAt` | `string` | 否 |  | 子体数据更新时间(时间戳) |
| `monthlySalesUnitsGrowthRate` | `number` | 否 |  | 月销量增长率 |

### 嵌套输出结构：`products.badge`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `ebc` | `string` | 否 |  | A+页面(Y/N) |
| `video` | `string` | 否 |  | 视频介绍(Y/N) |
| `bestSeller` | `string` | 否 |  | Best Seller标识(Y/N) |
| `newRelease` | `string` | 否 |  | release标识(Y/N) |
| `amazonChoice` | `string` | 否 |  | amazon choice标识(Y/N) |

### 嵌套输出结构：`products.subcategories`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `code` | `string` | 否 |  | 类目code |
| `rank` | `integer` | 否 |  | 排名 |
| `label` | `string` | 否 |  | 名称 |

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
