---
name: linkfox-sellersprite-product-search
description: 使用卖家精灵数据搜索和筛选亚马逊商品，支持价格、月销量、BSR排名、毛利率、评分、配送方式、标签、卖家来源等多维度条件，覆盖多个亚马逊站点。当用户提到亚马逊选品调研、产品筛选、销量过滤、产品发掘、BSR分析、小众商品发现、竞品分析、市场机会评估、按商品维度的市场规模估算、毛利率筛选、SellerSprite product selection, Amazon product selection, sales filtering, BSR analysis, profit screening, market analysis, product selection tool时触发此技能。即使用户未明确提及"卖家精灵"，只要其需求涉及筛选和分析亚马逊商品级数据进行选品，也应触发此技能。
---

# 卖家精灵-选产品

## 基本信息

- **业务工具名**：`/sellersprite/productSearch`
- **所属分组**：卖家精灵 · 亚马逊选品
- **功能说明**：支持按价格、月销量、数据快照年月、分页、毛利率、关键词、类目名称等条件来筛选亚马逊的商品。
- **关键词**：卖家精灵, 亚马逊选品, 选产品, 销量筛选, 市场分析, 过滤, 词组匹配, 选品工具, 功能需求调研, 市场机会点, 选品决策


## 何时使用

当用户意图与“卖家精灵-选产品”匹配，或需要以下能力时使用本工具：支持按价格、月销量、数据快照年月、分页、毛利率、关键词、类目名称等条件来筛选亚马逊的商品。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `uid` | `string` | 否 | 最长 1000 | 用户id |
| `page` | `integer` | 否 | 默认 `1` | 页码，从1开始 |
| `size` | `integer` | 否 | 默认 `20`；最小 10；最大 100 | 每页条数,返回10-100条数据 |
| `order` | `object` | 否 |  |  |
| `chatId` | `string` | 否 | 最长 1000 | 对话id |
| `maxBsr` | `integer` | 否 |  | 大类BSR最高排名 |
| `maxFba` | `number` | 否 | 最小 0 | 最高FBA运费 |
| `minBsr` | `integer` | 否 |  | 大类BSR最低排名 |
| `minFba` | `number` | 否 | 最小 0 | 最低FBA运费 |
| `teamId` | `string` | 否 | 最长 1000 | 团队id |
| `keyword` | `string` | 否 | 最长 10240 | 关键字；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等 |
| `maxPrice` | `number` | 否 | 最小 0 | 最高价格 |
| `maxUnits` | `integer` | 否 | 最小 0 | 最高月销量 |
| `minPrice` | `number` | 否 | 最小 0 | 最低价格 |
| `minUnits` | `integer` | 否 | 最小 0 | 最低月销量 |
| `matchType` | `integer` | 否 | 默认 `1`；示例：`1`, `2`, `3` | 匹配方式，1词组匹配 2模糊匹配 3精准匹配；默认 1 |
| `maxProfit` | `number` | 否 | 最小 1；最大 100 | 最大毛利率,单位 %，利润率最小为1 ，最大为100 |
| `maxRating` | `number` | 否 | 最小 0；最大 5 | 最高评分值。评分最大为5分，最小0分，3.8-4.3为产品改良机会的产品 |
| `minProfit` | `number` | 否 | 最小 1；最大 100 | 最小毛利率，单位 %。利润率最小为1 ，最大为100 |
| `minRating` | `number` | 否 | 最小 0；最大 5 | 最低评分值。评分最大为5分，最小0分 |
| `nodeLabel` | `string` | 否 | 最长 1000 | 亚马逊类目名称 |
| `requestId` | `string` | 否 | 最长 1000 | 推送id |
| `maxAmzUnit` | `integer` | 否 | 最小 0 | 最高子体近30日销量(仅近30日查询支持) |
| `maxRatings` | `integer` | 否 | 最小 0；最大 10000 | 最高评分数 |
| `maxRevenue` | `number` | 否 | 最小 0 | 最高月销售额 |
| `maxSellers` | `integer` | 否 |  | 最大卖家数量，卖家数量小于等于 |
| `maxWeights` | `number` | 否 | 最小 0 | 最大重量 |
| `minAmzUnit` | `integer` | 否 | 最小 0 | 最低子体近30日销量(仅近30日查询支持) |
| `minRatings` | `integer` | 否 | 最小 0；最大 10000 | 最低评分数 |
| `minRevenue` | `number` | 否 | 最小 0 | 最低月销售额 |
| `minSellers` | `integer` | 否 |  | 最小卖家数量,卖家数量大于等于 |
| `minWeights` | `number` | 否 | 最小 0 | 最小重量 |
| `nodeIdPath` | `string` | 否 | 最长 1000 | 亚马逊类目节点id |
| `weightUnit` | `string` | 否 | 格式 `g\|kg\|oz\|lb`；示例：`g`, `kg`, `oz`, `lb` | 重量单位。支持的有：g/kg/oz/lb 这几种，如果用户的参数里面有重量，则必须要求用户也输入重量的单位。 |
| `fulfillment` | `string` | 否 | 最长 1000；示例：`AMZ`, `FBA`, `FBM`, `AMZ,FBA`, `AMZ,FBM`, `FBA,FBM`, `AMZ,FBA,FBM`, `` | 配送方式，多条件查询用逗号隔开AMZ or FBA or FBM |
| `marketplace` | `string` | 否 | 默认 `"US"`；格式 `US\|UK\|DE\|FR\|JP\|CA\|IT\|ES\|MX\|IN`；示例：`US`, `UK`, `DE`, `FR`, `JP`, `CA`, `IT`, `ES` | 市场 |
| `sellerNation` | `string` | 否 | 最长 1000；示例：`US`, `DE`, `FR`, `JP`, `CN`, `HK`, `` | 卖家所属地，默认不限制，多条件查询用逗号隔开 |
| `dimensionType` | `string` | 否 | 最长 1000 | 包装尺寸类型, 参数信息如下  美国站点: SS-小号标准尺寸, LS-大号标准尺寸, SO-小号大件, MO-中号大件, LO/LB-大号大件, SP-特殊大件, O-其他尺寸, ELO-超大尺寸：0至50磅, EL5O-超大尺寸：50到70磅（不含50磅）, EL7O-超大尺寸：70至150磅（不含70磅）, EL15O-超大尺寸：150磅以上（不含150磅）; 日本站点: SM-小号, ST-标准, OV-大件, SS-超大尺寸, O-其他尺寸; 加拿大站点: EN-信封装, ST-标准, SO-小号大件, MO-中号大件, LO-大号大件, SP-特殊大件, O-其他尺寸; 英国/法国/德国/意大利/西班牙站点: SL-小号信封, NL-标准信封, LL-大号信封, ELL-超大号信封, SM-小包裹, SD-标准包裹, SB-小号大件, NB-标准大件, LB-大号大件, SPO-特殊大件, O-其他尺寸 |
| `excludeBrands` | `string` | 否 | 最长 10240 | 排除品牌 |
| `filterSubNode` | `boolean` | 否 | 示例：`true`, `false` | 是否筛选子类目节点，true为筛选，false为不筛选，只有在nodeLabel 或 nodeIdPath 有值时才会生效 |
| `includeBrands` | `string` | 否 | 最长 10240 | 包含品牌 |
| `maxVariations` | `integer` | 否 |  | 最高变体数 |
| `minVariations` | `integer` | 否 |  | 最低变体数 |
| `showVariation` | `string` | 否 | 默认 `"N"`；最长 1000；示例：`Y`, `N` | 是否查询变体 |
| `excludeSellers` | `string` | 否 | 最长 10240 | 排除卖家 |
| `includeSellers` | `string` | 否 | 最长 10240 | 包含卖家 |
| `badgeBestSeller` | `string` | 否 | 最长 1000；示例：`Y`, `N`, `` | 是否有热销标识 Best Seller(Y/N) |
| `badgeNewRelease` | `string` | 否 | 最长 1000；示例：`Y`, `N`, `` | 是否有新品标识 New Release(Y/N) |
| `excludeKeywords` | `string` | 否 | 最长 10240 | 排除关键词 |
| `maxBsrGrowthRate` | `number` | 否 |  | BSR最高增长率，单位 % |
| `minBsrGrowthRate` | `number` | 否 |  | BSR最低增长率，单位 % |
| `dataSnapshotMonth` | `string` | 否 | 默认 `"nearly"`；最长 1000；示例：`nearly`, `202412`, `202501` | 亚马逊商品数据快照年月。指定查询特定历史时间点的商品数据快照，每个快照包含该月份所有在售商品的完整数据。格式：yyyyMM（如202412表示2024年12月所有在售商品的数据快照）。默认值 'nearly' 表示查询最近30天的实时数据。注意：数据快照是对特定月份亚马逊市场上所有在售商品的完整记录，用于历史分析和同期对比。仅支持查询已存在的历史快照，不支持未来日期。建议季节性分析时查询去年同期快照进行对比 |
| `maxBsrGrowthCount` | `integer` | 否 |  | 大类BSR最高增长数 |
| `maxSubNodeBsrRank` | `integer` | 否 |  | 子类目BSR最大排名 ，只有在 filterSubNode 为 true 是生效 |
| `minBsrGrowthCount` | `integer` | 否 |  | BSR最低增长数 |
| `minSubNodeBsrRank` | `integer` | 否 |  | 子类目BSR最低排名 ，只有在 filterSubNode 为 true 是生效 |
| `badgeAmazonsChoice` | `string` | 否 | 最长 1000；示例：`Y`, `N`, `` | 是否有热销标识 Amazon's Choice(Y/N) |
| `maxUnitsGrowthRate` | `number` | 否 |  | 月销量最高增长率,单位 % |
| `minUnitsGrowthRate` | `number` | 否 |  | 月销量最低增长率,单位 % |
| `hideUnlistedProduct` | `boolean` | 否 | 默认 `true`；示例：`true`, `false` | 是否隐藏已经下架的商品 |
| `maxRatingsGrowthCount` | `integer` | 否 | 最小 0 | 最高月新增评分数 |
| `minRatingsGrowthCount` | `integer` | 否 | 最小 0 | 最低月新增评分数 |
| `listedWithinLastMonths` | `integer` | 否 | 示例：`1`, `3`, `6`, `12`, `24` | 上架时间范围（月），商品上架日期距离当前日期的月份范围筛选，仅支持枚举值：1（近1个月内上架）、3（近3个月内上架）、6（近6个月内上架）、12（近12个月内上架）、24（近24个月内上架）。如果传入的是具体日期，应先计算该日期距离当前时间的月份差，并取不超过上述枚举值的最大值 |
| `maxListingQualityScore` | `number` | 否 | 最小 0 | 最高 Listing 页面质量分 |
| `minListingQualityScore` | `number` | 否 | 最小 0 | 最低 Listing 页面质量分， |

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
    "name": "/sellersprite/productSearch",
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
| `keyword` | `string` | 否 |  | 对应筛选的关键词，如果有值，则表示这批数据是通过 这个关键词 keyword 搜索出来的 |
| `message` | `string` | 否 |  | 消息 |
| `products` | `array<object>` | 否 |  | 搜索结果产品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `nodeLabel` | `string` | 否 |  | 亚马逊类目 |
| `nodeIdPath` | `string` | 否 |  | 搜索类目节点 |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |
| `dataSnapshotMonth` | `string` | 否 |  | 数据查询月份 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `bsr` | `integer` | 否 |  | BSR 排名 |
| `fba` | `number` | 否 |  | fba运费 |
| `sku` | `string` | 否 |  | sku |
| `asin` | `string` | 否 |  | asin |
| `badge` | `object` | 否 |  |  |
| `brand` | `string` | 否 |  | 品牌 |
| `price` | `number` | 否 |  | 价格 |
| `title` | `string` | 否 |  | 商品标题 |
| `nodeId` | `integer` | 否 |  | 节点id |
| `profit` | `number` | 否 |  | 利润率 |
| `rating` | `number` | 否 |  | 评分 |
| `weight` | `string` | 否 |  | 重量 |
| `asinUrl` | `string` | 否 |  | 亚马逊asin的详情网址 |
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
| `availableDate` | `string` | 否 | 格式 `date` | 上架时间(时间戳) |
| `bsrGrowthRate` | `number` | 否 |  | BSR 增长率 |
| `deliveryPrice` | `number` | 否 |  | 卖家运费 |
| `nodeLabelPath` | `string` | 否 |  | 类目路径 |
| `packageWeight` | `string` | 否 |  | 包装重量 |
| `subcategories` | `array<object>` | 否 |  | 子类目 |
| `dimensionsType` | `string` | 否 |  | 尺寸类型 |
| `badgeBestSeller` | `string` | 否 |  | Best Seller标识(Y/N) |
| `badgeNewRelease` | `string` | 否 |  | release标识(Y/N) |
| `badgeAmazonChoice` | `string` | 否 |  | amazon choice标识(Y/N) |
| `dataSnapshotMonth` | `string` | 否 |  | 数据查询月份 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `packageDimensions` | `string` | 否 |  | 包装尺寸 |
| `variant30DayUnits` | `integer` | 否 |  | 子体月销量(件数) |
| `availableDateString` | `string` | 否 |  | 上架日期(字符串) |
| `listingQualityScore` | `number` | 否 |  | listing质量得分 |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额 |
| `variant30DayRevenue` | `number` | 否 |  | 子体月销售额(金额) |
| `packageDimensionType` | `string` | 否 |  | 包装尺寸类型 |
| `variant30DayUpdatedAt` | `string` | 否 |  | 子体数据更新时间(日期) |
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
