---
name: linkfox-junglescout-keyword-by-keyword
description: Jungle Scout关键词拓展工具，根据种子关键词扩展出相关关键词列表，包含搜索量、趋势、PPC竞价、排名难度等数据，覆盖美国、英国、德国、日本等10个亚马逊站点。当用户提到关键词拓展、关键词挖掘、长尾词挖掘、相关关键词、关键词建议、拓词、PPC竞价研究、关键词竞争度、关键词发现、Jungle Scout关键词、keyword expansion, keyword discovery, keyword scout, related keywords, long-tail keywords, keyword suggestions, PPC bid research, keyword competition, seed keyword expansion, keyword mining时触发此技能。即使用户未明确提及"Jungle Scout"，只要其需求涉及从一个种子关键词出发找到更多相关关键词及其搜索量、竞争度等指标，也应触发此技能。
---

# 根据关键词扩展关键词信息

## 基本信息

- **业务工具名**：`/tool-jungle-scout/keywords/by-keyword`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：根据关键词扩展关键词信息


## 何时使用

当用户意图与“根据关键词扩展关键词信息”匹配，或需要以下能力时使用本工具：根据关键词扩展关键词信息

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `sort` | `string` | 否 | 最长 1000；示例：`name`, `-name`, `dominant_category`, `-dominant_category`, `monthly_trend`, `-monthly_trend`, `quarterly_trend`, `-quarterly_trend` | 排序字段。可选值: name, -name, dominant_category, -dominant_category, monthly_trend, -monthly_trend, quarterly_trend, -quarterly_trend, monthly_search_volume_exact, -monthly_search_volume_exact, monthly_search_volume_broad, -monthly_search_volume_broad, recommended_promotions, -recommended_promotions, sp_brand_ad_bid, -sp_brand_ad_bid, ppc_bid_broad, -ppc_bid_broad, ppc_bid_exact, -ppc_bid_exact, ease_of_ranking_score, -ease_of_ranking_score, relevancy_score, -relevancy_score, organic_product_count, -organic_product_count。默认: -monthly_search_volume_exact |
| `needCount` | `integer` | 否 |  | 需要返回的总条数(系统内部自动分页拉取) |
| `marketplace` | `string` | 是 | 最长 1000；示例：`us`, `uk`, `de`, `in`, `ca`, `fr`, `it`, `es` | 目标市场代码 |
| `searchTerms` | `string` | 是 | 最长 1000 | 种子关键词(单个字符串) |
| `maxWordCount` | `integer` | 否 |  | 最大词数 |
| `minWordCount` | `integer` | 否 |  | 最小词数 |
| `maxOrganicProductCount` | `integer` | 否 |  | 最大自然产品数 |
| `minOrganicProductCount` | `integer` | 否 |  | 最小自然产品数 |
| `maxMonthlySearchVolumeBroad` | `integer` | 否 |  | 最大广泛搜索量 |
| `maxMonthlySearchVolumeExact` | `integer` | 否 |  | 最大精确搜索量 |
| `minMonthlySearchVolumeBroad` | `integer` | 否 |  | 最小广泛搜索量 |
| `minMonthlySearchVolumeExact` | `integer` | 否 |  | 最小精确搜索量 |


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
    "name": "/tool-jungle-scout/keywords/by-keyword",
    "arguments": {
      "marketplace": "us",
      "searchTerms": "example"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `keywordInfoList` | `array<object>` | 否 |  | 关键词信息列表 |

### 嵌套输出结构：`keywordInfoList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `name` | `string` | 否 |  | 关键词名称 |
| `country` | `string` | 否 |  | 国家代码 |
| `ppcBidBroad` | `number` | 否 |  | 广泛竞价 |
| `ppcBidExact` | `number` | 否 |  | 精确竞价 |
| `monthlyTrend` | `number` | 否 |  | 月度趋势(%) |
| `spBrandAdBid` | `number` | 否 |  | 品牌广告竞价 |
| `quarterlyTrend` | `number` | 否 |  | 季度趋势(%) |
| `relevancyScore` | `integer` | 否 |  | 相关性评分 |
| `dominantCategory` | `string` | 否 |  | 主导分类 |
| `easeOfRankingScore` | `integer` | 否 |  | 排名难度分 |
| `organicProductCount` | `integer` | 否 |  | 自然产品数 |
| `recommendedPromotions` | `integer` | 否 |  | 推荐促销次数 |
| `sponsoredProductCount` | `integer` | 否 |  | 赞助产品数 |
| `monthlySearchVolumeBroad` | `integer` | 否 |  | 广泛月搜索量 |
| `monthlySearchVolumeExact` | `integer` | 否 |  | 精确月搜索量 |

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
