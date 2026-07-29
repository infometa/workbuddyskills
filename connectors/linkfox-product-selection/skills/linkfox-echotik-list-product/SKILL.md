---
name: linkfox-echotik-list-product
description: 搜索和分析TikTok商品数据，包括销量、达人带货数据、定价和佣金比例，覆盖16个TikTok Shop站点。当用户提到TikTok商品搜索、TikTok Shop商品分析、TikTok销量数据、达人带货销售、TikTok选品、TikTok佣金比例、TikTok商品排名、EchoTik数据查询、TikTok product search, TikTok sales, influencer sales, TikTok commission, TikTok product selection, short-video e-commerce, TikTok data时触发此技能。即使用户未明确提及"EchoTik"或"TikTok"，只要其需求涉及在TikTok Shop上搜索商品或分析TikTok商品表现指标，也应触发此技能。
---

# EchoTik-TikTok商品搜索

## 基本信息

- **业务工具名**：`/echotik/listProduct`
- **所属分组**：EchoTik · TikTok 商品与视频
- **功能说明**：支持TikTok平台的商品关键词搜索，分析商品在TikTok上的销量和达人带货数据。
- **关键词**：EchoTik, TikTok搜索, TikTok商品搜索, 达人带货数据, 销量查询, 直播商品, EchoTik-TikTok, EchoTik-TikTok商品搜索


## 何时使用

当用户意图与“EchoTik-TikTok商品搜索”匹配，或需要以下能力时使用本工具：支持TikTok平台的商品关键词搜索，分析商品在TikTok上的销量和达人带货数据。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `region` | `string` | 否 | 默认 `"US"`；格式 `US\|ID\|TH\|PH\|MY\|VN\|GB\|MX\|SG\|SA\|BR\|ES\|JP\|DE\|IT\|FR`；示例：`US`, `ID`, `TH`, `PH`, `MY`, `VN`, `GB`, `MX` | 区域 |
| `keyword` | `string` | 否 | 最长 1000 | 商品关键词（请翻译为当地语言） |
| `pageNum` | `integer` | 否 | 默认 `1` | 分页页码 |
| `pageSize` | `integer` | 否 | 默认 `50` | 每页条数 |
| `saleDays` | `integer` | 否 |  | 商品上架销售天数,单位是天 |
| `sortType` | `integer` | 否 | 默认 `1`；示例：`0`, `1` | 排序方式 |
| `maxReviewCount` | `integer` | 否 |  | 商品评价数（最大值） |
| `maxSpuAvgPrice` | `number` | 否 |  | SPU平均价格（最大值） |
| `maxTotalIflCnt` | `integer` | 否 |  | 带货达人数（最大值） |
| `minReviewCount` | `integer` | 否 |  | 商品评价数（最小值） |
| `minSpuAvgPrice` | `number` | 否 |  | SPU平均价格（最小值） |
| `minTotalIflCnt` | `integer` | 否 |  | 带货达人数（最小值） |
| `maxFirstCrawlDt` | `integer` | 否 |  | 商品上架时间（最大值） |
| `maxTotalSaleCnt` | `integer` | 否 |  | 总销量（最大值） |
| `minFirstCrawlDt` | `integer` | 否 | 示例：`20200101` | 商品上架时间（最小值） |
| `minTotalSaleCnt` | `integer` | 否 |  | 总销量（最小值） |
| `maxProductRating` | `number` | 否 |  | 商品评分（最大值） |
| `maxTotalVideoCnt` | `integer` | 否 |  | 带货视频数（最大值） |
| `maxTotalViewsCnt` | `integer` | 否 |  | 带货播放数（最大值） |
| `minProductRating` | `number` | 否 |  | 商品评分（最小值） |
| `minTotalVideoCnt` | `integer` | 否 |  | 带货视频数（最小值） |
| `minTotalViewsCnt` | `integer` | 否 |  | 带货播放数（最小值） |
| `productSortField` | `integer` | 否 | 默认 `1`；示例：`1`, `2`, `3`, `4`, `5`, `6`, `7` | 排序字段 |
| `categoryKeywordCN` | `string` | 否 | 最长 1000 | 商品分类（商品分类 请输入 中文） |
| `maxTotalSale30dCnt` | `integer` | 否 |  | 30天销量（最大值） |
| `maxTotalSaleGmvAmt` | `string` | 否 | 最长 1000 | 商品交易总额（最大值） |
| `minTotalSale30dCnt` | `integer` | 否 |  | 30天销量（最小值） |
| `minTotalSaleGmvAmt` | `string` | 否 | 最长 1000 | 商品交易总额（最小值） |
| `maxTotalSaleGmv30dAmt` | `string` | 否 | 最长 1000 | 商品交易总额（30天）（最大值） |
| `minTotalSaleGmv30dAmt` | `string` | 否 | 最长 1000 | 商品交易总额（30天）（最小值） |
| `maxProductCommissionRate` | `number` | 否 |  | 商品佣金比例（最大值）, 输入值为百分比时自动转成小数，例如：5%->0.05 |
| `minProductCommissionRate` | `number` | 否 |  | 商品佣金比例（最小值）, 输入值为百分比时自动转成小数，例如：5%->0.05 |


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
    "name": "/echotik/listProduct",
    "arguments": {
      "pageSize": 50,
      "sortType": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `products` | `array<object>` | 否 |  | 产品信息列表 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 产品ID |
| `price` | `number` | 否 |  | 商品价格 |
| `title` | `string` | 否 |  | 商品名称 |
| `region` | `string` | 否 |  | 区域代码 |
| `ratings` | `integer` | 否 |  | 评论数 |
| `coverUrl` | `string` | 否 |  | 封面图URL列表 |
| `currency` | `string` | 否 |  | 货币 |
| `discount` | `string` | 否 |  | 折扣信息 |
| `imageUrl` | `string` | 否 |  | 商品图片URL |
| `maxPrice` | `number` | 否 |  | 最高价格 |
| `minPrice` | `number` | 否 |  | 最低价格 |
| `productId` | `string` | 否 |  | 商品唯一标识ID |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 商品来源 |
| `categoryIds` | `array<any>` | 否 |  | 商品品类ID列表 |
| `isSShopText` | `string` | 否 |  | 是否S店 |
| `offMarkText` | `string` | 否 |  | 是否有优惠标记 |
| `productName` | `string` | 否 |  | 商品名称 |
| `reviewCount` | `integer` | 否 |  | 评论数量 |
| `spuAvgPrice` | `number` | 否 |  | SPU平均价格 |
| `categoryName` | `string` | 否 |  | 商品品类名称 |
| `firstCrawlDt` | `integer` | 否 |  | 上架日期 |
| `totalSaleCnt` | `integer` | 否 |  | 总销量 |
| `availableDate` | `string` | 否 | 格式 `date` | 上架时间(时间戳) |
| `productRating` | `number` | 否 |  | 商品评分 |
| `salePropsInfo` | `array<object>` | 否 |  | 销售属性信息 |
| `salesFlagText` | `string` | 否 |  | 带货方式 |
| `totalSale1dCnt` | `integer` | 否 |  | 1天内总销量 |
| `totalSale7dCnt` | `integer` | 否 |  | 7天内总销量 |
| `totalSale15dCnt` | `integer` | 否 |  | 15天内总销量 |
| `totalSale30dCnt` | `integer` | 否 |  | 30天内总销量 |
| `totalSale60dCnt` | `integer` | 否 |  | 60天内总销量 |
| `totalSale90dCnt` | `integer` | 否 |  | 90天内总销量 |
| `totalSaleGmvAmt` | `number` | 否 |  | 总销售额 |
| `freeShippingText` | `string` | 否 |  | 是否包邮 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片URL列表 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `totalSaleGmv1dAmt` | `number` | 否 |  | 1天内总销售额 |
| `totalSaleGmv7dAmt` | `number` | 否 |  | 7天内总销售额 |
| `salesTrendFlagText` | `string` | 否 |  | 销售趋势标记 |
| `totalSaleGmv15dAmt` | `number` | 否 |  | 15天内总销售额 |
| `totalSaleGmv30dAmt` | `number` | 否 |  | 30天内总销售额 |
| `totalSaleGmv60dAmt` | `number` | 否 |  | 60天内总销售额 |
| `totalSaleGmv90dAmt` | `number` | 否 |  | 90天内总销售额 |
| `productCommissionRate` | `number` | 否 |  | 商品佣金比例 |

### 嵌套输出结构：`products.salePropsInfo`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `propId` | `string` | 否 |  | 产品属性ID |
| `hasImage` | `boolean` | 否 |  | 产品属性是否包含图片 |
| `propName` | `string` | 否 |  | 产品属性名称 |
| `salePropValues` | `array<object>` | 否 |  | 产品属性值列表 |

### 嵌套输出结构：`products.salePropsInfo.salePropValues`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `image` | `string` | 否 |  | 属性值图片 |
| `propValue` | `string` | 否 |  | 属性值名称 |
| `propValueId` | `string` | 否 |  | 属性值ID |

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
