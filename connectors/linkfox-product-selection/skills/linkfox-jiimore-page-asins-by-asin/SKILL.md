---
name: linkfox-jiimore-page-asins-by-asin
description: 按ASIN查找亚马逊同细分市场（Niche）竞品，支持点击转化率、综合转化率、点击量、销量、评论、评分、价格、毛利率等多维度筛选潜力竞品。当用户提到同细分竞品、ASIN竞品挖掘、Niche竞品分析、同类商品对标、ASIN对标分析、细分市场竞品列表、高转化竞品筛选、极目产品挖掘、niche competitor by ASIN, ASIN competitor analysis, same niche products, similar products discovery, conversion rate comparison, potential competitor screening, Jiimore ASIN mining时触发此技能。即使用户未明确提及"细分市场"或"Niche"，只要其需求涉及根据某个ASIN挖掘同细分下的竞品列表或筛选潜力竞品，也应触发此技能。
---

# 极目-亚马逊-产品挖掘（根据ASIN）

## 基本信息

- **业务工具名**：`/jiimore/pageAsinsByAsin`
- **所属分组**：极目 · 亚马逊选品
- **功能说明**：支持基于特定参考ASIN结合高转化率、点击增长率等指标的潜力爆品挖掘。
- **关键词**：极目数据, 产品挖掘, 高转化选品, 潜力爆品, 市场增长


## 何时使用

当用户意图与“极目-亚马逊-产品挖掘（根据ASIN）”匹配，或需要以下能力时使用本工具：支持基于特定参考ASIN结合高转化率、点击增长率等指标的潜力爆品挖掘。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000 | 种子 ASIN（必填，用于查询与该 ASIN 相关的商品列表） |
| `page` | `integer` | 否 | 默认 `1` | 页码 |
| `pageSize` | `integer` | 否 | 默认 `50`；最小 10；最大 100 | 每页数量 |
| `priceMax` | `number` | 否 |  | 最高商品价格 |
| `priceMin` | `number` | 否 |  | 最低商品价格 |
| `sortType` | `string` | 否 | 默认 `"desc"`；格式 `^(desc\|asc)$`；示例：`desc`, `asc` | 排序方式 |
| `fbaFeeMax` | `number` | 否 |  | 最高fba佣金 |
| `fbaFeeMin` | `number` | 否 |  | 最低fba佣金 |
| `sortField` | `string` | 否 | 默认 `"purchasedClicksT360"`；格式受正则约束（见原始 Schema）；示例：`totalReviews`, `price`, `launchDate`, `clickCountT30`, `clickCountT90`, `clickCountT7`, `clickConversionRate`, `clickConversionRateComposite` | 排序字段 |
| `countryCode` | `string` | 否 | 默认 `"US"`；格式 `^(US\|JP\|DE)$`；示例：`US`, `JP`, `DE` | 国家,使用国家简称 |
| `launchDateMax` | `string` | 否 | 最长 1000 | 最大上架时间, 格式为：yyyyMMdd000000 |
| `launchDateMin` | `string` | 否 | 最长 1000 | 最小上架时间, 格式为：yyyyMMdd000000 |
| `nicheCountMax` | `integer` | 否 |  | 最高细分市场数量 |
| `nicheCountMin` | `integer` | 否 |  | 最低细分市场数量 |
| `sellerCountry` | `string` | 否 | 格式受正则约束（见原始 Schema）；示例：`AD`, `AE`, `AF`, `AL`, `AM`, `AR`, `AS`, `AT` | 卖家国家地区编码，选择多个的情况下用逗号隔开,如：CN,US |
| `clickCountT7Max` | `integer` | 否 |  | 最高周点击量 |
| `clickCountT7Min` | `integer` | 否 |  | 最低周点击量 |
| `totalReviewsMax` | `integer` | 否 |  | 最高评论数 |
| `totalReviewsMin` | `integer` | 否 |  | 最低评论数 |
| `clickCountT30Max` | `integer` | 否 |  | 最高月点击量 |
| `clickCountT30Min` | `integer` | 否 |  | 最低月点击量 |
| `customerRatingMax` | `number` | 否 |  | 最高评分，取值范围 0.0-5.0 |
| `customerRatingMin` | `number` | 否 |  | 最低评分，取值范围 0.0-5.0 |
| `salesVolumeT360Max` | `integer` | 否 |  | 最高年销售量 |
| `salesVolumeT360Min` | `integer` | 否 |  | 最低年销售量 |
| `grossProfitMarginMax` | `number` | 否 |  | 最高毛利率 |
| `grossProfitMarginMin` | `number` | 否 |  | 最低毛利率 |
| `clickCountGrowthT7Max` | `number` | 否 |  | 最高周点击增长率,取值范围 0-1，输入 0.1 表示 10% |
| `clickCountGrowthT7Min` | `number` | 否 |  | 最低周点击增长率,取值范围 0-1，输入 0.1 表示 10% |
| `clickConversionRateMax` | `number` | 否 |  | 最高点击购买转化率,取值范围 0-1，输入 0.1 表示 10% |
| `clickConversionRateMin` | `number` | 否 |  | 最低点击购买转化率,取值范围 0-1，输入 0.1 表示 10% |
| `clickCountGrowthT30Max` | `number` | 否 |  | 最高月点击增长率,取值范围 0-1，输入 0.1 表示 10% |
| `clickCountGrowthT30Min` | `number` | 否 |  | 最低月点击增长率,取值范围 0-1，输入 0.1 表示 10% |
| `clickConversionRateCompositeMax` | `number` | 否 |  | 最高综合转化率,取值范围 0-1，输入 0.1 表示 10% |
| `clickConversionRateCompositeMin` | `number` | 否 |  | 最低综合转化率,取值范围 0-1，输入 0.1 表示 10% |


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
    "name": "/jiimore/pageAsinsByAsin",
    "arguments": {
      "asin": "B0EXAMPLE01",
      "page": 1,
      "pageSize": 50,
      "countryCode": "US",
      "sortField": "purchasedClicksT360",
      "sortType": "desc"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | ASIN 商品列表 |
| `page` | `integer` | 否 |  | 当前页 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `pages` | `integer` | 否 |  | 总页数 |
| `total` | `integer` | 否 |  | 总记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `pageSize` | `integer` | 否 |  | 每页大小 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `gpm` | `number` | 否 |  | 毛利率 |
| `asin` | `string` | 否 |  | 亚马逊商品asin |
| `link` | `string` | 否 |  | asin链接 |
| `brand` | `string` | 否 |  | 品牌 |
| `price` | `number` | 否 |  | 价格 |
| `title` | `string` | 否 |  | 产品标题 |
| `fbaFee` | `number` | 否 |  | fba佣金 |
| `images` | `array<object>` | 否 |  | 产品图(大图+小图),json格式 |
| `niches` | `array<object>` | 否 |  | top3利基市场 |
| `trends` | `array<object>` | 否 |  | 90天点击量趋势 |
| `currency` | `string` | 否 |  | 货币 |
| `sellerId` | `string` | 否 |  | 卖家ID |
| `hasMetric` | `boolean` | 否 |  | 标识是否有指标 |
| `imagesUrl` | `string` | 否 |  | 产品主图 |
| `nichesIds` | `array<any>` | 否 |  | 市场标识列表 |
| `launchDate` | `string` | 否 |  | 上架时间 |
| `nicheCount` | `integer` | 否 |  | 利基市场数 |
| `parentAsin` | `string` | 否 |  | 亚马逊商品父Asin |
| `sellerName` | `string` | 否 |  | 卖家名称 |
| `involvedNum` | `integer` | 否 |  | 覆盖的关键词数量 |
| `shippingFee` | `number` | 否 |  | Fba运费 |
| `clickCountT7` | `integer` | 否 |  | 7天点击量 |
| `currentPrice` | `number` | 否 |  | 当前价格 |
| `totalReviews` | `integer` | 否 |  | 评论数 |
| `categoryNames` | `array<any>` | 否 |  | 类目信息 |
| `clickCountT30` | `integer` | 否 |  | 30天点击量 |
| `clickCountT90` | `integer` | 否 |  | 90天点击量 |
| `marketplaceId` | `string` | 否 |  | 市场标识 |
| `customerRating` | `number` | 否 |  | 评分 |
| `lastUpdateTime` | `string` | 否 |  | 最后更新时间 |
| `sameNicheTitle` | `string` | 否 |  | 同利基市场名称 |
| `searchValueType` | `string` | 否 |  | 搜索类型[Enum values: exact(精准匹配) sameNiche(同利基市场) category(类目)] |
| `involvedFrequency` | `integer` | 否 |  | 覆盖的关键词频 |
| `bestSellersRanking` | `array<object>` | 否 |  | 利基市场排名 |
| `clickCountGrowthT7` | `number` | 否 |  | 周点击增长率 |
| `clickConversionRate` | `number` | 否 |  | 点击购买转化率(原7天点击转化率) |
| `clickCountGrowthT30` | `number` | 否 |  | 月点击增长率 |
| `purchasedClicksT360` | `integer` | 否 |  | 360天购买量 |
| `clickConversionRateType` | `string` | 否 |  | 点击转化率计算类型 |
| `clickConversionRateComposite` | `number` | 否 |  | 综合点击购买转化率 |
| `clickConversionRateCompositeType` | `string` | 否 |  | 点击转化率计算类型 |

### 嵌套输出结构：`data.niches`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `image` | `string` | 否 |  | 图片地址 |
| `demand` | `integer` | 否 |  | 市场需求 |
| `nicheId` | `string` | 否 |  | 细分市场id |
| `nicheTitle` | `string` | 否 |  | 细分市场标题 |
| `marketplaceId` | `string` | 否 |  | asin市场 |

### 嵌套输出结构：`data.trends`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `day` | `integer` | 否 |  | 日期 |
| `reviewCount` | `integer` | 否 |  | 评论数 |
| `clickCountT7` | `integer` | 否 |  | 周点击量 |
| `reviewRating` | `number` | 否 |  | 评分 |
| `averagePriceT7` | `number` | 否 |  | 周平均价格 |
| `bestSellerRanking` | `integer` | 否 |  | BestSeller排名 |
| `totalOfferDepthT7` | `integer` | 否 |  | 7天下单数 |

### 嵌套输出结构：`data.bestSellersRanking`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `rank` | `integer` | 否 |  | 排名 |
| `category` | `string` | 否 |  | 类目名称 |

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
