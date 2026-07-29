---
name: linkfox-jiimore-get-niche-info-by-keyword
description: 按关键词深度分析亚马逊细分市场，涵盖垄断程度、品牌集中度、新品成功率和市场机会评分。当用户提到细分市场分析、关键词市场调研、垄断评估、品牌集中度分析、新品成功率、市场需求评分、竞争格局、亚马逊子市场探索、niche market analysis, keyword market, monopoly level, brand concentration, new product success rate, market opportunity score, competitive landscape, Jiimore data时触发此技能。即使用户未明确提及"细分市场"，只要其需求涉及评估某个关键词维度的亚马逊市场竞争格局、品牌密度或机会潜力，也应触发此技能。
---

# 极目-亚马逊-细分市场信息

## 基本信息

- **业务工具名**：`/jiimore/getNicheInfoByKeyword`
- **所属分组**：极目 · 亚马逊选品
- **功能说明**：支持关键词细分市场的深度分析，评估市场垄断程度、品牌集中度及潜在机会。
- **关键词**：极目数据, 细分市场, 市场机会, 垄断程度, 关键词市场分析


## 何时使用

当用户意图与“极目-亚马逊-细分市场信息”匹配，或需要以下能力时使用本工具：支持关键词细分市场的深度分析，评估市场垄断程度、品牌集中度及潜在机会。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1` | 页码（从1开始） |
| `keyword` | `string` | 是 | 最长 1000 | 关键词（必填，并根据所选国家，翻译关键词为对应国家的语言） |
| `pageSize` | `integer` | 否 | 默认 `50`；最小 10；最大 100 | 每页返回数量（10-100） |
| `sortType` | `string` | 否 | 默认 `"desc"`；格式 `^(desc\|asc)$`；示例：`desc`, `asc` | 排序方式 |
| `sortField` | `string` | 否 | 默认 `"unitsSoldT7"`；格式受正则约束（见原始 Schema）；示例：`clickConversionRateT7`, `demand`, `avgPrice`, `maximumPrice`, `minimumPrice`, `productCount`, `searchConversionRateT7`, `searchVolumeT7` | 排序字段 |
| `avgPriceMax` | `number` | 否 |  | 平均价格（当前）最大值 |
| `avgPriceMin` | `number` | 否 |  | 平均价格（当前）最小值 |
| `countryCode` | `string` | 否 | 默认 `"US"`；格式 `^(US\|JP\|DE)$`；示例：`US`, `JP`, `DE` | 国家编码 |
| `cpcMediumMax` | `number` | 否 |  | CPC（当前）最大值 |
| `cpcMediumMin` | `number` | 否 |  | CPC（当前）最小值 |
| `brandCountMax` | `integer` | 否 |  | 品牌数量最大值 |
| `brandCountMin` | `integer` | 否 |  | 品牌数量最小值 |
| `avgBrandAgeMax` | `number` | 否 |  | 平均品牌年龄（当前）最大值 |
| `avgBrandAgeMin` | `number` | 否 |  | 平均品牌年龄（当前）最小值 |
| `unitsSoldT7Max` | `integer` | 否 |  | 销售量（7天统计）最大值 |
| `unitsSoldT7Min` | `integer` | 否 |  | 销售量（7天统计）最小值 |
| `clickCountT7Max` | `integer` | 否 |  | 点击量（7天统计）最大值 |
| `clickCountT7Min` | `integer` | 否 |  | 点击量（7天统计）最小值 |
| `productCountMax` | `integer` | 否 |  | 商品数量（当前）最大值 |
| `productCountMin` | `integer` | 否 |  | 商品数量（当前）最小值 |
| `avgBrandAgeQoqMax` | `number` | 否 |  | 平均品牌年龄（90天统计）最大值 |
| `avgBrandAgeQoqMin` | `number` | 否 |  | 平均品牌年龄（90天统计）最小值 |
| `avgBrandAgeYoyMax` | `number` | 否 |  | 平均品牌年龄（360天统计）最大值 |
| `avgBrandAgeYoyMin` | `number` | 否 |  | 平均品牌年龄（360天统计）最小值 |
| `launchRateT180Max` | `number` | 否 |  | 发布商品的成功率（180天统计）最大值，数值范围为0-1,代表0%-100% |
| `launchRateT180Min` | `number` | 否 |  | 发布商品的成功率（180天统计）最小值，数值范围为0-1,代表0%-100% |
| `returnRateT360Max` | `number` | 否 |  | 退货率（360天统计）最大值，数值范围为0-1,代表0%-100% |
| `returnRateT360Min` | `number` | 否 |  | 退货率（360天统计）最小值，数值范围为0-1,代表0%-100% |
| `searchVolumeT7Max` | `integer` | 否 |  | 搜索量（7天统计）最大值 |
| `searchVolumeT7Min` | `integer` | 否 |  | 搜索量（7天统计）最小值 |
| `newProductRateT180` | `number` | 否 |  | 新商品占比（180天统计）最小值，数值范围为0-1,代表0%-100% |
| `avgSellingPartnerAgeMax` | `number` | 否 |  | 平均销售伙伴年龄最大值 |
| `avgSellingPartnerAgeMin` | `number` | 否 |  | 平均销售伙伴年龄最小值 |
| `top5BrandsClickShareMax` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额最大值，数值范围为0-1,代表0%-100% |
| `top5BrandsClickShareMin` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额最小值，数值范围为0-1,代表0%-100% |
| `clickConversionRateT7Max` | `number` | 否 |  | 点击转换率（7天统计）最大值，数值范围为0-1,代表0%-100% |
| `clickConversionRateT7Min` | `number` | 否 |  | 点击转换率（7天统计）最小值，数值范围为0-1,代表0%-100% |
| `top5ProductsClickShareMax` | `number` | 否 |  | 排名前 5 位的商品点击份额（当前）最大值，数值范围为0-1,代表0%-100% |
| `top5ProductsClickShareMin` | `number` | 否 |  | 排名前 5 位的商品点击份额（当前）最小值，数值范围为0-1,代表0%-100% |
| `avgSellingPartnerAgeQoqMax` | `number` | 否 |  | 平均销售伙伴年龄（90天统计）最大值 |
| `avgSellingPartnerAgeQoqMin` | `number` | 否 |  | 平均销售伙伴年龄（90天统计）最小值 |
| `avgSellingPartnerAgeYoyMax` | `number` | 否 |  | 平均销售伙伴年龄（360天统计）最大值 |
| `avgSellingPartnerAgeYoyMin` | `number` | 否 |  | 平均销售伙伴年龄（360天统计）最小值 |
| `sponsoredProductsPercentageMax` | `number` | 否 |  | SP广告占比最大值，数值范围为0-1,代表0%-100% |
| `sponsoredProductsPercentageMin` | `number` | 否 |  | SP广告占比最小值，数值范围为0-1,代表0%-100% |


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
    "name": "/jiimore/getNicheInfoByKeyword",
    "arguments": {
      "keyword": "wireless headphones",
      "page": 1,
      "pageSize": 50,
      "countryCode": "US",
      "sortField": "unitsSoldT7",
      "sortType": "desc"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 细分市场信息列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `title` | `string` | 否 |  | 标题 |
| `total` | `integer` | 否 |  | 总数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `cpc` | `object` | 否 |  |  |
| `acos` | `number` | 否 |  | （ACOS）广告销售成本比 |
| `demand` | `integer` | 否 |  | 细分市场得分 |
| `nicheId` | `string` | 否 |  | 细分市场ID |
| `avgPrice` | `number` | 否 |  | 产品均价 |
| `brandCount` | `integer` | 否 |  | 品牌数量 |
| `nicheTitle` | `string` | 否 |  | 细分市场标题 |
| `maximumPrice` | `number` | 否 |  | 产品最高价 |
| `minimumPrice` | `number` | 否 |  | 产品最低价 |
| `productCount` | `integer` | 否 |  | 商品数量 |
| `categorieList` | `array<any>` | 否 |  | 商品品类列表 |
| `translationZh` | `string` | 否 |  | 细分市场标题(中文) |
| `avgBrandAgeNow` | `number` | 否 |  | 平均品牌年龄(当前) |
| `breakEvenRatio` | `number` | 否 |  | 盈亏平衡比率 |
| `unitsSoldWeekly` | `integer` | 否 |  | 销售数量（周数据） |
| `clickCountWeekly` | `integer` | 否 |  | 点击量（周数据） |
| `returnRateAnnual` | `number` | 否 |  | 退货率（全年数据） |
| `searchVolumeWeekly` | `integer` | 否 |  | 搜索量（周数据） |
| `unitsSoldQuarterly` | `integer` | 否 |  | 销售数量（季度数据） |
| `clickCountQuarterly` | `integer` | 否 |  | 点击量（季度数据） |
| `avgBrandAgeQuarterly` | `number` | 否 |  | 平均品牌年龄(季度数据) |
| `launchRateSemiannual` | `number` | 否 |  | 发布商品的成功率（半年数据） |
| `top5BrandsClickShare` | `number` | 否 |  | 前5个品牌所占细分市场的点击量份额 |
| `referenceAsinImageUrl` | `string` | 否 |  | 细分市场参考图片地址 |
| `searchVolumeQuarterly` | `integer` | 否 |  | 搜索量（季度数据） |
| `top5ProductsClickShare` | `number` | 否 |  | 排名前 5 位的商品点击份额 |
| `searchVolumeGrowthWeekly` | `number` | 否 |  | 搜索量增长率（周数据） |
| `searchConversionRateWeekly` | `number` | 否 |  | 搜索转换率（周数据） |
| `clickToSaleConversionWeekly` | `number` | 否 |  | 点击转换率（周数据） |
| `profitMarginGt50PctSkuRatio` | `number` | 否 |  | 利润率大于50%的商品比例 |
| `searchVolumeGrowthQuarterly` | `number` | 否 |  | 搜索量增长率（季度数据） |
| `clickConversionRateQuarterly` | `number` | 否 |  | 点击转换率（季度数据） |
| `successfulLaunchedSemiannual` | `integer` | 否 |  | 成功发布商品的数量（半年数据） |
| `newProductsLaunchedSemiannual` | `integer` | 否 |  | 已发布新产品的数量（半年数据） |
| `searchConversionRateQuarterly` | `number` | 否 |  | 搜索转换率（季度数据） |

### 嵌套输出结构：`data.cpc`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `low` | `number` | 否 |  | 最低价 |
| `high` | `number` | 否 |  | 最高价 |
| `medium` | `number` | 否 |  | 中间价 |

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
