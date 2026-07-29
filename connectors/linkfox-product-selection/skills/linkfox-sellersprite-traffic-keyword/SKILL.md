---
name: linkfox-sellersprite-traffic-keyword
description: 使用卖家精灵流量词反查能力，按ASIN查询关键词流量来源、流量占比类型、转化类型、自然位与广告位等指标，支持历史月份与多维排序。当用户提到ASIN反查流量词、流量关键词列表、关键词流量结构、自然词/广告词分析、关键词转化类型、SellerSprite traffic keyword、Amazon traffic keywords、reverse ASIN keywords时触发此技能。即使用户未明确提及"卖家精灵"，只要需求是围绕某个ASIN查看其关键词流量来源与词列表，也应触发此技能。
---

# 卖家精灵-关键词反查(流量词列表)

## 基本信息

- **业务工具名**：`/sellersprite/traffic/keyword`
- **所属分组**：卖家精灵 · 亚马逊选品
- **功能说明**：根据一个或多个ASIN，反查该商品在亚马逊上的所有流量关键词，包括自然搜索词、SP广告词、AC推荐词、品牌推荐词、视频推荐词等多种流量词类型。
- **关键词**：卖家精灵, 关键词, 流量词, 反查


## 何时使用

当用户意图与“卖家精灵-关键词反查(流量词列表)”匹配，或需要以下能力时使用本工具：根据一个或多个ASIN，反查该商品在亚马逊上的所有流量关键词，包括自然搜索词、SP广告词、AC推荐词、品牌推荐词、视频推荐词等多种流量词类型。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000；示例：`B07Z82895W` | ASIN |
| `page` | `integer` | 否 | 默认 `1` | 当前页，默认1 |
| `size` | `integer` | 否 | 默认 `50`；最小 1；最大 100 | 每页条数，默认50，最大100，最多查2000条 |
| `month` | `string` | 否 | 格式 `^(19\|20)\d{2}(0[1-9]\|1[0-2])$`；示例：`202308` | 历史月份，不传默认最近30天，格式 yyyyMM |
| `badges` | `string` | 否 | 最长 1000；示例：`naturalSearching`, `amazonChoice`, `editorialRecommendations`, `fourStar`, `highlyRated`, `sponsorBrand`, `sponsorVideo`, `ads` | 流量词类型(badges)，多个值用英文逗号分隔。可选枚举：naturalSearching-自然搜索词；amazonChoice-AC推荐词；editorialRecommendations-ER推荐词；fourStar-四星推荐词；highlyRated-HR推荐词；sponsorBrand-品牌推荐词；sponsorVideo-视频推荐词；ads-SP广告词 |
| `keyword` | `string` | 否 | 最长 1000 | 关键词筛选 |
| `orderDesc` | `boolean` | 否 | 默认 `false` | 排序是否倒序，默认 false |
| `orderField` | `string` | 否 | 默认 `"rankPosition"`；最长 1000；示例：`rankPosition`, `adPosition`, `createdTime`, `searchesRank`, `searches`, `purchases`, `purchaseRate`, `products` | 排序字段(order.field)，默认 rankPosition。可选：rankPosition-自然排名；adPosition-广告排名；createdTime-创建时间；searchesRank-搜索量周排名；searches-月搜索量；purchases-月购买量；purchaseRate-购买率；products-商品数；supplyDemandRatio-供需比；latest1daysAds-广告竞品数；bid-PPC竞价；trafficPercentage-流量占比 |
| `marketplace` | `string` | 是 | 默认 `"US"`；最长 1000；示例：`US`, `JP`, `UK`, `DE`, `FR`, `IT`, `ES`, `CA` | 市场(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹) |
| `trafficKeywordTypes` | `string` | 否 | 最长 1000；示例：`primary`, `precise`, `preciseLongTail` | 流量占比类型(trafficKeywordTypes)，多个值用英文逗号分隔。可选枚举：primary-主要流量词；precise-精准流量词；preciseLongTail-转化流失词 |
| `conversionKeywordTypes` | `string` | 否 | 最长 1000；示例：`excellent`, `stable`, `lost`, `invalid` | 流量转化类型(conversionKeywordTypes)，多个值用英文逗号分隔。可选枚举：excellent-转化优质词；stable-转化平稳词；lost-转化流失词；invalid-无效曝光词 |


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
    "name": "/sellersprite/traffic/keyword",
    "arguments": {
      "marketplace": "US",
      "asin": "B07Z82895W",
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `data` | `array<object>` | 否 |  | 流量词列表(对应第三方 data.items) |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总条数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `marketplace` | `string` | 否 |  | 市场编码 |
| `summaryList` | `array<object>` | 否 |  | 高频词总结列表 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `bid` | `number` | 否 |  | PPC竞价 |
| `sprt` | `number` | 否 |  | SP相关比率 |
| `stats` | `array<object>` | 否 |  | 高频词 |
| `badges` | `array<any>` | 否 |  | 曝光位置(流量词类型) |
| `bidMax` | `number` | 否 |  | PPC竞价上限 |
| `bidMin` | `number` | 否 |  | PPC竞价下限 |
| `clicks` | `integer` | 否 |  | 点击量 |
| `adRatio` | `number` | 否 |  | 流量分布-广告占比 |
| `keyword` | `string` | 否 |  | 关键词 |
| `products` | `integer` | 否 |  | 商品数 |
| `searches` | `integer` | 否 |  | 月搜索量 |
| `keywordCn` | `string` | 否 |  | 关键词中文翻译 |
| `purchases` | `integer` | 否 |  | 月购买量 |
| `adPosition` | `object` | 否 |  |  |
| `impressions` | `integer` | 否 |  | 展示量 |
| `updatedTime` | `integer` | 否 |  | 更新时间 |
| `naturalRatio` | `number` | 否 |  | 流量分布-自然占比 |
| `purchaseRate` | `number` | 否 |  | 购买率 |
| `rankPosition` | `object` | 否 |  |  |
| `searchesRank` | `integer` | 否 |  | 周搜索量排名 |
| `titleDensity` | `number` | 否 |  | 标题密度 |
| `latest1daysAds` | `integer` | 否 |  | 最近1天广告竞品数 |
| `latest7daysAds` | `integer` | 否 |  | 最近7天广告竞品数 |
| `latest30daysAds` | `integer` | 否 |  | 最近30天广告竞品数 |
| `top3ClickingRate` | `number` | 否 |  | Top3点击率 |
| `monopolyClickRate` | `number` | 否 |  | 垄断点击率 |
| `supplyDemandRatio` | `number` | 否 |  | 供需比 |
| `trafficPercentage` | `number` | 否 |  | 流量占比 |
| `searchesRankTimeTo` | `integer` | 否 |  | 周搜索量排名时间范围止 |
| `top3ConversionRate` | `number` | 否 |  | Top3转化率 |
| `trafficKeywordType` | `string` | 否 |  | 流量占比类型 |
| `searchesRankTimeFrom` | `integer` | 否 |  | 周搜索量排名时间范围起 |
| `conversionKeywordType` | `string` | 否 |  | 流量转化类型 |
| `calculatedWeeklySearches` | `number` | 否 |  | 预估周曝光量 |

### 嵌套输出结构：`data.stats`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `total` | `integer` | 否 |  | 总条数 |
| `keywords` | `string` | 否 |  | 词 |
| `adPosition` | `object` | 否 |  |  |
| `rankPosition` | `object` | 否 |  |  |

### 嵌套输出结构：`data.stats.adPosition`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 |  | 第几页 |
| `index` | `integer` | 否 |  | 当前页排第几 |
| `pageSize` | `integer` | 否 |  | 每页多少条数据 |
| `position` | `integer` | 否 |  | 总结果中排第几 |
| `updatedTime` | `integer` | 否 |  | 排名时间 |

### 嵌套输出结构：`data.stats.rankPosition`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 |  | 第几页 |
| `index` | `integer` | 否 |  | 当前页排第几 |
| `pageSize` | `integer` | 否 |  | 每页多少条数据 |
| `position` | `integer` | 否 |  | 总结果中排第几 |
| `updatedTime` | `integer` | 否 |  | 排名时间 |

### 嵌套输出结构：`data.adPosition`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 |  | 第几页 |
| `index` | `integer` | 否 |  | 当前页排第几 |
| `pageSize` | `integer` | 否 |  | 每页多少条数据 |
| `position` | `integer` | 否 |  | 总结果中排第几 |
| `updatedTime` | `integer` | 否 |  | 排名时间 |

### 嵌套输出结构：`data.rankPosition`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 |  | 第几页 |
| `index` | `integer` | 否 |  | 当前页排第几 |
| `pageSize` | `integer` | 否 |  | 每页多少条数据 |
| `position` | `integer` | 否 |  | 总结果中排第几 |
| `updatedTime` | `integer` | 否 |  | 排名时间 |

### 嵌套输出结构：`summaryList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `total` | `integer` | 否 |  | 总次数 |
| `keywords` | `string` | 否 |  | 词 |

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
