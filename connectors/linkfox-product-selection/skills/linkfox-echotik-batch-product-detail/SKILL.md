---
name: linkfox-echotik-batch-product-detail
description: 批量查询TikTok商品详情数据，包括多周期销量与GMV（1天/7天/15天/30天/60天/90天/累计）、直播销量与直播GMV、带货视频与达人数据、播放量、价格、评分、评论数、佣金比例及上下架/全托管状态，支持通过商品ID或TikTok Shop商品URL批量获取。当用户提到TikTok商品详情、批量查询TikTok商品、TikTok商品销量分析、TikTok商品GMV、TikTok直播销量、TikTok带货数据、TikTok商品价格评分、批量获取TikTok商品信息、EchoTik商品详情、TikTok product detail, batch product lookup, TikTok sales analysis, TikTok GMV, TikTok live sales, TikTok influencer data时触发此技能。即使用户未明确提及"EchoTik"，只要其需求涉及根据商品ID或商品URL批量获取TikTok商品的详细销售与营销数据，也应触发此技能。
---

# EchoTik-商品详情

## 基本信息

- **业务工具名**：`/echotik/batchProductDetail`
- **所属分组**：EchoTik · TikTok 商品与视频
- **功能说明**：EchoTik-商品详情


## 何时使用

当用户意图与“EchoTik-商品详情”匹配，或需要以下能力时使用本工具：EchoTik-商品详情

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `productIds` | `array<string>` | 否 | 最多 1000 项 | 商品ID列表, 多个使用英文逗号分隔 |
| `productUrls` | `array<string>` | 否 | 最多 1000 项 | 商品URL列表, 形如 https://shop.tiktok.com/us/pdp/<slug>/<productId>?... ; 将从每个URL中提取末尾的productId并合并到productIds, 与productIds不排斥 |


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
    "name": "/echotik/batchProductDetail",
    "arguments": {}
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
| `products` | `array<object>` | 否 |  | 商品详情列表 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `region` | `string` | 否 |  | 区域代码 |
| `isSShop` | `integer` | 否 |  | 是否全托管店铺 |
| `offMark` | `integer` | 否 |  | 商品下架标识 |
| `discount` | `string` | 否 |  | 折扣信息 |
| `imageUrl` | `string` | 否 |  | 商品图片 |
| `maxPrice` | `number` | 否 |  | 最高SKU价格(USD) |
| `minPrice` | `number` | 否 |  | 最低SKU价格(USD) |
| `sellerId` | `string` | 否 |  | 卖家ID |
| `productId` | `string` | 否 |  | 商品ID |
| `salesFlag` | `integer` | 否 |  | 主要配送方式 |
| `categoryId` | `string` | 否 |  | 一级分类ID |
| `descDetail` | `string` | 否 |  | 商品详情描述 |
| `productName` | `string` | 否 |  | 商品名称 |
| `reviewCount` | `integer` | 否 |  | 评论数量 |
| `spuAvgPrice` | `number` | 否 |  | SPU平均价格(USD) |
| `totalIflCnt` | `integer` | 否 |  | 总达人数量 |
| `categoryL2Id` | `string` | 否 |  | 二级分类ID |
| `categoryL3Id` | `string` | 否 |  | 三级分类ID |
| `firstCrawlDt` | `string` | 否 |  | 首次爬取日期 |
| `freeShipping` | `integer` | 否 |  | 是否免运费 |
| `totalLiveCnt` | `integer` | 否 |  | 总直播数量 |
| `totalSaleCnt` | `integer` | 否 |  | 总销量 |
| `productRating` | `number` | 否 |  | 商品评分 |
| `totalVideoCnt` | `integer` | 否 |  | 总视频数量 |
| `totalViewsCnt` | `integer` | 否 |  | 总观看次数 |
| `salesTrendFlag` | `integer` | 否 |  | 销售趋势标识(0=稳定 1=上升 2=下降) |
| `totalLive1dCnt` | `integer` | 否 |  | 近1天直播数量 |
| `totalLive7dCnt` | `integer` | 否 |  | 近7天直播数量 |
| `totalSale1dCnt` | `integer` | 否 |  | 近1天销量 |
| `totalSale7dCnt` | `integer` | 否 |  | 近7天销量 |
| `totalLive15dCnt` | `integer` | 否 |  | 近15天直播数量 |
| `totalLive30dCnt` | `integer` | 否 |  | 近30天直播数量 |
| `totalLive60dCnt` | `integer` | 否 |  | 近60天直播数量 |
| `totalLive90dCnt` | `integer` | 否 |  | 近90天直播数量 |
| `totalSale15dCnt` | `integer` | 否 |  | 近15天销量 |
| `totalSale30dCnt` | `integer` | 否 |  | 近30天销量 |
| `totalSale60dCnt` | `integer` | 否 |  | 近60天销量 |
| `totalSale90dCnt` | `integer` | 否 |  | 近90天销量 |
| `totalSaleGmvAmt` | `number` | 否 |  | 总销售额 |
| `totalVideo1dCnt` | `integer` | 否 |  | 近1天视频数量 |
| `totalVideo7dCnt` | `integer` | 否 |  | 近7天视频数量 |
| `totalViews1dCnt` | `integer` | 否 |  | 近1天观看次数 |
| `totalViews7dCnt` | `integer` | 否 |  | 近7天观看次数 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片列表 |
| `totalVideo15dCnt` | `integer` | 否 |  | 近15天视频数量 |
| `totalVideo30dCnt` | `integer` | 否 |  | 近30天视频数量 |
| `totalVideo60dCnt` | `integer` | 否 |  | 近60天视频数量 |
| `totalVideo90dCnt` | `integer` | 否 |  | 近90天视频数量 |
| `totalViews15dCnt` | `integer` | 否 |  | 近15天观看次数 |
| `totalViews30dCnt` | `integer` | 否 |  | 近30天观看次数 |
| `totalViews60dCnt` | `integer` | 否 |  | 近60天观看次数 |
| `totalViews90dCnt` | `integer` | 否 |  | 近90天观看次数 |
| `totalIflLive1dCnt` | `integer` | 否 |  | 近1天达人直播数量 |
| `totalIflLive7dCnt` | `integer` | 否 |  | 近7天达人直播数量 |
| `totalSaleGmv1dAmt` | `number` | 否 |  | 近1天销售额 |
| `totalSaleGmv7dAmt` | `number` | 否 |  | 近7天销售额 |
| `totalIflLive15dCnt` | `integer` | 否 |  | 近15天达人直播数量 |
| `totalIflLive30dCnt` | `integer` | 否 |  | 近30天达人直播数量 |
| `totalIflLive60dCnt` | `integer` | 否 |  | 近60天达人直播数量 |
| `totalIflLive90dCnt` | `integer` | 否 |  | 近90天达人直播数量 |
| `totalIflVideo1dCnt` | `integer` | 否 |  | 近1天达人视频数量 |
| `totalIflVideo7dCnt` | `integer` | 否 |  | 近7天达人视频数量 |
| `totalLiveSale1dCnt` | `integer` | 否 |  | 近1天直播销量 |
| `totalLiveSale7dCnt` | `integer` | 否 |  | 近7天直播销量 |
| `totalSaleGmv15dAmt` | `number` | 否 |  | 近15天销售额 |
| `totalSaleGmv30dAmt` | `number` | 否 |  | 近30天销售额 |
| `totalSaleGmv60dAmt` | `number` | 否 |  | 近60天销售额 |
| `totalSaleGmv90dAmt` | `number` | 否 |  | 近90天销售额 |
| `totalIflVideo15dCnt` | `integer` | 否 |  | 近15天达人视频数量 |
| `totalIflVideo30dCnt` | `integer` | 否 |  | 近30天达人视频数量 |
| `totalIflVideo60dCnt` | `integer` | 否 |  | 近60天达人视频数量 |
| `totalIflVideo90dCnt` | `integer` | 否 |  | 近90天达人视频数量 |
| `totalLiveSale15dCnt` | `integer` | 否 |  | 近15天直播销量 |
| `totalLiveSale30dCnt` | `integer` | 否 |  | 近30天直播销量 |
| `totalLiveSale60dCnt` | `integer` | 否 |  | 近60天直播销量 |
| `totalLiveSale90dCnt` | `integer` | 否 |  | 近90天直播销量 |
| `productCommissionRate` | `number` | 否 |  | 商品佣金比例 |
| `totalLiveSaleGmv1dAmt` | `integer` | 否 |  | 近1天直播销售额 |
| `totalLiveSaleGmv7dAmt` | `integer` | 否 |  | 近7天直播销售额 |
| `totalLiveSaleGmv15dAmt` | `integer` | 否 |  | 近15天直播销售额 |
| `totalLiveSaleGmv30dAmt` | `integer` | 否 |  | 近30天直播销售额 |
| `totalLiveSaleGmv60dAmt` | `integer` | 否 |  | 近60天直播销售额 |
| `totalLiveSaleGmv90dAmt` | `integer` | 否 |  | 近90天直播销售额 |

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
