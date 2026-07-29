---
name: linkfox-keepa-product-request
description: 通过ASIN获取亚马逊商品详情，包括价格、标题、主图、上架日期、材质、重量、变体月销量及近12个月的月销数据。当用户查询亚马逊商品详情、ASIN查询、商品定价、销售排名历史、月销量趋势、商品尺寸、FBA费用、产品规格、批量ASIN查询、Keepa product details, ASIN detail lookup, monthly sales data, pricing info, product specifications, FBA fees, batch ASIN query时触发此技能。即使用户未明确提及"Keepa"，只要其需求涉及获取一个或多个亚马逊ASIN的结构化商品数据，也应触发此技能。
---

# Keepa-亚马逊-商品详情

## 基本信息

- **业务工具名**：`/keepa/productRequest`
- **所属分组**：Keepa · 亚马逊商品与价格历史
- **功能说明**：支持按亚马逊电商的asin 和站点 ，返回亚马逊商品列表页的数据：价格、商品标题、主图、上架时间、材质、重量、子体月销量、最近12个月的每个月月销量等。
- **关键词**：Keepa-亚马逊-商品详情,asin,站点,批量获取多个asin的详情


## 何时使用

当用户意图与“Keepa-亚马逊-商品详情”匹配，或需要以下能力时使用本工具：支持按亚马逊电商的asin 和站点 ，返回亚马逊商品列表页的数据：价格、商品标题、主图、上架时间、材质、重量、子体月销量、最近12个月的每个月月销量等。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 3000；示例：`B0088PUEPK`, `B0088PUEPK,B00U26V4VQ,B07M68S376` | 亚马逊标准识别号(ASIN)，多个ASIN，用英文逗号分隔，最多100个 |
| `domain` | `string` | 是 | 格式 `1\|2\|3\|4\|5\|6\|8\|9\|10\|11\|12`；示例：`1`, `2`, `3`, `4`, `5`, `6`, `8`, `9` | 亚马逊域名ID |
| `history` | `integer` | 否 | 默认 `0`；示例：`1`, `0` | 返回值是否包含历史数据,历史销量 |


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
    "name": "/keepa/productRequest",
    "arguments": {
      "asin": "B0088PUEPK",
      "domain": "1"
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
| `perPage` | `integer` | 否 |  | 每页数量 |
| `products` | `array<object>` | 否 |  | 商品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `sourceType` | `string` | 否 |  | 来源类型：keepa |
| `totalCount` | `integer` | 否 |  | 总数量 |
| `currentPage` | `integer` | 否 |  | 当前页码 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `brand` | `string` | 否 |  | 品牌 |
| `color` | `string` | 否 |  | 颜色 |
| `model` | `string` | 否 |  | 型号 |
| `price` | `number` | 否 |  | 当前价格（单位：元，如美元/欧元等） |
| `title` | `string` | 否 |  | 商品标题 |
| `profit` | `number` | 否 |  | 利润率（百分比，如25.5表示25.5%） |
| `rating` | `number` | 否 |  | 当前评分（0.0-5.0，如4.5星） |
| `weight` | `string` | 否 |  | 重量（克） |
| `asinUrl` | `string` | 否 |  | 亚马逊asin的详情网址 |
| `fbaFees` | `number` | 否 |  | FBA配送费（单位：元） |
| `ratings` | `integer` | 否 |  | 评分数量 |
| `urlSlug` | `string` | 否 |  | URL Slug |
| `currency` | `string` | 否 |  | 币种 |
| `imageUrl` | `string` | 否 |  | 图片URL（完整URL） |
| `isHazmat` | `boolean` | 否 |  | 是否为危险品 |
| `material` | `string` | 否 |  | 产品的材质，指其构造中使用的主要材料 |
| `dimension` | `string` | 否 |  | 尺寸 |
| `itemWidth` | `integer` | 否 |  | 商品宽度，单位为毫米，不可用时为0或-1。示例: 100 |
| `salesRank` | `integer` | 否 |  | 销售排名 |
| `sellerNum` | `integer` | 否 |  | 卖家数 |
| `itemHeight` | `integer` | 否 |  | 商品高度，单位为毫米，不可用时为0或-1。示例: 100 |
| `itemLength` | `integer` | 否 |  | 商品长度，单位为毫米，不可用时为0或-1。示例: 100 |
| `lastUpdate` | `string` | 否 |  | 最后更新时间（yyyy-MM-dd HH:mm:ss） |
| `parentAsin` | `string` | 否 |  | 父ASIN |
| `primePrice` | `number` | 否 |  | prime价格 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：keepa |
| `fulfillment` | `string` | 否 |  | 配送方式(AMZ,FBA,FBM) |
| `reviewCount` | `integer` | 否 |  | 评论数量 |
| `salesRank30` | `integer` | 否 |  | 近30天平均销售排名 |
| `salesRank90` | `integer` | 否 |  | 近90天平均销售排名 |
| `categoryTree` | `string` | 否 |  | 类目树 |
| `manufacturer` | `string` | 否 |  | 制造商 |
| `packageWidth` | `integer` | 否 |  | 包装宽度（毫米） |
| `rootCategory` | `integer` | 否 |  | 根类目ID |
| `salesRank180` | `integer` | 否 |  | 近180天平均销售排名 |
| `variationNum` | `integer` | 否 |  | 变体数量 |
| `availableDate` | `string` | 否 |  | 上架时间（yyyy-MM-dd HH:mm:ss） |
| `packageHeight` | `integer` | 否 |  | 包装高度（毫米） |
| `packageLength` | `integer` | 否 |  | 包装长度（毫米） |
| `packageWeight` | `string` | 否 |  | 包装重量（克） |
| `subcategories` | `array<object>` | 否 |  | 子类目列表 |
| `buyBoxSellerId` | `string` | 否 |  | 购买按钮卖家ID |
| `categoryTreeId` | `string` | 否 |  | 类目树Id |
| `dimensionsType` | `string` | 否 |  | 尺寸类型 |
| `isAdultProduct` | `boolean` | 否 |  | 是否为成人产品 |
| `packageQuantity` | `integer` | 否 |  | 包装中商品的数量，不可用时为0或-1。示例: 3 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片列表 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `packageDimensions` | `string` | 否 |  | 包装尺寸 |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额 |
| `referralFeePercentage` | `number` | 否 |  | 推荐费百分比 |
| `monthlySalesUnits1MonthAgo` | `integer` | 否 |  | 1月前月销量 |
| `monthlySalesUnits2MonthsAgo` | `integer` | 否 |  | 2月前月销量 |
| `monthlySalesUnits3MonthsAgo` | `integer` | 否 |  | 3月前月销量 |
| `monthlySalesUnits4MonthsAgo` | `integer` | 否 |  | 4月前月销量 |
| `monthlySalesUnits5MonthsAgo` | `integer` | 否 |  | 5月前月销量 |
| `monthlySalesUnits6MonthsAgo` | `integer` | 否 |  | 6月前月销量 |
| `monthlySalesUnits7MonthsAgo` | `integer` | 否 |  | 7月前月销量 |
| `monthlySalesUnits8MonthsAgo` | `integer` | 否 |  | 8月前月销量 |
| `monthlySalesUnits9MonthsAgo` | `integer` | 否 |  | 9月前月销量 |
| `monthlySalesUnits10MonthsAgo` | `integer` | 否 |  | 10月前月销量 |
| `monthlySalesUnits11MonthsAgo` | `integer` | 否 |  | 11月前月销量 |
| `monthlySalesUnits12MonthsAgo` | `integer` | 否 |  | 12月前月销量 |

### 嵌套输出结构：`products.subcategories`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `code` | `string` | 否 |  | 类目ID |
| `rank` | `integer` | 否 |  | 排名 |
| `label` | `string` | 否 |  | 类目名称 |

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
