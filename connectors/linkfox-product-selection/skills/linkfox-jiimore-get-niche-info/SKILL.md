---
name: linkfox-jiimore-get-niche-info
description: 查询并分析极目数据的亚马逊细分市场洞察，包括市场指标、买家评论、竞争格局、价格走势和增长趋势。当用户提到细分市场分析、市场洞察、细分市场数据、市场竞争分析、品牌集中度、新品上架成功率、断货率、价格趋势、评论洞察、市场需求评分、niche market insights, market metrics, competition analysis, price trends, growth trends, Jiimore data, market intelligence, out-of-stock rate时触发此技能。即使用户未明确提及"极目"或"细分市场"，只要其需求涉及通过市场ID查询特定亚马逊细分市场的市场级情报，也应触发此技能。
---

# 极目-亚马逊-细分市场洞察信息

## 基本信息

- **业务工具名**：`/jiimore/getNicheInfo`
- **所属分组**：极目 · 亚马逊选品
- **功能说明**：支持细分市场id查询市场信息、买家评价、市场洞察等，只支持单个id查询
- **关键词**：极目数据, 细分市场, 市场信息, 市场洞察


## 何时使用

当用户意图与“极目-亚马逊-细分市场洞察信息”匹配，或需要以下能力时使用本工具：支持细分市场id查询市场信息、买家评价、市场洞察等，只支持单个id查询

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `nicheId` | `string` | 是 | 最长 1000 | 细分市场ID |
| `countryCode` | `string` | 否 | 默认 `"US"`；格式 `^(US\|JP\|DE)$`；示例：`US`, `JP`, `DE` | 国家编码，仅支持US，JP，DE |


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
    "name": "/jiimore/getNicheInfo",
    "arguments": {
      "nicheId": "example-id",
      "countryCode": "US"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 细分市场信息列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `cpc` | `object` | 否 |  |  |
| `acos` | `number` | 否 |  | （ACOS）广告销售成本比 |
| `demand` | `integer` | 否 |  | 细分市场得分 |
| `nicheId` | `string` | 否 |  | 细分市场ID |
| `avgPrice` | `number` | 否 |  | 产品均价 |
| `brandCount` | `integer` | 否 |  | 品牌数量 |
| `nicheTitle` | `string` | 否 |  | 细分市场标题 |
| `maximumPrice` | `number` | 否 |  | 产品最高价 |
| `minimumPrice` | `number` | 否 |  | 产品最低价 |
| `productCount` | `integer` | 否 |  | 商品数量 |
| `avgOOSRateNow` | `number` | 否 |  | 平均缺货率(当前) |
| `brandCountNow` | `integer` | 否 |  | 品牌数量(当前) |
| `categorieList` | `array<any>` | 否 |  | 商品品类列表 |
| `marketplaceId` | `string` | 否 |  | 市场ID |
| `translationZh` | `string` | 否 |  | 细分市场标题(中文) |
| `avgBrandAgeNow` | `number` | 否 |  | 平均品牌年龄(当前) |
| `breakEvenRatio` | `number` | 否 |  | 盈亏平衡比率 |
| `productCountNow` | `integer` | 否 |  | 商品数量(当前) |
| `unitsSoldWeekly` | `integer` | 否 |  | 销售数量（周数据） |
| `clickCountWeekly` | `integer` | 否 |  | 点击量（周数据） |
| `returnRateAnnual` | `number` | 否 |  | 退货率（全年数据） |
| `avgOOSRateT360Now` | `number` | 否 |  | 平均缺货率(360天统计)(当前) |
| `avgReviewCountNow` | `number` | 否 |  | 平均评论数(当前) |
| `brandCountT360Now` | `integer` | 否 |  | 品牌数量(360天统计)(当前) |
| `avgBrandAgeT360Now` | `number` | 否 |  | 平均品牌年龄(360 天统计)(当前) |
| `avgProductPriceNow` | `number` | 否 |  | 产品均价(当前) |
| `avgReviewRatingNow` | `number` | 否 |  | 平均评论评分(当前) |
| `searchVolumeWeekly` | `integer` | 否 |  | 搜索量（周数据） |
| `unitsSoldQuarterly` | `integer` | 否 |  | 销售数量（季度数据） |
| `avgOOSRateT90Before` | `number` | 否 |  | 平均缺货率(90天前) |
| `brandCountT90Before` | `integer` | 否 |  | 品牌数量(90天前) |
| `clickCountQuarterly` | `integer` | 否 |  | 点击量（季度数据） |
| `avgBestSellerRankNow` | `number` | 否 |  | 平均BestSeller排名(当前) |
| `avgBrandAgeQuarterly` | `number` | 否 |  | 平均品牌年龄(季度数据) |
| `avgBrandAgeT90Before` | `number` | 否 |  | 平均品牌年龄(90天前) |
| `avgOOSRateT360Before` | `number` | 否 |  | 平均缺货率(360天前) |
| `brandCountT360Before` | `integer` | 否 |  | 品牌数量(360天前) |
| `launchRateSemiannual` | `number` | 否 |  | 发布商品的成功率（半年数据） |
| `top5BrandsClickShare` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额 |
| `avgBrandAgeT360Before` | `number` | 否 |  | 平均品牌年龄(360天前) |
| `productCountT90Before` | `integer` | 否 |  | 商品数量(90天前) |
| `referenceAsinImageUrl` | `string` | 否 |  | 细分市场参考图片地址 |
| `searchVolumeQuarterly` | `integer` | 否 |  | 搜索量（季度数据） |
| `productCountT360Before` | `integer` | 否 |  | 商品数量(360天前) |
| `sellingPartnerCountNow` | `integer` | 否 |  | 销售伙伴数量(当前) |
| `top5ProductsClickShare` | `number` | 否 |  | 排名前 5 位的商品点击份额 |
| `avgOOSRateT360T90Before` | `number` | 否 |  | 平均缺货率(360天统计)(90天前) |
| `avgReviewCountT90Before` | `number` | 否 |  | 平均评论数(90天前) |
| `avgSellingPartnerAgeNow` | `number` | 否 |  | 平均销售伙伴年龄(当前) |
| `brandCountT360T90Before` | `integer` | 否 |  | 品牌数量(360天统计)(90天前) |
| `productStarRatingImpact` | `array<object>` | 否 |  | 产品星级影响力信息 |
| `top5BrandsClickShareNow` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(当前) |
| `avgBrandAgeT360T90Before` | `number` | 否 |  | 平均品牌年龄(360 天统计)(90天前) |
| `avgOOSRateT360T360Before` | `number` | 否 |  | 平均缺货率(360天统计)(360天前) |
| `avgProductPriceT90Before` | `number` | 否 |  | 产品均价(90天前) |
| `avgReviewCountT360Before` | `number` | 否 |  | 平均评论数(360天前) |
| `avgReviewRatingT90Before` | `number` | 否 |  | 平均评论评分(90天前) |
| `brandCountT360T360Before` | `integer` | 否 |  | 品牌数量(360天统计)(360天前) |
| `searchVolumeGrowthWeekly` | `number` | 否 |  | 搜索量增长率（周数据） |
| `successfulLaunchesT90Now` | `integer` | 否 |  | 成功上架数(90天统计)(当前） |
| `top20BrandsClickShareNow` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(当前) |
| `avgBrandAgeT360T360Before` | `number` | 否 |  | 平均品牌年龄(360 天统计)(360天前) |
| `avgProductPriceT360Before` | `number` | 否 |  | 产品均价(360天前) |
| `avgReviewRatingT360Before` | `number` | 否 |  | 平均评论评分(360天前) |
| `successfulLaunchesT180Now` | `integer` | 否 |  | 成功发布商品的数量（180 天统计）(当前) |
| `successfulLaunchesT360Now` | `integer` | 否 |  | 成功发布商品的数量（360 天统计）(当前) |
| `top5ProductsClickShareNow` | `number` | 否 |  | 前5个商品所占细分市场的点击量份额(当前) |
| `avgBestSellerRankT90Before` | `number` | 否 |  | 平均BestSeller排名(90天前) |
| `newProductsLaunchedT180Now` | `integer` | 否 |  | 已发布新产品的数量(180天统计)(当前) |
| `newProductsLaunchedT360Now` | `integer` | 否 |  | 新上架商品数(360天统计)(当前) |
| `primeProductsPercentageNow` | `number` | 否 |  | prime商品的百分比(当前) |
| `searchConversionRateWeekly` | `number` | 否 |  | 搜索转换率（周数据） |
| `sellingPartnerCountT360Now` | `integer` | 否 |  | 销售伙伴数量(360 天统计)(当前) |
| `top20ProductsClickShareNow` | `number` | 否 |  | 前20个商品所占细分市场的点击量份额（当前) |
| `avgBestSellerRankT360Before` | `number` | 否 |  | 平均BestSeller排名(360天前) |
| `clickToSaleConversionWeekly` | `number` | 否 |  | 点击转换率（周数据） |
| `profitMarginGt50PctSkuRatio` | `number` | 否 |  | 利润率大于50%的商品比例 |
| `searchVolumeGrowthQuarterly` | `number` | 否 |  | 搜索量增长率（季度数据） |
| `top5BrandsClickShareT360Now` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(360 天统计)(当前) |
| `clickConversionRateQuarterly` | `number` | 否 |  | 点击转换率（季度数据） |
| `sellingPartnerCountT90Before` | `integer` | 否 |  | 销售伙伴数量(90天前) |
| `successfulLaunchedSemiannual` | `integer` | 否 |  | 成功发布商品的数量（半年数据） |
| `top20BrandsClickShareT360Now` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(360天统计)（当前) |
| `avgSellingPartnerAgeT90Before` | `number` | 否 |  | 平均销售伙伴年龄(90天前) |
| `newProductsLaunchedSemiannual` | `integer` | 否 |  | 已发布新产品的数量（半年数据） |
| `searchConversionRateQuarterly` | `number` | 否 |  | 搜索转换率（季度数据） |
| `sellingPartnerCountT360Before` | `integer` | 否 |  | 销售伙伴数量(360天前) |
| `top5BrandsClickShareT90Before` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(90天前) |
| `top5ProductsClickShareT360Now` | `number` | 否 |  | 排名前 5 位的商品点击份额（360天统计）(当前) |
| `avgSellingPartnerAgeT360Before` | `number` | 否 |  | 平均销售伙伴年龄(360天前) |
| `negativeCustomerReviewInsights` | `array<object>` | 否 |  | 负面客户评论见解信息 |
| `positiveCustomerReviewInsights` | `array<object>` | 否 |  | 正面客户评论见解信息 |
| `primeProductsPercentageT360Now` | `number` | 否 |  | prime商品的百分比(360 天统计）(当前) |
| `sponsoredProductsPercentageNow` | `number` | 否 |  | 已进行商品推广的商品的百分比(当前) |
| `successfulLaunchesT90T90Before` | `integer` | 否 |  | 成功上架数(90天统计)(90天前) |
| `top20BrandsClickShareT90Before` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(90天前) |
| `top20ProductsClickShareT360Now` | `number` | 否 |  | 排名前20位的商品点击份额(360 天统计)(当前) |
| `top5BrandsClickShareT360Before` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(360天前) |
| `successfulLaunchesT180T90Before` | `integer` | 否 |  | 成功发布商品的数量（180 天统计）(90天前) |
| `successfulLaunchesT360T90Before` | `integer` | 否 |  | 成功发布商品的数量（360 天统计）(90天前) |
| `successfulLaunchesT90T360Before` | `integer` | 否 |  | 成功上架数(90天统计)(360天前) |
| `top20BrandsClickShareT360Before` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(360天前) |
| `top5ProductsClickShareT90Before` | `number` | 否 |  | 前5个商品所占细分市场的点击量份额(90天前) |
| `newProductsLaunchedT180T90Before` | `integer` | 否 |  | 已发布新产品的数量(180天统计)(90天前) |
| `newProductsLaunchedT360T90Before` | `integer` | 否 |  | 新上架商品数(360天统计)(90天前) |
| `primeProductsPercentageT90Before` | `number` | 否 |  | prime商品的百分比(90天前) |
| `sellingPartnerCountT360T90Before` | `integer` | 否 |  | 销售伙伴数量(360 天统计)(90天前) |
| `successfulLaunchesT180T360Before` | `integer` | 否 |  | 成功发布商品的数量（180 天统计）(360天前) |
| `successfulLaunchesT360T360Before` | `integer` | 否 |  | 成功发布商品的数量（360 天统计）(360天前) |
| `top20ProductsClickShareT90Before` | `number` | 否 |  | 前20个商品所占细分市场的点击量份额（90天前) |
| `top5ProductsClickShareT360Before` | `number` | 否 |  | 前5个商品所占细分市场的点击量份额(360天前) |
| `newProductsLaunchedT180T360Before` | `integer` | 否 |  | 已发布新产品的数量(180天统计)(360天前) |
| `newProductsLaunchedT360T360Before` | `integer` | 否 |  | 新上架商品数(360天统计)(360天前) |
| `primeProductsPercentageT360Before` | `number` | 否 |  | prime商品的百分比(360天前) |
| `sellingPartnerCountT360T360Before` | `integer` | 否 |  | 销售伙伴数量(360 天统计)(360天前) |
| `top20ProductsClickShareT360Before` | `number` | 否 |  | 前20个商品所占细分市场的点击量份额（360天前) |
| `top5BrandsClickShareT360T90Before` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(360 天统计)(90天前) |
| `sponsoredProductsPercentageT360Now` | `number` | 否 |  | 已进行商品推广的商品的百分比(360 天统计)(当前) |
| `top20BrandsClickShareT360T90Before` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(360天统计)（90天前) |
| `top5BrandsClickShareT360T360Before` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额(360 天统计)(360天前) |
| `top20BrandsClickShareT360T360Before` | `number` | 否 |  | 前20个品牌所占细分市场的点击量份额(360天统计)（360天前) |
| `top5ProductsClickShareT360T90Before` | `number` | 否 |  | 排名前 5 位的商品点击份额（360天统计）(90天前) |
| `primeProductsPercentageT360T90Before` | `number` | 否 |  | prime商品的百分比(360 天统计）(90天前) |
| `sponsoredProductsPercentageT90Before` | `number` | 否 |  | 已进行商品推广的商品的百分比(90天前) |
| `top20ProductsClickShareT360T90Before` | `number` | 否 |  | 排名前20位的商品点击份额(360 天统计)(90天前) |
| `top5ProductsClickShareT360T360Before` | `number` | 否 |  | 排名前 5 位的商品点击份额（360天统计）(360天前) |
| `primeProductsPercentageT360T360Before` | `number` | 否 |  | prime商品的百分比(360 天统计）(360天前) |
| `sponsoredProductsPercentageT360Before` | `number` | 否 |  | 已进行商品推广的商品的百分比(360天前) |
| `top20ProductsClickShareT360T360Before` | `number` | 否 |  | 排名前20位的商品点击份额(360 天统计)(360天前) |
| `sponsoredProductsPercentageT360T90Before` | `number` | 否 |  | 已进行商品推广的商品的百分比(360 天统计)(90天前) |
| `sponsoredProductsPercentageT360T360Before` | `number` | 否 |  | 已进行商品推广的商品的百分比(360 天统计)(360天前) |

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
