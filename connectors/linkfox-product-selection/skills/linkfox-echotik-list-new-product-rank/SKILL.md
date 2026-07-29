---
name: linkfox-echotik-list-new-product-rank
description: 通过EchoTik新品排行数据，发现TikTok Shop 16个区域市场的热门新品。当用户提到TikTok新品排行、TikTok热销商品、TikTok Shop爆品、短视频电商选品、TikTok新品发掘、跨境TikTok选品、TikTok new product rankings, TikTok bestsellers, short-video product selection, TikTok viral products, new product ranking, TikTok product trends时触发此技能。即使用户未明确提及"EchoTik"或"新品排行"，只要其需求涉及发现TikTok Shop上的热卖新品或新兴商品趋势，也应触发此技能。
---

# EchoTik-TikTok新品榜

## 基本信息

- **业务工具名**：`/echotik/listNewProductRank`
- **所属分组**：EchoTik · TikTok 商品与视频
- **功能说明**：支持发现TikTok各区域市场的热销新品，把握短视频电商的最新趋势。
- **关键词**：EchoTik, TikTok选品, 新品榜单, TikTok热销, 短视频选品


## 何时使用

当用户意图与“EchoTik-TikTok新品榜”匹配，或需要以下能力时使用本工具：支持发现TikTok各区域市场的热销新品，把握短视频电商的最新趋势。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `date` | `string` | 是 | 最长 1000 | 日期, 格式为YYYY-MM-DD |
| `region` | `string` | 否 | 默认 `"US"`；格式 `^(US\|ID\|TH\|PH\|MY\|VN\|GB\|MX\|SG\|SA\|BR\|ES\|JP\|DE\|IT\|FR)$`；示例：`US`, `ID`, `TH`, `PH`, `MY`, `VN`, `GB`, `MX` | 区域 |
| `pageNum` | `integer` | 否 | 默认 `1` | 分页页码 |
| `pageSize` | `integer` | 否 | 默认 `50` | 分页页码 |


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
    "name": "/echotik/listNewProductRank",
    "arguments": {
      "date": "20260101000000",
      "pageSize": 50
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `products` | `array<object>` | 否 |  | 最新商品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 商品ID |
| `price` | `number` | 否 |  | SPU平均价格 |
| `title` | `string` | 否 |  | 商品名称 |
| `region` | `string` | 否 |  | 区域代码 |
| `currency` | `string` | 否 |  | 货币 |
| `imageUrl` | `string` | 否 |  | 商品图片 |
| `maxPrice` | `number` | 否 |  | 最高价格 |
| `minPrice` | `number` | 否 |  | 最低价格 |
| `categoryId` | `string` | 否 |  | 商品分类ID |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 商品来源 |
| `reviewCount` | `integer` | 否 |  | 评论数量 |
| `totalIflCnt` | `integer` | 否 |  | 总达人数 |
| `totalLiveCnt` | `integer` | 否 |  | 直播总数 |
| `totalSaleCnt` | `integer` | 否 |  | 总销量 |
| `availableDate` | `string` | 否 | 格式 `date` | 首次爬取日期-firstCrawlDt |
| `productRating` | `number` | 否 |  | 商品评分 |
| `totalVideoCnt` | `integer` | 否 |  | 视频总数 |
| `totalSale30dCnt` | `integer` | 否 |  | 近30天销量 |
| `totalSaleGmvAmt` | `number` | 否 |  | 总销售额 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片URL列表 |
| `salesTrendFlagText` | `string` | 否 |  | 销售趋势标识, 0=平稳 1=上升 2=下降 |
| `totalSaleGmv30dAmt` | `number` | 否 |  | 近30天销售额 |
| `productCommissionRate` | `number` | 否 |  | 商品佣金比例 |

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
