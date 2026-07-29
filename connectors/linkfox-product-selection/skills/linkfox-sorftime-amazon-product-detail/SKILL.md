---
name: linkfox-sorftime-amazon-product-detail
description: 基于Sorftime数据按ASIN查询亚马逊产品详情与历史趋势，涵盖14个站点。当用户提到Sorftime产品详情、ASIN详情查询、销量走势、价格曲线、价格历史、BSR排名历史、BSR趋势、利润分析、FBA费用分析、毛利率、产品趋势分析、日销量月销量、销售额趋势、Deal促销历史、product detail, sales trend, price history, BSR ranking, profit analysis, FBA fees时触发此技能。即使用户未明确提及\"Sorftime\"，只要其需求涉及按ASIN查询亚马逊产品详情或历史趋势数据，也应触发此技能。
---

# Sorftime-亚马逊产品详情(含趋势)

## 基本信息

- **业务工具名**：`/sorftime/amazon/productDetail`
- **所属分组**：Sorftime · 亚马逊选品
- **功能说明**：按亚马逊 ASIN 查询产品详情和趋势数据，核心数据包括：
- **关键词**：Sorftime, 亚马逊产品详情，价格曲线, 销量走势, BSR排名历史, 利润分析, 价格历史


## 何时使用

当用户意图与“Sorftime-亚马逊产品详情(含趋势)”匹配，或需要以下能力时使用本工具：按亚马逊 ASIN 查询产品详情和趋势数据，核心数据包括：

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000；示例：`B0088PUEPK`, `B0088PUEPK,B00U26V4VQ` | 亚马逊标准识别号(ASIN).支持多个ASIN查询（最多10个），以英文逗号隔开 |
| `marketplace` | `string` | 是 | 格式 `us\|gb\|de\|fr\|in\|ca\|jp\|es\|it\|mx\|ae\|au\|br\|sa`；示例：`us`, `gb`, `de`, `fr`, `in`, `ca`, `jp`, `es` | 亚马逊站点代码 |
| `includeTrend` | `integer` | 否 | 默认 `1`；示例：`1`, `2` | 是否包含趋势数据.1：包含（默认）；2：不包含 |
| `queryTrendEndDate` | `string` | 否 | 格式 `^\d{4}-\d{2}-\d{2}$`；示例：`2025-03-01` | 趋势截止日期(yyyy-MM-dd) |
| `queryTrendStartDate` | `string` | 否 | 格式 `^\d{4}-\d{2}-\d{2}$`；示例：`2025-01-01` | 趋势开始日期(yyyy-MM-dd).默认仅返回近15天，查询天数>15天时扣费加倍 |


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
    "name": "/sorftime/amazon/productDetail",
    "arguments": {
      "asin": "B0088PUEPK",
      "marketplace": "us"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 响应消息 |
| `code` | `integer` | 否 |  | 响应码（200表示成功） |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costTime` | `integer` | 否 |  | 接口耗时(毫秒) |
| `products` | `array<object>` | 否 |  | 产品详情列表 |
| `costToken` | `integer` | 否 |  | 消耗的Token数量 |
| `sourceType` | `string` | 否 |  | 来源类型 |
| `requestConsumed` | `integer` | 否 |  | 消耗的请求数 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `size` | `array<any>` | 否 |  | 尺寸.外包装[最长边,第二长边,最短边]，单位cm |
| `aPlus` | `boolean` | 否 |  | 有A+ |
| `brand` | `string` | 否 |  | 品牌 |
| `isFBA` | `boolean` | 否 |  | 是否FBA.Buybox卖家是否使用FBA物流 |
| `price` | `number` | 否 |  | 销售价.扣除Coupon后的实际售价，单位为当地货币(如美元) |
| `title` | `string` | 否 |  | 商品标题 |
| `coupon` | `integer` | 否 |  | Coupon政策.值>0为抵扣金额(如500=$5)，值<0为折扣百分比(如-10=10%折扣) |
| `rating` | `number` | 否 |  | 当前评分（0.0-5.0，如4.70） |
| `weight` | `string` | 否 |  | 重量.单位g |
| `asinUrl` | `string` | 否 |  | 商品链接.亚马逊Listing详情页URL |
| `fbaFees` | `number` | 否 |  | FBA费用.单位为当地货币(如美元) |
| `feature` | `object` | 否 |  |  |
| `offSale` | `integer` | 否 |  | 是否下架.1=不可售，0=可售 |
| `ratings` | `integer` | 否 |  | 评分数量 |
| `category` | `array<any>` | 否 |  | 大类.[大类名称, NodeId] |
| `dealType` | `string` | 否 |  | Deal标签 |
| `ebcPhoto` | `array<any>` | 否 |  | A+图片 |
| `hasVideo` | `boolean` | 否 |  | 有视频 |
| `imageUrl` | `string` | 否 |  | 主图 |
| `property` | `object` | 否 |  |  |
| `shipCost` | `number` | 否 |  | FBM配送费.单位为当地货币(如美元) |
| `attribute` | `array<object>` | 否 |  | 产品属性.有子体时表示子体属性 |
| `dealTrend` | `array<any>` | 否 |  | Deal趋势.下标%2=0为日期，下标%2=1为状态(1:有Deal，0:无Deal) |
| `fbaDetail` | `array<any>` | 否 |  | FBA明细.首项为配送费，后续为月份:仓储费，如[475,1-9:5,10-12:15] |
| `rankTrend` | `array<any>` | 否 |  | BSR趋势.大类排名变化历史 |
| `salesRank` | `integer` | 否 |  | BSR排名 |
| `sellerNum` | `integer` | 否 |  | 卖家数 |
| `shipsFrom` | `string` | 否 |  | 发货方 |
| `storeName` | `string` | 否 |  | 店铺名称 |
| `lastUpdate` | `string` | 否 |  | 更新时间.ASIN数据最近采集时间（格式yyyy-MM-dd） |
| `onlineDays` | `integer` | 否 |  | 上架天数 |
| `parentAsin` | `string` | 否 |  | 父ASIN.有子体时为父级ASIN，无子体时为null |
| `priceTrend` | `array<any>` | 否 |  | 售价趋势.未扣Coupon，单位为当地货币最小单位，-1表示该日无可用价格 |
| `profitRate` | `number` | 否 |  | 利润率.例25.83表示25.83% |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型 |
| `bsrCategory` | `array<object>` | 否 |  | 小类排名列表 |
| `description` | `string` | 否 |  | 五点描述 |
| `platformFee` | `number` | 否 |  | 平台佣金.单位为当地货币(如美元) |
| `productInfo` | `object` | 否 |  |  |
| `productType` | `string` | 否 |  | 分类.亚马逊产品类目节点名称 |
| `bsrRankTrend` | `array<object>` | 否 |  | 小类排名趋势.JSON格式，示例: [{NodeId:xxx, Rank:[日期,排名,...]}] |
| `buyboxSeller` | `string` | 否 |  | Buybox卖家 |
| `extraSavings` | `array<object>` | 否 |  | 关联促销.如[{Asin:xxx, Text:Save 5%...}] |
| `productBadge` | `array<any>` | 否 |  | 产品标志.如Amazon Choice、Best Seller、New Release等 |
| `profitAmount` | `number` | 否 |  | 利润.到手价-FBA费-佣金，单位为当地货币(如美元) |
| `variationNum` | `integer` | 否 |  | 变体数 |
| `availableDate` | `string` | 否 |  | 上架时间.格式yyyy-MM-dd |
| `hasBrandStore` | `boolean` | 否 |  | 有品牌店 |
| `variationASIN` | `array<any>` | 否 |  | 子体ASIN列表.无子体时为null |
| `brandPromotion` | `string` | 否 |  | 品牌促销 |
| `buyBoxSellerId` | `string` | 否 |  | Buybox卖家ID |
| `listPriceTrend` | `array<any>` | 否 |  | 原价趋势.划线价历史，单位为当地货币最小单位，-1表示该日无可用价格 |
| `oneStarRatings` | `number` | 否 |  | 1星占比.例15.5表示15.5% |
| `twoStarRatings` | `number` | 否 |  | 2星占比.例8.0表示8.0% |
| `fiveStarRatings` | `number` | 否 |  | 5星占比.例57.7表示57.7% |
| `fourStarRatings` | `number` | 否 |  | 4星占比.例12.3表示12.3% |
| `productImageUrls` | `array<any>` | 否 |  | 主图列表 |
| `threeStarRatings` | `number` | 否 |  | 3星占比.例6.5表示6.5% |
| `monthlySalesUnits` | `integer` | 否 |  | 官方月销量.亚马逊公布的ASIN月销量，取近7个自然日最新值，无则为0 |
| `buyboxSellerAddress` | `string` | 否 |  | 卖家所在地.Buybox卖家国籍(二字码如CN、US)，亚马逊自营时为null |
| `listingSalesOfDailyTrend` | `array<any>` | 否 |  | 日销售额趋势.单位为当地货币最小单位(如美分)，下标%2=0为日期，下标%2=1为预计日销售额 |
| `listingSalesOfMonthTrend` | `array<any>` | 否 |  | 月销售额趋势.单位为当地货币最小单位，下标%2=0为日期，下标%2=1为预计月销售额 |
| `listingSalesVolumeOfDailyTrend` | `array<any>` | 否 |  | 日销量趋势.下标%2=0为日期，下标%2=1为预计日销量，值为-1表示无法预估 |
| `listingSalesVolumeOfMonthTrend` | `array<any>` | 否 |  | 月销量趋势.近30日销量，下标%2=0为日期，下标%2=1为月销量，值为-1表示无法预估 |

### 嵌套输出结构：`products.attribute`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 子体ASIN |
| `name` | `string` | 否 |  | 属性名 |
| `value` | `string` | 否 |  | 属性值 |

### 嵌套输出结构：`products.bsrCategory`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `date` | `string` | 否 |  | 日期.格式yyyyMMdd |
| `name` | `string` | 否 |  | 类目名称 |
| `rank` | `string` | 否 |  | 排名 |
| `nodeId` | `string` | 否 |  | 节点ID |

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
