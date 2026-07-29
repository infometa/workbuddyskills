---
name: linkfox-amazon-search-by-image
description: 基于图片的亚马逊跨站点视觉商品搜索，支持8个站点的以图搜图和视觉相似商品发现。当用户提到以图搜图、图片搜索、视觉搜索、找同款、外观相似商品、图片找货、竞品图片搜索、相似商品发现、image search, Amazon visual search, find similar products, reverse image lookup, visual search, similar items, competitor image search, product image match时触发此技能。即使用户未明确提及"图片搜索"，只要用户提供了图片URL并希望在亚马逊上查找匹配或相似的商品，也应触发此技能。
---

# 亚马逊前端-以图搜图

## 基本信息

- **业务工具名**：`/amazon/searchByImage`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：支持对亚马逊多站点进行视觉搜索。通过图片链接检索外观相似的商品，返回结果包含商品的ASIN, 图片，评论数，评分，价格，品牌等。支持不同站点、不同配送地址（邮编）的检索，仅支持按默认排序、价格正序与倒序、评分正序与倒序、评论数正序与倒序方式排序。
- **关键词**：亚马逊以图搜图，图片找竞品、亚马逊找同款


## 何时使用

当用户意图与“亚马逊前端-以图搜图”匹配，或需要以下能力时使用本工具：支持对亚马逊多站点进行视觉搜索。通过图片链接检索外观相似的商品，返回结果包含商品的ASIN, 图片，评论数，评分，价格，品牌等。支持不同站点、不同配送地址（邮编）的检索，仅支持按默认排序、价格正序与倒序、评分正序与倒序、评论数正序与倒序方式排序。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `sort` | `string` | 否 | 格式 `default\|price-asc-rank\|price-desc-rank\|rating-asc-rank\|rating-desc-rank\|ratings-asc-rank\|ratings-desc-rank`；示例：`default`, `price-asc-rank`, `price-desc-rank`, `rating-asc-rank`, `rating-desc-rank`, `ratings-asc-rank`, `ratings-desc-rank` | 排序, 支持价格，评分，评论数排序 |
| `imageUrl` | `string` | 是 | 最长 1000；示例：`https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg` | 图片URL地址,请确保图片URL地址有效 |
| `deliveryZip` | `string` | 否 | 最长 1000；示例：`10001`, `EC1A 1BB`, `10115`, `75001`, `00100`, `28001`, `100-0001`, `110034` | 站内收货地址邮编或城市，如果用户未指定，则取站点（国家）的默认邮编。例如：亚马逊美国站取邮编10001。 |
| `amazonDomain` | `string` | 是 | 格式 `amazon.com\|amazon.co.uk\|amazon.de\|amazon.fr\|amazon.it\|amazon.es\|amazon.co.jp\|amazon.in`；示例：`amazon.com`, `amazon.co.uk`, `amazon.de`, `amazon.fr`, `amazon.it`, `amazon.es`, `amazon.co.jp`, `amazon.in` | 亚马逊站点，仅支持以下站点：美国，英国，德国，法国，意大利，西班牙，日本，印度。默认 amazon.com |
| `countryOrAreaCode` | `string` | 否 | 最长 1000；示例：`CN`, `JP`, `KR`, `TW`, `HK`, `MO`, `SG`, `TH` | 站外收货的国家代码，站内邮编地址和站外国家地区代码不能同时指定。注意：印度站不支持设置站外国家或地区收货 |
| `aggregateByKeepaData` | `boolean` | 否 |  | 是否聚合Keepa数据 |


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
    "name": "/amazon/searchByImage",
    "arguments": {
      "amazonDomain": "amazon.com",
      "imageUrl": "https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg"
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
| `sourceType` | `string` | 否 |  | 来源类型 |
| `totalCount` | `integer` | 否 |  | 总数量 |
| `currentPage` | `integer` | 否 |  | 当前页码 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `brand` | `string` | 否 |  | 品牌 |
| `color` | `string` | 否 |  | 颜色(keepa) |
| `model` | `string` | 否 |  | 型号(keepa) |
| `price` | `number` | 否 |  | 当前价格.（单位：元，如美元/欧元等） |
| `title` | `string` | 否 |  | 商品标题 |
| `profit` | `number` | 否 |  | 利润率(keepa).（利润率百分比，如25.5表示25.5%） |
| `rating` | `number` | 否 |  | 当前评分.（0.0-5.0，如4.5星） |
| `weight` | `string` | 否 |  | 重量（克）(keepa) |
| `asinUrl` | `string` | 否 |  | 亚马逊asin的详情网址 |
| `fbaFees` | `number` | 否 |  | FBA配送费(keepa).（单位：元） |
| `ratings` | `integer` | 否 |  | 评分数量 |
| `urlSlug` | `string` | 否 |  | URL Slug(keepa) |
| `currency` | `string` | 否 |  | 币种 |
| `imageUrl` | `string` | 否 |  | 图片URL（完整URL） |
| `isHazmat` | `boolean` | 否 |  | 是否为危险品(keepa) |
| `material` | `string` | 否 |  | 产品的材质(keepa).指其构造中使用的主要材料 |
| `oldPrice` | `number` | 否 |  | 划线价格 |
| `dimension` | `string` | 否 |  | 尺寸(keepa) |
| `itemWidth` | `integer` | 否 |  | 商品宽度(keepa).单位为毫米，不可用时为0或-1。示例: 100 |
| `salesRank` | `integer` | 否 |  | 销售排名(keepa) |
| `sellerNum` | `integer` | 否 |  | 卖家数(keepa) |
| `itemHeight` | `integer` | 否 |  | 商品高度(keepa).单位为毫米，不可用时为0或-1。示例: 100 |
| `itemLength` | `integer` | 否 |  | 商品长度(keepa).单位为毫米，不可用时为0或-1。示例: 100 |
| `lastUpdate` | `string` | 否 |  | 最后更新时间(keepa).（yyyy-MM-dd HH:mm:ss） |
| `parentAsin` | `string` | 否 |  | 父ASIN(keepa) |
| `primePrice` | `number` | 否 |  | prime价格(keepa) |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型 |
| `fulfillment` | `string` | 否 |  | 配送方式(AMZ,FBA,FBM)(keepa) |
| `reviewCount` | `integer` | 否 |  | 评论数量(keepa) |
| `salesRank30` | `integer` | 否 |  | 近30天平均销售排名(keepa) |
| `salesRank90` | `integer` | 否 |  | 近90天平均销售排名(keepa) |
| `categoryTree` | `string` | 否 |  | 类目树(keepa) |
| `manufacturer` | `string` | 否 |  | 制造商(keepa) |
| `packageWidth` | `integer` | 否 |  | 包装宽度（毫米）(keepa) |
| `rootCategory` | `integer` | 否 |  | 根类目ID(keepa) |
| `salesRank180` | `integer` | 否 |  | 近180天平均销售排名(keepa) |
| `variationNum` | `integer` | 否 |  | 变体数量(keepa) |
| `availableDate` | `string` | 否 |  | 上架时间(keepa).（yyyy-MM-dd HH:mm:ss） |
| `packageHeight` | `integer` | 否 |  | 包装高度（毫米）(keepa) |
| `packageLength` | `integer` | 否 |  | 包装长度（毫米）(keepa) |
| `packageWeight` | `string` | 否 |  | 包装重量（克）(keepa) |
| `buyBoxSellerId` | `string` | 否 |  | 购买按钮卖家ID(keepa) |
| `categoryTreeId` | `string` | 否 |  | 类目树Id(keepa) |
| `dimensionsType` | `string` | 否 |  | 尺寸类型(keepa) |
| `isAdultProduct` | `boolean` | 否 |  | 是否为成人产品(keepa) |
| `packageQuantity` | `integer` | 否 |  | 包装中商品的数量(keepa).不可用时为0或-1。示例: 3 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片列表(keepa) |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量(keepa) |
| `packageDimensions` | `string` | 否 |  | 包装尺寸(keepa) |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额(keepa) |
| `referralFeePercentage` | `number` | 否 |  | 推荐费百分比(keepa) |
| `monthlySalesUnits1MonthAgo` | `integer` | 否 |  | 1月前月销量(keepa) |
| `monthlySalesUnits2MonthsAgo` | `integer` | 否 |  | 2月前月销量(keepa) |
| `monthlySalesUnits3MonthsAgo` | `integer` | 否 |  | 3月前月销量(keepa) |
| `monthlySalesUnits4MonthsAgo` | `integer` | 否 |  | 4月前月销量(keepa) |
| `monthlySalesUnits5MonthsAgo` | `integer` | 否 |  | 5月前月销量(keepa) |
| `monthlySalesUnits6MonthsAgo` | `integer` | 否 |  | 6月前月销量(keepa) |
| `monthlySalesUnits7MonthsAgo` | `integer` | 否 |  | 7月前月销量(keepa) |
| `monthlySalesUnits8MonthsAgo` | `integer` | 否 |  | 8月前月销量(keepa) |
| `monthlySalesUnits9MonthsAgo` | `integer` | 否 |  | 9月前月销量(keepa) |
| `monthlySalesUnits10MonthsAgo` | `integer` | 否 |  | 10月前月销量(keepa) |
| `monthlySalesUnits11MonthsAgo` | `integer` | 否 |  | 11月前月销量(keepa) |
| `monthlySalesUnits12MonthsAgo` | `integer` | 否 |  | 12月前月销量(keepa) |

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
