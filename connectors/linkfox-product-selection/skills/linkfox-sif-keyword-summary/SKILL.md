---
name: linkfox-sif-keyword-summary
description: 在给定关键词下拆解所有竞品 ASIN 的流量来源——自然搜索、SP 广告、SB 品牌广告、SBV 视频广告、SP 推荐、AC/ER/TR 等推荐位，支持按 ASIN 过滤、指定日期区间及新进流量词等筛选。当用户提到关键词流量来源、该关键词下哪些竞品在抢流量、自然流量与付费流量占比、SP广告曝光、品牌广告占比、SP推荐位、推荐位广告/非广告拆分、搜索展示分析、Amazon's Choice或编辑推荐曝光、关键词竞争格局、ASIN流量构成、keyword traffic, traffic structure analysis, search share, ad share, traffic source distribution, SIF, traffic analysis, SP recommendation, recommend position breakdown时触发此技能。即使用户未明确提及"SIF"，只要其需求涉及在某关键词下分析竞品 ASIN 的流量来源分布，也应触发此技能。
---

# SIF-关键词流量来源

## 基本信息

- **业务工具名**：`/sif/keywordSummary`
- **所属分组**：SIF · 亚马逊流量与关键词
- **功能说明**：支持关键词的流量结构分析，了解该词下自然搜索、SP广告及品牌广告的竞争格局。
- **关键词**：SIF, 关键词流量, 流量结构, 搜索份额, 广告占比, 流量来源


## 何时使用

当用户意图与“SIF-关键词流量来源”匹配，或需要以下能力时使用本工具：支持关键词的流量结构分析，了解该词下自然搜索、SP广告及品牌广告的竞争格局。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `desc` | `boolean` | 否 | 默认 `true` | 是否降序，默认传 true  |
| `asins` | `string` | 否 | 最长 1000；示例：`B01NBNDC1T`, `B01NBNDC1T,B09VLJJPL6` | ASIN 过滤列表，多个用英文逗号分隔；不传则返回该关键词下所有 ASIN |
| `last7d` | `boolean` | 否 | 默认 `true` | 是否取最近7天数据，默认 true；传 false 时使用 startDate/endDate 区间 |
| `sortBy` | `string` | 否 | 格式受正则约束（见原始 Schema）；示例：``, `totalKeywordNum`, `naturalKeywordNum`, `brandKeywordNum`, `vedioKeywordNum`, `acKeywordNum`, `erKeywordNum`, `trKeywordNum` | 排序字段 |
| `country` | `string` | 否 | 默认 `"US"`；格式 `US\|UK\|DE\|CA\|JP\|FR\|ES\|IT\|MX\|AU\|AE\|BR\|SA`；示例：`US`, `UK`, `DE`, `CA`, `JP`, `FR`, `ES`, `IT` | 国家站点 |
| `endDate` | `string` | 否 | 最长 1000；示例：`2026-04-11` | 结束日期 yyyy-MM-dd（与 startDate 配套） |
| `pageNum` | `integer` | 否 | 默认 `1` | 页码 |
| `pageSize` | `integer` | 否 | 默认 `100`；最小 10；最大 100 | 每页数量，最小10，最大100，默认也是100 |
| `condition` | `string` | 否 | 格式受正则约束（见原始 Schema）；示例：`nfPosition`, `isSpAd`, `isVedioAd`, `isBrandAd`, `isPPCAd`, `isSearchRecommend`, `acAd`, `totalPeriod.in` | 条件筛选,每次只能传一个 |
| `startDate` | `string` | 否 | 最长 1000；示例：`2026-04-05` | 开始日期 yyyy-MM-dd（last7d=false 时生效，不填取系统最新整周） |
| `searchKeyword` | `string` | 是 | 最长 1000 | 搜索关键词，尽量翻译成对应国家站点的语言 |


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
    "name": "/sif/keywordSummary",
    "arguments": {
      "searchKeyword": "wireless headphones",
      "pageSize": 100
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

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN编码.亚马逊商品标准识别码（Amazon Standard Identification Number） |
| `keyword` | `string` | 否 |  | 关键词 |
| `productPrice` | `number` | 否 |  | 商品售价.当前亚马逊页面显示的商品价格 |
| `productTitle` | `string` | 否 |  | 商品标题.亚马逊页面显示的完整商品标题 |
| `productImageUrl` | `string` | 否 |  | 商品主图URL.商品在亚马逊页面上的主要展示图片链接 |
| `isVariantProduct` | `boolean` | 否 |  | 是否为变体.true=该ASIN是父ASIN下的变体（如不同颜色、尺寸），false=独立ASIN或父ASIN |
| `ppcTrafficSources` | `array<any>` | 否 |  | PPC付费广告流量来源标记.包含：sp广告（Sponsored Products）、头部品牌广告（Top Brand Ad）、底部品牌广告（Bottom Brand Ad）、视频广告（Video Ad） |
| `productStarRating` | `number` | 否 |  | 商品星级（0-5 星） |
| `productUpdateTime` | `string` | 否 |  | 产品更新时间.格式 yyyy-MM-dd HH:mm:ss |
| `productRatingScore` | `number` | 否 |  | 商品评分 |
| `totalExposureRatio` | `number` | 否 |  | 总流量份额 |
| `totalExposureScore` | `number` | 否 |  | 总曝光分数.该商品在所有关键词下的曝光量综合评分，分数越高表示整体曝光量越大 |
| `customerRatingCount` | `integer` | 否 |  | 客户评分总数.该商品在亚马逊上获得的客户评分总数 |
| `dataPeriodStartDate` | `string` | 否 |  | 数据周期起始日期 (yyyy-MM-dd) |
| `brandAdExposureRatio` | `number` | 否 |  | 品牌广告曝光占比.品牌广告曝光分数占总曝光分数的百分比 |
| `brandAdExposureScore` | `number` | 否 |  | 品牌广告曝光总分.该商品在品牌广告位的曝光量综合评分 |
| `videoAdExposureRatio` | `number` | 否 |  | 视频广告曝光占比.视频广告曝光分数占总曝光分数的百分比 |
| `videoAdExposureScore` | `number` | 否 |  | 视频广告曝光总分.该商品在视频广告位的曝光量综合评分 |
| `topRatedExposureRatio` | `number` | 否 |  | Top Rated推荐曝光占比.TR推荐曝光分数占总曝光分数的百分比 |
| `topRatedExposureScore` | `number` | 否 |  | Top Rated推荐曝光总分.该商品在TR推荐位的曝光量综合评分 |
| `promotionalDealSources` | `array<any>` | 否 |  | 促销活动流量来源标记.包含：优惠券（Coupon）、限时优惠（Limited Time Deal）、30天内最低价（Lowest Price in 30 Days）等 |
| `recommendAdExposureRatio` | `number` | 否 |  | 推荐位广告流量份额 |
| `recommendAdExposureScore` | `number` | 否 |  | 推荐位广告曝光分数 |
| `keywordTotalExposureScore` | `number` | 否 |  | 关键词总得分 |
| `amazonsChoiceExposureRatio` | `number` | 否 |  | Amazon's Choice曝光占比.AC推荐曝光分数占总曝光分数的百分比 |
| `amazonsChoiceExposureScore` | `number` | 否 |  | Amazon's Choice曝光总分.该商品作为AC推荐商品的曝光量综合评分 |
| `naturalSearchExposureRatio` | `number` | 否 |  | 自然搜索曝光占比.自然搜索曝光分数占总曝光分数的百分比，反映自然流量的比重 |
| `naturalSearchExposureScore` | `number` | 否 |  | 自然搜索曝光总分.该商品在自然搜索结果位置的曝光量综合评分 |
| `amazonRecommendationSources` | `array<any>` | 否 |  | 亚马逊推荐流量来源标记.包含：Best Seller榜单、Amazon's Choice推荐、编辑推荐（ER）、高评分推荐（TR）、高频购买推荐（TRFOB）等 |
| `keywordBrandAdExposureScore` | `number` | 否 |  | 关键词品牌广告得分 |
| `keywordNaturalExposureScore` | `number` | 否 |  | 关键词自然得分 |
| `keywordVideoAdExposureScore` | `number` | 否 |  | 关键词视频广告得分 |
| `naturalSearchTrafficSources` | `array<any>` | 否 |  | 自然搜索流量来源标记.如果该数组不为空，表示商品有自然搜索流量。数组内容标记具体的自然搜索类型 |
| `recommendNonadExposureRatio` | `number` | 否 |  | 推荐位非广告流量份额 |
| `recommendNonadExposureScore` | `number` | 否 |  | 推荐位非广告曝光分数 |
| `keywordRecommendExposureScore` | `number` | 否 |  | 关键词推荐位得分 |
| `recommendPositionExposureScore` | `number` | 否 |  | 推荐位曝光总分 |
| `sponsoredProductsExposureRatio` | `number` | 否 |  | SP广告曝光占比.SP广告曝光分数占总曝光分数的百分比，反映付费广告流量的比重 |
| `sponsoredProductsExposureScore` | `number` | 否 |  | SP广告曝光总分.该商品在SP广告位的曝光量综合评分 |
| `keywordRecommendAdExposureScore` | `number` | 否 |  | 关键词推荐位广告得分 |
| `comprehensiveNaturalExposureRatio` | `number` | 否 |  | 综合自然流量份额 |
| `comprehensiveNaturalExposureScore` | `number` | 否 |  | 综合自然流量得分.自然搜索 + 推荐位非广告 |
| `keywordAmazonsChoiceExposureScore` | `number` | 否 |  | 关键词Amazon's Choice得分 |
| `keywordRecommendNonadExposureScore` | `number` | 否 |  | 关键词推荐位非广告得分 |
| `editorialRecommendationsExposureRatio` | `number` | 否 |  | Editorial Recommendations曝光占比.ER推荐曝光分数占总曝光分数的百分比 |
| `editorialRecommendationsExposureScore` | `number` | 否 |  | Editorial Recommendations曝光总分.该商品在编辑推荐位的曝光量综合评分 |
| `keywordSponsoredProductsExposureScore` | `number` | 否 |  | 关键词SP广告得分 |
| `keywordComprehensiveNaturalExposureScore` | `number` | 否 |  | 关键词综合自然得分.自然 + 推荐位非广告 |

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
