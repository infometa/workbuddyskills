---
name: linkfox-sif-asin-keywords
description: 使用SIF数据反查任意亚马逊ASIN的流量关键词，包括自然排名、广告排名、搜索量、流量占比、自然/付费得分、ABA TOP3点击集中度、点击转化率、搜索量同比涨跌及周/月时间窗。当用户提到ASIN关键词分析、ASIN反查、流量关键词研究、自然排名查询、广告排名查询、关键词位置追踪、SIF关键词数据、竞品关键词窥探、查看哪些关键词为产品带来流量、分析特定ASIN的关键词表现、按周/月/最近N天的关键词时间窗、ASIN reverse keyword lookup, traffic keywords, organic ranking, ad ranking, search volume, SIF keywords, competitor keyword reverse lookup, click concentration, click-to-purchase conversion, week-over-week search volume时触发此技能。即使用户未明确提及"SIF"，只要其需求涉及查找与特定亚马逊商品（ASIN）关联的关键词，也应触发此技能。
---

# SIF-ASIN的关键词

## 基本信息

- **业务工具名**：`/sif/asinKeywords`
- **所属分组**：SIF · 亚马逊流量与关键词
- **功能说明**：根据亚马逊站点 和 asin 查询 这个 商品的 流量关键词
- **关键词**：SIF, ASIN关键词, 反查关键词, 自然排名, 广告排名, 流量词


## 何时使用

当用户意图与“SIF-ASIN的关键词”匹配，或需要以下能力时使用本工具：根据亚马逊站点 和 asin 查询 这个 商品的 流量关键词

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000 | ASIN码 |
| `desc` | `boolean` | 否 | 默认 `true` | 是否降序，默认传 true  |
| `sortBy` | `string` | 否 | 格式 `lastRank\|adLastRank\|updateTime\|searchesRank\|estSearchesNum`；示例：``, `lastRank`, `adLastRank`, `updateTime`, `searchesRank`, `estSearchesNum` | 排序字段 |
| `country` | `string` | 否 | 默认 `"US"`；格式 `US\|UK\|DE\|CA\|JP\|FR\|ES\|IT\|MX\|AU\|AE\|BR\|SA`；示例：`US`, `UK`, `DE`, `CA`, `JP`, `FR`, `ES`, `IT` | 国家站点 |
| `keyword` | `string` | 否 | 最长 1000 | 关键词，尽量翻译成对应国家站点的语言 |
| `pageNum` | `integer` | 否 | 默认 `1` | 页码 |
| `pageSize` | `integer` | 否 | 默认 `100`；最小 10；最大 100 | 每页数量,最小10，最大100，默认也是100 |
| `conditions` | `string` | 否 | 格式受正则约束（见原始 Schema）；示例：`nfPosition`, `isSpAd`, `isBrandAd`, `isVedioAd`, `isAC`, `isAccurateKw`, `isAccurateTailKw`, `isPurchaseKw` | 条件筛选,多个条件以英文逗号隔开 |
| `timePieceType` | `string` | 否 | 默认 `"latelyDay"`；格式 `latelyDay\|month\|week`；示例：`latelyDay`, `month`, `week` | 时间片段类型：latelyDay=最近N天/month=某月/week=某周 |
| `timePieceValue` | `string` | 否 | 默认 `"7"`；最长 1000；示例：`7`, `30`, `2026-04`, `2026-04-13` | 时间片段值：latelyDay 时仅支持 7 或 30；month 时为 YYYY-MM；week 时为周开始日期 YYYY-MM-DD |


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
    "name": "/sif/asinKeywords",
    "arguments": {
      "asin": "B0EXAMPLE01",
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
| `hasVaiants` | `boolean` | 否 |  | 是否有变体 |
| `isParentAsin` | `boolean` | 否 |  | 是否是父体 |
| `abaCreateDateWeek` | `string` | 否 |  | 最新周aba时间 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 商品asin |
| `keyword` | `string` | 否 |  | 关键词 |
| `updateTime` | `string` | 否 |  | 关键词数据更新时间 |
| `brandAdScore` | `number` | 否 |  | SB 品牌广告得分.该关键词下 Sponsored Brands 品牌广告的流量得分（含常规 + 视频，总和） |
| `trafficShare` | `number` | 否 |  | 流量占比.该关键词为商品带来的流量占所有关键词总流量的比例，其中1表示100% |
| `videoAdScore` | `number` | 否 |  | SBV 视频广告得分.该关键词下 Sponsored Brands Video 视频广告的流量得分 |
| `adRankDisplay` | `string` | 否 |  | 广告排名显示文本.SP广告排名的字符串表示形式 |
| `periodEndDate` | `string` | 否 |  | 本周期结束日期.本周期（周粒度）的最大时间（站点时间），= 开始周 + 7 天 |
| `productAdRank` | `integer` | 否 |  | 商品SP广告排名.该商品在此关键词下的Sponsored Products广告位中的排名位置，如3表示排在广告位第3位 |
| `lastAdRankTime` | `string` | 否 |  | 最近有效SP广告排名的时间.商品在此关键词下最近一次Sponsored Products广告排名的记录时间 |
| `paidTrafficShare` | `number` | 否 |  | 付费广告流量得分占比.广告流量得分 / 总得分；广告合计 = sp + sb + sbv + recAd |
| `translateKeyword` | `string` | 否 |  | 关键词翻译.关键词的站点本地化译文（如中文），v2 新增 |
| `naturalRankDisplay` | `string` | 否 |  | 自然排名显示文本.自然搜索排名的字符串表示形式 |
| `productNaturalRank` | `integer` | 否 |  | 商品自然搜索排名.该商品在此关键词下的自然搜索结果中的位置排名，如1表示排在搜索结果第1位（首位） |
| `weeklySearchVolume` | `integer` | 否 |  | 周搜索量.该关键词在亚马逊平台每周的预估搜索次数 |
| `lastNaturalRankTime` | `string` | 否 |  | 最近有效自然排名的时间.商品在此关键词下最近一次有效自然搜索排名的记录时间 |
| `naturalTrafficScore` | `number` | 否 |  | 自然流量得分.该关键词为该 ASIN 带来的自然搜索曝光得分，0 = 无自然流量曝光 |
| `naturalTrafficShare` | `number` | 否 |  | 自然流量得分占比.自然搜索流量得分 / 总得分 |
| `displayPositionTypes` | `array<any>` | 否 |  | 商品展示位置类型数组.该关键词下商品的展示位置，可能包含以下值：natural=自然搜索结果位；ac=Amazon's Choice推荐位；sp=Sponsored Products赞助商品广告位；top=页面顶部品牌广告位；bottom=页面底部品牌广告位；er=Editorial Recommendations编辑推荐位；vedio=视频广告位；tr=Top Rated高评分推荐位；trfob=Top Rated Frequently Bought高频购买推荐位。示例：["natural"]表示仅在自然搜索结果中展示，["natural","sp"]表示同时在自然搜索和广告位展示 |
| `keywordPopularityRank` | `integer` | 否 |  | 关键词搜索热度排名.该关键词的月搜索量在亚马逊所有关键词中的排名，数值越小表示搜索量越大，如203表示该词搜索热度排第203名 |
| `sponsoredProductsScore` | `number` | 否 |  | SP 广告常规得分.该关键词下 Sponsored Products 常规位的流量得分（不含 SP 推荐位） |
| `clickConcentrationShare` | `number` | 否 |  | ABA TOP3 点击集中度.衡量该关键词下点击是否集中在头部几款 ASIN 上的指标；注意：不是转化率 |
| `conversionPerformanceMarkers` | `array<any>` | 否 |  | 转化效果标记数组.标记该关键词的转化表现，可能包含以下值：isPurchaseKw=出单词（通过该词产生过订单）；isQualityKw=转化优质词（转化率高的优质关键词）；isStableKw=转化平稳词（转化表现稳定的关键词）；isLossKw=转化流失词（曾经转化好但现在流失的关键词）；isInvalidKw=无效曝光词（有曝光但无转化的无效词）。示例：["isPurchaseKw","isStableKw"] |
| `sponsoredRecommendationScore` | `number` | 否 |  | SP 推荐位得分.该关键词下 SP 推荐位（Trending now / Seen on social media / Customers frequently viewed 等）合计得分 |
| `trafficCharacteristicMarkers` | `array<any>` | 否 |  | 关键词流量特征标记数组.标记该关键词的流量特征，可能包含以下值：isMainKw=主要流量词（为该商品带来主要流量的核心词）；isAccurateKw=精准流量词（与商品高度相关的精准词）；isAccurateAboveKw=精准大词（搜索量大且精准的关键词）；isAccurateTailKw=精准长尾词（搜索量较小但精准的长尾关键词）。示例：["isMainKw","isAccurateKw"] |
| `clickToPurchaseConversionRate` | `number` | 否 |  | 点击到购买的转化率（purchaseQty / clickQty） |
| `totalSearchResultProductCount` | `integer` | 否 |  | 该关键词下搜索结果商品总数（在售产品数） |
| `sponsoredRecommendationBreakdown` | `array<object>` | 否 |  | SP 推荐位得分明细.数组，每项 {title, score, scoreRatio}；title 示例：Trending now / Seen on social media / 4 stars and above / Customers frequently viewed |

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
