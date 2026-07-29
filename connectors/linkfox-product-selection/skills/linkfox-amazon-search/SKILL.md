---
name: linkfox-amazon-search
description: 模拟真实用户在亚马逊前台搜索，获取实时关键词排名和搜索结果页数据。当用户提到亚马逊商品搜索、搜索结果抓取、关键词在搜索页的排名、ASIN排名位置查询、竞品发现、搜索页价格对比、广告商品分析、新品监控、前台搜索模拟、Amazon search, keyword ranking, search results, ASIN ranking position, competitor discovery, price comparison, sponsored product analysis, real-time search, new product monitoring时触发此技能。即使用户未明确提及"搜索模拟"，只要其需求涉及实时亚马逊搜索结果、商品排位数据或前台SERP分析，也应触发此技能。
---

# 亚马逊前端搜索模拟

## 基本信息

- **业务工具名**：`/amazon/search`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：支持模拟真实用户在亚马逊前台的搜索行为，获取实时关键词排名和搜索结果页数据。
- **关键词**：亚马逊搜索, 前端模拟, 实时搜索结果, 关键词排名, 页面抓取


## 何时使用

当用户意图与“亚马逊前端搜索模拟”匹配，或需要以下能力时使用本工具：支持模拟真实用户在亚马逊前台的搜索行为，获取实时关键词排名和搜索结果页数据。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `node` | `string` | 否 | 最长 1000 | 亚马逊类目节点 |
| `page` | `integer` | 否 | 默认 `1` | 页码(从1开始，每页大概20条) |
| `sort` | `string` | 否 | 默认 `"relevanceblender"`；最长 1000；示例：`relevanceblender`, `price-asc-rank`, `price-desc-rank`, `review-rank`, `date-desc-rank`, `exact-aware-popularity-rank` | 排序 |
| `device` | `string` | 否 | 最长 1000；示例：`desktop`, `mobile`, `tablet` | 设备类型(device): desktop/mobile，默认 desktop |
| `keyword` | `string` | 否 | 最长 1024 | 关键词；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等  |
| `language` | `string` | 否 | 最长 1000；示例：`en_US`, `en_AU`, `nl_BE`, `fr_BE`, `pt_BR`, `en_CA`, `fr_CA`, `zh_CN` | 语言 |
| `deliveryZip` | `string` | 否 | 最长 1000；示例：`10001`, `2000`, `1000`, `01000-000`, `M5A 1A1`, `100000`, `11511`, `75001` | Generate a recommended postal code commonly used for Amazon frontend address entry in the specified country (preferably from a major city). For example, Amazon US site often uses New York's postal code 10001 |
| `amazonDomain` | `string` | 否 | 默认 `"amazon.com"`；格式受正则约束（见原始 Schema）；示例：`amazon.com`, `amazon.com.au`, `amazon.com.be`, `amazon.com.br`, `amazon.ca`, `amazon.cn`, `amazon.eg`, `amazon.fr` | 亚马逊各个国家站点，默认 amazon.com |


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
    "name": "/amazon/search",
    "arguments": {
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总行数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `keyword` | `string` | 否 |  | keyword |
| `products` | `array<object>` | 否 |  | 搜索结果列表 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `tags` | `string` | 否 |  | 标签 |
| `brand` | `string` | 否 |  | 品牌 |
| `price` | `number` | 否 |  | 价格 |
| `title` | `string` | 否 |  | 标题 |
| `badges` | `string` | 否 |  | 亚马逊前台搜索标识 |
| `offers` | `string` | 否 |  | 优惠信息 |
| `rating` | `number` | 否 |  | 评分 |
| `weight` | `string` | 否 |  | 重量 |
| `asinUrl` | `string` | 否 |  | 链接 |
| `keyword` | `string` | 否 |  | keyword |
| `options` | `string` | 否 |  | 选项 |
| `ratings` | `integer` | 否 |  | 评分数 |
| `currency` | `string` | 否 |  | 币种 |
| `delivery` | `string` | 否 |  | 配送信息 |
| `imageUrl` | `string` | 否 |  | 缩略图 |
| `oldPrice` | `number` | 否 |  | 划线价格 |
| `position` | `integer` | 否 |  | 位置 |
| `dimension` | `string` | 否 |  | 尺寸 |
| `priceUnit` | `string` | 否 |  | 价格单位 |
| `sponsored` | `boolean` | 否 |  | 是否赞助商 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：amazon |
| `fulfillment` | `string` | 否 |  | 配送信息 |
| `sellerNation` | `string` | 否 |  | 卖家国籍 |
| `availableDate` | `string` | 否 | 格式 `date` | 上架时间 |
| `extractedPrice` | `number` | 否 |  | 解析后的价格 |
| `snapEbtEligible` | `boolean` | 否 |  | SNAP/EBT资格 |
| `extractedOldPrice` | `number` | 否 |  | 解析后的划线价格 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `extractedPriceUnit` | `number` | 否 |  | 解析后的价格单位 |
| `monthlySalesRevenue` | `string` | 否 |  | 月销售额 |

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
