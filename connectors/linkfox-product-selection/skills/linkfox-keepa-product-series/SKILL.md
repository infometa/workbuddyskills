---
name: linkfox-keepa-product-series
description: 查询亚马逊商品的历史时序数据，包括价格走势、BSR（畅销排名）趋势、评分变化、卖家数量和月销量，支持多个亚马逊站点的任意ASIN。当用户提到价格历史、价格追踪、BSR历史、BSR趋势、历史定价、价格波动、Keepa数据、排名历史、降价提醒、秒杀历史价格、Buy Box价格趋势、优惠券价格、FBA/FBM价格对比、卖家数量变化、评分趋势、销量历史、price history, BSR trends, Keepa historical data, price tracking, sales history, rating changes, seller count changes, price fluctuation时触发此技能。即使用户未明确提及"Keepa"或"时序数据"，只要其需求涉及亚马逊历史商品级数据（如价格、排名或销量随时间的变化趋势），也应触发此技能。
---

# Keepa-亚马逊价格历史

## 基本信息

- **业务工具名**：`/keepa/productSeries`
- **所属分组**：Keepa · 亚马逊商品与价格历史
- **功能说明**：按亚马逊 amazon asin查询该 asin 的 价格 变化 历史、BSR历史、历史数据趋势
- **关键词**：Keepa, 价格历史, BSR历史, 历史数据趋势, 价格追踪


## 何时使用

当用户意图与“Keepa-亚马逊价格历史”匹配，或需要以下能力时使用本工具：按亚马逊 amazon asin查询该 asin 的 价格 变化 历史、BSR历史、历史数据趋势

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000 | 亚马逊标准识别号(ASIN)，只支持单个ASIN |
| `days` | `integer` | 否 | 默认 `90`；最大 1096；示例：`30`, `90` | 限制历史数据天数，默认90天 |
| `domain` | `string` | 是 | 格式 `1\|2\|3\|4\|5\|6\|8\|9\|10\|11\|12`；示例：`1`, `2`, `3`, `4`, `5`, `6`, `8`, `9` | 亚马逊域名ID |
| `showPrice` | `integer` | 否 | 示例：`1` | 是否返回市场最低新品价曲线 |
| `showBsrMain` | `integer` | 否 | 示例：`1` | 是否返回大类BSR曲线 |
| `showPriceFba` | `integer` | 否 | 示例：`1` | 是否返回第三方FBA新品价曲线 |
| `showPriceFbm` | `integer` | 否 | 示例：`1` | 是否返回第三方FBM新品价曲线 |
| `showPriceDeal` | `integer` | 否 | 示例：`1` | 是否返回闪促价格曲线 |
| `showPriceList` | `integer` | 否 | 示例：`1` | 是否返回划线价/标价曲线 |
| `showPricePrime` | `integer` | 否 | 示例：`1` | 是否返回Prime专属新品价曲线 |
| `showPriceCoupon` | `integer` | 否 | 示例：`1` | 是否返回优惠券后买盒价曲线 |
| `showSellerCount` | `integer` | 否 | 示例：`1` | 是否返回卖家数曲线 |


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
    "name": "/keepa/productSeries",
    "arguments": {
      "asin": "B0EXAMPLE01",
      "domain": "1"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `price` | `array<object>` | 否 |  | 价格,(time=时间,value=价格) |
| `bsrSub` | `array<object>` | 否 |  | 小类BSR |
| `rating` | `array<object>` | 否 |  | 评分(time=时间,value=评分) |
| `bsrMain` | `array<object>` | 否 |  | 大类BSR |
| `priceFba` | `array<object>` | 否 |  | FBA价格,(time=时间,value=FBA价格) |
| `priceFbm` | `array<object>` | 否 |  | FBM价格,(time=时间,value=FBM价格) |
| `costToken` | `integer` | 否 |  | 消耗token |
| `priceDeal` | `array<object>` | 否 |  | Deal价格,(time=时间,value=Deal价格) |
| `priceList` | `array<object>` | 否 |  | 划线价,(time=时间,value=划线价格) |
| `pricePrime` | `array<object>` | 否 |  | Prime价格,(time=时间,value=Prime价格) |
| `buyboxPrice` | `array<object>` | 否 |  | Buybox价格,(time=时间,value=Buybox价格) |
| `monthlySold` | `array<object>` | 否 |  | 子体销量(time=时间,value=销量) |
| `priceCoupon` | `array<object>` | 否 |  | coupon价格(time=时间,value=coupon价格) |
| `ratingCount` | `array<object>` | 否 |  | 评分数(time=时间,value=评分数) |
| `sellerCount` | `array<object>` | 否 |  | 卖家数(time=时间,value=卖家数) |

### 嵌套输出结构：`bsrSub`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `points` | `array<object>` | 否 |  | time=时间,value=排名 |
| `categoryName` | `string` | 否 |  | 类目名称 |

### 嵌套输出结构：`bsrMain`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `points` | `array<object>` | 否 |  | time=时间,value=排名 |
| `categoryName` | `string` | 否 |  | 类目名称 |

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
