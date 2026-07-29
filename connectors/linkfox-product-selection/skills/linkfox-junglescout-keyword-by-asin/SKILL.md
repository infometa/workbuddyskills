---
name: linkfox-junglescout-keyword-by-asin
description: Jungle Scout根据ASIN反查关键词，输入最多10个ASIN获取其在亚马逊搜索结果中出现的所有关键词及搜索量、竞争度、PPC竞价等数据，覆盖10个站点。当用户提到ASIN反查关键词、反查词、ASIN关键词挖掘、竞品关键词、ASIN流量词、反向ASIN查询、ASIN搜索词、关键词拓展、ASIN词库、竞品流量分析、reverse ASIN lookup, keyword by ASIN, ASIN keyword mining, competitor keywords, ASIN traffic keywords, reverse keyword lookup, ASIN search terms, keyword expansion时触发此技能。即使用户未明确提及"Jungle Scout"或"反查"，只要其需求涉及通过ASIN查找相关关键词或分析竞品关键词，也应触发此技能。
---

# 根据ASIN列表扩展关键词信息

## 基本信息

- **业务工具名**：`/tool-jungle-scout/keywords/by-asin`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：根据ASIN列表扩展关键词信息：返回所查ASIN在亚马逊搜索结果中出现的关键词；单次最多10个ASIN


## 何时使用

当用户意图与“根据ASIN列表扩展关键词信息”匹配，或需要以下能力时使用本工具：根据ASIN列表扩展关键词信息：返回所查ASIN在亚马逊搜索结果中出现的关键词；单次最多10个ASIN

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `sort` | `string` | 否 | 最长 1000；示例：`name`, `-name`, `dominant_category`, `-dominant_category`, `monthly_trend`, `-monthly_trend`, `quarterly_trend`, `-quarterly_trend` | 排序字段。可选值: name, -name, dominant_category, -dominant_category, monthly_trend, -monthly_trend, quarterly_trend, -quarterly_trend, monthly_search_volume_exact, -monthly_search_volume_exact, monthly_search_volume_broad, -monthly_search_volume_broad, recommended_promotions, -recommended_promotions, sp_brand_ad_bid, -sp_brand_ad_bid, ppc_bid_broad, -ppc_bid_broad, ppc_bid_exact, -ppc_bid_exact, ease_of_ranking_score, -ease_of_ranking_score, relevancy_score, -relevancy_score, organic_product_count, -organic_product_count。默认: -monthly_search_volume_exact |
| `asins` | `string` | 是 | 最长 1000 | 要分析的ASIN列表(1-10个有效ASIN), 多个asin使用逗号分隔 |
| `needCount` | `integer` | 否 |  | 需要返回的总条数(系统内部自动分页拉取) |
| `marketplace` | `string` | 是 | 最长 1000；示例：`us`, `uk`, `de`, `in`, `ca`, `fr`, `it`, `es` | 目标市场代码 |
| `maxWordCount` | `integer` | 否 |  | 关键词最多词数(1-99999) |
| `minWordCount` | `integer` | 否 |  | 关键词最少词数(1-99999) |
| `includeVariants` | `boolean` | 否 | 示例：`false`, `true` | 是否包含变体产品关键词 |
| `maxOrganicProductCount` | `integer` | 否 |  | 最大自然搜索结果数(1-99999) |
| `minOrganicProductCount` | `integer` | 否 |  | 最小自然搜索结果数(1-99999) |
| `maxMonthlySearchVolumeBroad` | `integer` | 否 |  | 最大广泛月搜索量(1-999999) |
| `maxMonthlySearchVolumeExact` | `integer` | 否 |  | 最大精确月搜索量(1-999999) |
| `minMonthlySearchVolumeBroad` | `integer` | 否 |  | 最小广泛月搜索量(1-999999) |
| `minMonthlySearchVolumeExact` | `integer` | 否 |  | 最小精确月搜索量(1-999999) |


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
    "name": "/tool-jungle-scout/keywords/by-asin",
    "arguments": {
      "marketplace": "us",
      "asins": "B0EXAMPLE01"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `keywordInfoList` | `array<object>` | 否 |  | 按ASIN扩展的关键词信息列表 |

### 嵌套输出结构：`keywordInfoList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `name` | `string` | 否 |  | 关键词名称 |
| `country` | `string` | 否 |  | 国家市场代码 |
| `updatedAt` | `string` | 否 |  | 数据更新时间(UTC) |
| `organicRank` | `integer` | 否 |  | 自然排名位置 |
| `overallRank` | `integer` | 否 |  | 综合排名 |
| `ppcBidBroad` | `number` | 否 |  | 广泛匹配PPC竞价(USD) |
| `ppcBidExact` | `number` | 否 |  | 精确匹配PPC竞价(USD) |
| `primaryAsin` | `string` | 否 |  | 主要ASIN |
| `monthlyTrend` | `number` | 否 |  | 月度搜索趋势(%) |
| `spBrandAdBid` | `number` | 否 |  | 品牌广告建议竞价(USD) |
| `sponsoredRank` | `integer` | 否 |  | 赞助排名位置 |
| `quarterlyTrend` | `number` | 否 |  | 季度搜索趋势(%) |
| `relevancyScore` | `integer` | 否 |  | 相关性评分(0-100) |
| `dominantCategory` | `string` | 否 |  | 主导产品类别 |
| `easeOfRankingScore` | `integer` | 否 |  | 排名难度评分(0-100) |
| `organicProductCount` | `integer` | 否 |  | 自然搜索结果数 |
| `competitorOrganicRank` | `array<object>` | 否 |  | 竞品自然排名列表 |
| `recommendedPromotions` | `integer` | 否 |  | 推荐推广次数 |
| `sponsoredProductCount` | `integer` | 否 |  | 赞助产品数量 |
| `competitorSponsoredRank` | `array<object>` | 否 |  | 竞品赞助排名列表 |
| `relativeOrganicPosition` | `integer` | 否 |  | 相对自然位次 |
| `avgCompetitorOrganicRank` | `number` | 否 |  | 平均竞品自然排名 |
| `monthlySearchVolumeBroad` | `integer` | 否 |  | 广泛匹配月搜索量 |
| `monthlySearchVolumeExact` | `integer` | 否 |  | 精确匹配月搜索量 |
| `organicRankingAsinsCount` | `integer` | 否 |  | 自然排名ASIN数 |
| `relativeSponsoredPosition` | `integer` | 否 |  | 相对赞助位次 |
| `avgCompetitorSponsoredRank` | `number` | 否 |  | 平均竞品赞助排名 |
| `sponsoredRankingAsinsCount` | `integer` | 否 |  | 赞助排名ASIN数 |
| `variationLowestOrganicRank` | `integer` | 否 |  | 变体最低自然排名 |
| `variationLowestSponsoredRank` | `integer` | 否 |  | 变体最低赞助排名 |

### 嵌套输出结构：`keywordInfoList.competitorOrganicRank`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `organicRank` | `integer` | 否 |  | 自然排名 |

### 嵌套输出结构：`keywordInfoList.competitorSponsoredRank`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `sponsoredRank` | `integer` | 否 |  | 赞助排名 |

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
