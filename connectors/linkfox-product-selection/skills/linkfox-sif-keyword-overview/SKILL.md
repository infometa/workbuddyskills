---
name: linkfox-sif-keyword-overview
description: 亚马逊市场关键词竞争度的SIF概览分析。当用户提到关键词竞争度、供需比、竞品数量、关键词搜索量估算、市场竞争力评估、关键词热度排名、广告竞争分析、某个关键词下的商品数量、keyword competition, supply-demand ratio, competitor count, search popularity, market competition analysis, SIF, keyword overview时触发此技能。即使用户未明确说"SIF"，只要其需求涉及评估亚马逊上关键词层面的竞争强度、供需平衡或搜索结果商品数量，也应触发此技能。
---

# SIF-关键词竞品数量

## 基本信息

- **业务工具名**：`/sif/keywordOverview`
- **所属分组**：SIF · 亚马逊流量与关键词
- **功能说明**：支持关键词的市场竞争度评估，通过统计竞品数量计算供需比。
- **关键词**：SIF, 关键词竞品, 供需比, 市场竞争度, 搜索热度


## 何时使用

当用户意图与“SIF-关键词竞品数量”匹配，或需要以下能力时使用本工具：支持关键词的市场竞争度评估，通过统计竞品数量计算供需比。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `last7d` | `boolean` | 否 | 默认 `true` | 是否取最近7天数据，默认 true；传 false 时使用 startDate/endDate 区间 |
| `country` | `string` | 否 | 默认 `"US"`；格式 `US\|UK\|DE\|CA\|JP\|FR\|ES\|IT\|MX\|AU\|AE\|BR\|SA`；示例：`US`, `UK`, `DE`, `CA`, `JP`, `FR`, `ES`, `IT` | 国家站点 |
| `endDate` | `string` | 否 | 最长 1000；示例：`2025-11-15` | 结束日期 yyyy-MM-dd（与 startDate 配套） |
| `keyword` | `string` | 是 | 最长 1000 | 关键词，尽量翻译成对应国家站点的语言 |
| `startDate` | `string` | 否 | 最长 1000；示例：`2025-11-13` | 开始日期 yyyy-MM-dd（last7d=false 时生效） |


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
    "name": "/sif/keywordOverview",
    "arguments": {
      "keyword": "wireless headphones"
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
| `total` | `integer` | 否 |  | 数据总量。注意：本接口通常只返回单条数据，total 通常为1 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costTime` | `integer` | 否 |  | 耗时 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `keyword` | `string` | 否 |  | 关键词.搜索查询的关键词文本 |
| `dataPeriodEndDate` | `string` | 否 |  | 数据周期结束日期.本次返回数据对应的 ABA 周结束日期 (yyyy-MM-dd) |
| `recAdProductCount` | `integer` | 否 |  | 推荐位广告商品数量.在该关键词下推荐位中属于广告的商品数量 |
| `supplyDemandRatio` | `number` | 否 |  | 供需比率.供应与需求的比率，计算公式：搜索结果商品数 / 月搜索量，数值越小表示竞争越小、机会越大 |
| `brandAdProductCount` | `integer` | 否 |  | 品牌广告商品数量.在该关键词下投放品牌广告（Brand Ads）的商品数量 |
| `dataPeriodStartDate` | `string` | 否 |  | 数据周期起始日期.本次返回数据对应的 ABA 周起始日期 (yyyy-MM-dd) |
| `videoAdProductCount` | `integer` | 否 |  | 视频广告商品数量.在该关键词下投放视频广告（Video Ads）的商品数量 |
| `recNonadProductCount` | `integer` | 否 |  | 推荐位非广告商品数量.在该关键词下推荐位中属于非广告（自然）的商品数量 |
| `topRatedProductCount` | `integer` | 否 |  | Top Rated推荐商品数量.在该关键词下出现在Top Rated（高评分）推荐位的商品数量 |
| `keywordDataUpdateTime` | `string` | 否 |  | 关键词数据更新时间.该关键词相关数据的最后更新时间 |
| `keywordPopularityRank` | `integer` | 否 |  | 关键词热度排名.该关键词的月搜索量在亚马逊所有关键词中的排名，数值越小表示搜索量越大 |
| `trackedAsinTotalCount` | `integer` | 否 |  | SIF 跟踪的有曝光 ASIN 去重总数.该关键词下所有位置（自然/广告/推荐）中，SIF 系统追踪到有曝光得分的 ASIN 去重数量。上游字段：totalAsinNum |
| `sponsoredProductsCount` | `integer` | 否 |  | SP广告商品数量.在该关键词下投放Sponsored Products（赞助商品）广告的商品数量 |
| `amazonChoiceProductCount` | `integer` | 否 |  | Amazon's Choice商品数量.在该关键词下获得Amazon's Choice推荐标志的商品数量 |
| `naturalSearchProductCount` | `integer` | 否 |  | 自然搜索商品数量.在该关键词的自然搜索结果中展示的商品数量（不包括广告位） |
| `estimatedWeeklySearchVolume` | `integer` | 否 |  | 周预估搜索量.该关键词在亚马逊上每周的预估搜索次数，反映该词的搜索热度 |
| `paidAdvertisingProductCount` | `integer` | 否 |  | PPC广告商品总数.在该关键词下所有PPC付费广告（包括SP、品牌广告、视频广告等）的商品总数 |
| `totalMarketplaceKeywordCount` | `integer` | 否 |  | 站点关键词总量.该站点（如美国站）所有关键词的总数量，用于了解市场整体规模 |
| `totalSearchResultProductCount` | `integer` | 否 |  | 搜索结果商品总数.在该关键词下显示的所有商品总数（包括自然搜索、广告位、推荐位等） |
| `searchRecommendationProductCount` | `integer` | 否 |  | 搜索推荐商品数量.在该关键词搜索时亚马逊推荐的商品数量 |
| `editorialRecommendationsProductCount` | `integer` | 否 |  | Editorial Recommendations商品数量.在该关键词下出现在编辑推荐位的商品数量 |

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
