---
name: linkfox-jiimore-product-discovery
description: 基于极目数据的亚马逊商品发掘与潜力爆品挖掘。当用户提到产品挖掘、潜力爆品、高转化选品、点击增长分析、市场增长机会、关键词选品、FBA利润筛选、细分市场商品发掘、卖家来源筛选、product mining, potential bestsellers, high-conversion product selection, market growth opportunities, Jiimore data, FBA profitability screening, keyword-based product selection时触发此技能。即使用户未明确提及"极目"，只要其需求涉及基于转化率、点击量和利润指标的亚马逊关键词驱动选品，也应触发此技能。
---

# 极目-亚马逊-产品挖掘

## 基本信息

- **业务工具名**：`/jiimore/productDiscovery`
- **所属分组**：极目 · 亚马逊选品
- **功能说明**：支持基于特定关键词结合高转化率、点击增长率等指标的潜力爆品挖掘。
- **关键词**：极目数据, 产品挖掘, 高转化选品, 潜力爆品, 市场增长


## 何时使用

当用户意图与“极目-亚马逊-产品挖掘”匹配，或需要以下能力时使用本工具：支持基于特定关键词结合高转化率、点击增长率等指标的潜力爆品挖掘。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1` | 页码 |
| `keyword` | `string` | 是 | 最长 1000 | 关键词（必填，并根据所选国家，翻译关键词为对应国家的语言） |
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
| `customerRatingMax` | `number` | 否 |  | 最高评分 |
| `customerRatingMin` | `number` | 否 |  | 最低评分 |
| `salesVolumeT360Max` | `integer` | 否 |  | 最高年销售量 |
| `salesVolumeT360Min` | `integer` | 否 |  | 最低年销售量 |
| `grossProfitMarginMax` | `number` | 否 |  | 最高毛利率 |
| `grossProfitMarginMin` | `number` | 否 |  | 最低毛利率 |
| `clickCountGrowthT7Max` | `number` | 否 |  | 最高周点击增长率,数值范围为0-1,0.1表示10% |
| `clickCountGrowthT7Min` | `number` | 否 |  | 最低周点击增长率,数值范围为0-1,0.1表示10% |
| `clickConversionRateMax` | `number` | 否 |  | 最高点击购买转化率,数值范围为0-1,0.1表示10% |
| `clickConversionRateMin` | `number` | 否 |  | 最低点击购买转化率,数值范围为0-1,0.1表示10% |
| `clickCountGrowthT30Max` | `number` | 否 |  | 最高月点击增长率,数值范围为0-1,0.1表示10% |
| `clickCountGrowthT30Min` | `number` | 否 |  | 最低月点击增长率,数值范围为0-1,0.1表示10% |
| `clickConversionRateCompositeMax` | `number` | 否 |  | 最高综合转化率,数值范围为0-1,0.1表示10% |
| `clickConversionRateCompositeMin` | `number` | 否 |  | 最低综合转化率,数值范围为0-1,0.1表示10% |


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
    "name": "/jiimore/productDiscovery",
    "arguments": {
      "keyword": "wireless headphones",
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
| `type` | `string` | 否 |  | 渲染的样式 |
| `title` | `string` | 否 |  | 标题 |
| `total` | `integer` | 否 |  | 总数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `products` | `array<object>` | 否 |  | 产品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `sourceTool` | `string` | 否 |  | 工具类型：jiimore |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 亚马逊商品asin |
| `brand` | `string` | 否 |  | 品牌 |
| `price` | `number` | 否 |  | 价格 |
| `title` | `string` | 否 |  | 产品标题 |
| `fbaFee` | `number` | 否 |  | 亚马逊佣金 |
| `asinUrl` | `string` | 否 |  | asin链接 |
| `ratings` | `integer` | 否 |  | 评论数 |
| `imageUrl` | `string` | 否 |  | 产品主图 |
| `parentAsin` | `string` | 否 |  | 亚马逊商品父Asin |
| `sourceTool` | `string` | 否 |  | 工具类型：jiimore |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |
| `shippingFee` | `number` | 否 |  | Fba运费 |
| `clickCountT7` | `integer` | 否 |  | 周点击量 |
| `availableDate` | `string` | 否 | 格式 `date` | 上架时间(时间戳) |
| `categoryNames` | `array<any>` | 否 |  | 类目信息 |
| `clickCountT30` | `integer` | 否 |  | 月点击量 |
| `clickCountT90` | `integer` | 否 |  | 季度点击量 |
| `marketplaceId` | `string` | 否 |  | 站点Id |
| `productImageUrls` | `array<any>` | 否 |  | 产品图片链接列表 |
| `grossProfitMargin` | `number` | 否 |  | 毛利率 |
| `availableDateString` | `string` | 否 |  | 上架日期(字符串) |
| `clickConversionRate` | `number` | 否 |  | 点击购买转化率 |
| `clickConversionRateComposite` | `number` | 否 |  | 综合转化率 |

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
