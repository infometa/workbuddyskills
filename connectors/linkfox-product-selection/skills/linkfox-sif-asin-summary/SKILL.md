---
name: linkfox-sif-asin-summary
description: 使用SIF（搜索情报框架）数据分析ASIN的流量来源构成与曝光分布，覆盖本期/上期/新进/退出周期对比。当用户提到ASIN流量来源、流量结构分析、自然流量与付费流量占比、曝光得分拆解、周期对比、新进/退出流量词、竞品流量分析、SP广告关键词数量、品牌广告曝光、Amazon's Choice曝光、编辑推荐曝光、Top Rated曝光、视频广告曝光、自然搜索曝光比例、PPC流量来源、促销秒杀流量来源、推荐位结构拆解、ASIN traffic analysis, traffic sources, organic traffic share, ad traffic share, exposure analysis, traffic structure, period-over-period comparison, keyword churn, SIF时触发此技能。即使用户未明确提及"SIF"，只要其需求涉及分析ASIN的流量来源、曝光渠道分布、跨周期对比或竞品流量结构对比，也应触发此技能。
---

# SIF-ASIN流量来源

## 基本信息

- **业务工具名**：`/sif/asinSummary`
- **所属分组**：SIF · 亚马逊流量与关键词
- **功能说明**：支持竞品流量来源拆解，分析其自然搜索、广告投放及推荐流量的占比结构。
- **关键词**：SIF, ASIN流量, 流量占比, 曝光分析, 竞品流量结构


## 何时使用

当用户意图与“SIF-ASIN流量来源”匹配，或需要以下能力时使用本工具：支持竞品流量来源拆解，分析其自然搜索、广告投放及推荐流量的占比结构。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `desc` | `boolean` | 否 | 默认 `true` | 是否降序，默认传 true  |
| `last7d` | `boolean` | 否 | 默认 `true` | 是否取最近7天数据，默认 true；传 false 时使用 startDate/endDate 区间 |
| `sortBy` | `string` | 否 | 格式受正则约束（见原始 Schema）；示例：``, `totalKeywordNum`, `naturalKeywordNum`, `brandKeywordNum`, `vedioKeywordNum`, `acKeywordNum`, `erKeywordNum`, `trKeywordNum` | 排序字段 |
| `country` | `string` | 否 | 默认 `"US"`；格式 `US\|UK\|DE\|CA\|JP\|FR\|ES\|IT\|MX\|AU\|AE\|BR\|SA`；示例：`US`, `UK`, `DE`, `CA`, `JP`, `FR`, `ES`, `IT` | 国家站点 |
| `endDate` | `string` | 否 | 最长 1000；示例：`2026-03-14` | 结束日期 yyyy-MM-dd（与 startDate 配套） |
| `pageNum` | `integer` | 否 | 默认 `1` | 页码 |
| `pageSize` | `integer` | 否 | 默认 `10000`；最小 10；最大 10000 | 每页数量，最小10，最大10000，默认10000 |
| `startDate` | `string` | 否 | 最长 1000；示例：`2026-03-08` | 开始日期 yyyy-MM-dd（last7d=false 时生效，不填取系统最新周） |
| `conditions` | `string` | 否 | 格式 `^(nf\|sp\|sb\|sbv\|ad\|acAd\|totalPeriod\.in)(,(nf\|sp\|sb\|sbv\|ad\|acAd\|totalPeriod\.in))*$`；示例：`nf`, `sp`, `sb`, `sbv`, `ad`, `acAd`, `totalPeriod.in` | 条件筛选,多个条件以英文逗号隔开（v2 新增） |
| `searchValue` | `string` | 是 | 最长 1000 | 搜索值，ASIN码，多个用逗号分隔，最多10个ASIN |


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
    "name": "/sif/asinSummary",
    "arguments": {
      "searchValue": "example",
      "pageSize": 10000
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 消息 |
| `code` | `string` | 否 |  | 返回码 |
| `data` | `array<object>` | 否 |  | 返回数据 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `title` | `string` | 否 |  | 标题 |
| `total` | `integer` | 否 |  | 本次实际返回的数据数量 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costTime` | `integer` | 否 |  | 耗时 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `variantsNum` | `integer` | 否 |  | 有关键词的变体商品数量 |
| `isParentAsin` | `boolean` | 否 |  | 搜索的是否是pasin |
| `noKeywordVariantsNum` | `integer` | 否 |  | 无关键词的变体商品数量 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN编码.亚马逊商品标准识别码（Amazon Standard Identification Number） |
| `isMonitored` | `boolean` | 否 |  | 是否已监控.true=该商品在监控列表中，false=未监控 |
| `productPrice` | `number` | 否 |  | 商品售价.当前亚马逊页面显示的商品价格 |
| `productTitle` | `string` | 否 |  | 商品标题.亚马逊页面显示的完整商品标题 |
| `productCategory` | `string` | 否 |  | 商品类目.该商品在亚马逊上所属的行业类目 |
| `productFeatures` | `array<any>` | 否 |  | 商品特征列表.商品在亚马逊页面上列出的主要特性和卖点 |
| `productImageUrl` | `string` | 否 |  | 商品主图URL.商品在亚马逊页面上的主要展示图片链接 |
| `isVariantProduct` | `boolean` | 否 |  | 是否为变体.true=该ASIN是父ASIN下的变体（如不同颜色、尺寸），false=独立ASIN或父ASIN |
| `ppcTrafficSources` | `array<any>` | 否 |  | PPC付费广告流量来源标记.包含：sp广告（Sponsored Products）、头部品牌广告（Top Brand Ad）、底部品牌广告（Bottom Brand Ad）、视频广告（Video Ad） |
| `productStarRating` | `number` | 否 |  | 商品星级（0-5 星） |
| `productRatingScore` | `number` | 否 |  | 商品评分数值（0-5，亚马逊页面显示数值） |
| `totalExposureScore` | `number` | 否 |  | 总曝光分数.该商品在所有关键词下的曝光量综合评分，分数越高表示整体曝光量越大 |
| `brandAdKeywordCount` | `integer` | 否 |  | 品牌广告关键词总数.该商品在品牌广告位（包括页面顶部和底部）展示的关键词总数 |
| `customerRatingCount` | `integer` | 否 |  | 客户评分总数.该商品在亚马逊上获得的客户评分总数 |
| `dataPeriodStartDate` | `string` | 否 |  | 数据周期起始日期 (yyyy-MM-dd) |
| `monitoringStartTime` | `string` | 否 |  | 商品关注时间.该商品被添加到监控系统的时间 |
| `videoAdKeywordCount` | `integer` | 否 |  | 视频广告关键词数量.该商品在视频广告位展示的关键词总数 |
| `brandAdExposureRatio` | `number` | 否 |  | 品牌广告曝光占比.品牌广告曝光分数占总曝光分数的百分比 |
| `brandAdExposureScore` | `number` | 否 |  | 品牌广告曝光总分.该商品在品牌广告位的曝光量综合评分 |
| `topRatedKeywordCount` | `integer` | 否 |  | Top Rated推荐关键词数量.该商品在高评分推荐位展示的关键词总数 |
| `videoAdExposureRatio` | `number` | 否 |  | 视频广告曝光占比.视频广告曝光分数占总曝光分数的百分比 |
| `videoAdExposureScore` | `number` | 否 |  | 视频广告曝光总分.该商品在视频广告位的曝光量综合评分 |
| `recommendKeywordCount` | `integer` | 否 |  | 推荐位关键词总数 |
| `topRatedExposureRatio` | `number` | 否 |  | Top Rated推荐曝光占比.TR推荐曝光分数占总曝光分数的百分比 |
| `topRatedExposureScore` | `number` | 否 |  | Top Rated推荐曝光总分.该商品在TR推荐位的曝光量综合评分 |
| `promotionalDealSources` | `array<any>` | 否 |  | 促销活动流量来源标记.包含：优惠券（Coupon）、限时优惠（Limited Time Deal）、30天内最低价（Lowest Price in 30 Days）等 |
| `topBrandAdKeywordCount` | `integer` | 否 |  | 页面顶部品牌广告关键词数量.该商品在搜索结果页面顶部品牌广告位展示的关键词总数 |
| `totalExposureScorePrev` | `number` | 否 |  | 上周期总曝光分数 |
| `recommendAdKeywordCount` | `integer` | 否 |  | 推荐位广告关键词数量 |
| `brandAdExposureScorePrev` | `number` | 否 |  | 上周期品牌广告曝光分数 |
| `recentMonthlySalesBucket` | `string` | 否 |  | 近一月销量桶（仅 keywordSummary 路径有值，形如 "300+" 或 "1,000+"） |
| `recommendAdExposureScore` | `number` | 否 |  | 推荐位广告曝光分数 |
| `totalTrafficKeywordCount` | `integer` | 否 |  | 流量关键词总数.该商品在所有渠道（自然搜索+各类广告位+推荐位）被发现的关键词总数 |
| `videoAdExposureScorePrev` | `number` | 否 |  | 上周期视频广告曝光分数 |
| `amazonsChoiceKeywordCount` | `integer` | 否 |  | Amazon's Choice关键词数量.该商品获得Amazon's Choice（亚马逊精选）推荐标志的关键词总数 |
| `bottomBrandAdKeywordCount` | `integer` | 否 |  | 页面底部品牌广告关键词数量.该商品在搜索结果页面底部品牌广告位展示的关键词总数 |
| `naturalSearchKeywordCount` | `integer` | 否 |  | 自然搜索关键词数量.该商品在自然搜索结果中被发现的关键词总数（不包括广告位） |
| `amazonsChoiceExposureRatio` | `number` | 否 |  | Amazon's Choice曝光占比.AC推荐曝光分数占总曝光分数的百分比 |
| `amazonsChoiceExposureScore` | `number` | 否 |  | Amazon's Choice曝光总分.该商品作为AC推荐商品的曝光量综合评分 |
| `naturalSearchExposureRatio` | `number` | 否 |  | 自然搜索曝光占比.自然搜索曝光分数占总曝光分数的百分比，反映自然流量的比重 |
| `naturalSearchExposureScore` | `number` | 否 |  | 自然搜索曝光总分.该商品在自然搜索结果位置的曝光量综合评分 |
| `recommendNonadKeywordCount` | `integer` | 否 |  | 推荐位非广告关键词数量 |
| `totalTrafficKeywordCountIn` | `integer` | 否 |  | 本周期新进流量关键词数量 |
| `amazonRecommendationSources` | `array<any>` | 否 |  | 亚马逊推荐流量来源标记.包含：Best Seller榜单、Amazon's Choice推荐、编辑推荐（ER）、高评分推荐（TR）、高频购买推荐（TRFOB）等 |
| `amazonsChoiceKeywordCountIn` | `integer` | 否 |  | 本周期新进Amazon's Choice关键词数量 |
| `naturalSearchKeywordCountIn` | `integer` | 否 |  | 本周期新进自然搜索关键词数量 |
| `naturalSearchTrafficSources` | `array<any>` | 否 |  | 自然搜索流量来源标记.如果该数组不为空，表示商品有自然搜索流量。数组内容标记具体的自然搜索类型 |
| `nonAcRecommendExposureScore` | `number` | 否 |  | 非AC推荐位曝光分数 |
| `recommendNonadExposureScore` | `number` | 否 |  | 推荐位非广告曝光分数 |
| `totalTrafficKeywordCountOut` | `integer` | 否 |  | 本周期退出流量关键词数量 |
| `amazonsChoiceKeywordCountOut` | `integer` | 否 |  | 本周期退出Amazon's Choice关键词数量 |
| `frequentlyBoughtKeywordCount` | `integer` | 否 |  | 高频购买推荐关键词数量.该商品在Top Rated Frequently Bought（高评分高频购买）推荐位展示的关键词总数 |
| `naturalSearchKeywordCountOut` | `integer` | 否 |  | 本周期退出自然搜索关键词数量 |
| `totalTrafficKeywordCountPrev` | `integer` | 否 |  | 上周期流量关键词总数 |
| `naturalSearchKeywordCountPrev` | `integer` | 否 |  | 上周期自然搜索关键词数量 |
| `sponsoredProductsKeywordCount` | `integer` | 否 |  | SP广告关键词数量.该商品在Sponsored Products（赞助商品）广告位展示的关键词总数 |
| `amazonsChoiceExposureScorePrev` | `number` | 否 |  | 上周期Amazon's Choice曝光分数 |
| `naturalSearchExposureScorePrev` | `number` | 否 |  | 上周期自然搜索曝光分数 |
| `recommendPositionExposureScore` | `number` | 否 |  | 推荐位曝光总分 |
| `sponsoredProductsExposureRatio` | `number` | 否 |  | SP广告曝光占比.SP广告曝光分数占总曝光分数的百分比，反映付费广告流量的比重 |
| `sponsoredProductsExposureScore` | `number` | 否 |  | SP广告曝光总分.该商品在SP广告位的曝光量综合评分 |
| `sponsoredProductsExposureScorePrev` | `number` | 否 |  | 上周期SP广告曝光分数 |
| `editorialRecommendationsKeywordCount` | `integer` | 否 |  | Editorial Recommendations关键词数量.该商品在编辑推荐位展示的关键词总数 |
| `editorialRecommendationsExposureRatio` | `number` | 否 |  | Editorial Recommendations曝光占比.ER推荐曝光分数占总曝光分数的百分比 |
| `editorialRecommendationsExposureScore` | `number` | 否 |  | Editorial Recommendations曝光总分.该商品在编辑推荐位的曝光量综合评分 |

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
