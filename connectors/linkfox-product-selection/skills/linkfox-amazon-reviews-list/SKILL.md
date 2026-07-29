---
name: linkfox-amazon-reviews-list
description: 按ASIN获取并分析亚马逊商品评论，支持15个站点(含美国站)，按星级筛选评论。当用户提到亚马逊评论、美国站评论、商品评价、买家投诉、差评、好评、星级评分、评论分析、评论情感、产品改良建议、Vine评论、已验证购买评论、竞品评论研究、Amazon reviews, US reviews, Amazon.com reviews, product feedback, negative review analysis, positive review analysis, star rating filter, review sentiment analysis, product improvement insights, Vine reviews, competitor reviews, customer feedback时触发此技能。即使用户未明确说"评论"，只要其需求涉及读取、筛选或分析亚马逊商品的买家评论，也应触发此技能。
---

# 亚马逊-商品评论

## 基本信息

- **业务工具名**：`/amazon/reviews/list`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：工具名称：亚马逊-商品评论
工具说明：支持获取亚马逊商品的评论，每个星级最多获取100条，仅支持一个asin，如果需要查询多个asin，请分次调用。
关键词：亚马逊、asin、评论、差评、好评、改良、review
- **关键词**：亚马逊、asin、评论、差评、好评、改良、review


## 何时使用

当用户意图与“亚马逊-商品评论”匹配，或需要以下能力时使用本工具：工具名称：亚马逊-商品评论
工具说明：支持获取亚马逊商品的评论，每个星级最多获取100条，仅支持一个asin，如果需要查询多个asin，请分次调用。
关键词：亚马逊、asin、评论、差评、好评、改良、review

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000；示例：`B08N5WRWNW` | 亚马逊商品ASIN |
| `sortBy` | `string` | 否 | 默认 `"recent"`；格式 `recent\|helpful`；示例：`recent`, `helpful` | 评论排序方式 |
| `star1Num` | `integer` | 否 | 最小 0；最大 100；示例：`10` | 1星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条 |
| `star2Num` | `integer` | 否 | 最小 0；最大 100；示例：`10` | 2星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条 |
| `star3Num` | `integer` | 否 | 最小 0；最大 100；示例：`10` | 3星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条 |
| `star4Num` | `integer` | 否 | 最小 0；最大 100；示例：`10` | 4星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条 |
| `star5Num` | `integer` | 否 | 最小 0；最大 100；示例：`10` | 5星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条 |
| `mediaType` | `string` | 否 | 默认 `"all_contents"`；格式 `all_contents\|media_reviews_only`；示例：`all_contents`, `media_reviews_only` | 媒体类型 |
| `domainCode` | `string` | 否 | 默认 `"com"`；格式 `com\|ca\|co.uk\|in\|de\|fr\|it\|es\|co.jp\|com.au\|com.br\|nl\|se\|com.mx\|ae`；示例：`com`, `ca`, `co.uk`, `in`, `de`, `fr`, `it`, `es` | 亚马逊域名代码 |
| `formatType` | `string` | 否 | 默认 `"all_formats"`；格式 `current_format\|all_formats`；示例：`all_formats`, `current_format` | 格式类型 |
| `reviewerType` | `string` | 否 | 默认 `"all_reviews"`；格式 `all_reviews\|avp_only_reviews`；示例：`all_reviews`, `avp_only_reviews` | 评论者类型 |
| `filterByKeyword` | `string` | 否 | 最长 1000；示例：`quality` | 按关键词筛选评论 |


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
    "name": "/amazon/reviews/list",
    "arguments": {
      "asin": "B08N5WRWNW"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 评论列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总评论数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 总Token消耗 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 产品ASIN |
| `date` | `string` | 否 |  | 评论日期 |
| `text` | `string` | 否 |  | 评论内容 |
| `vine` | `boolean` | 否 |  | 是否Vine Voice评论 |
| `title` | `string` | 否 |  | 评论标题 |
| `locale` | `object` | 否 |  |  |
| `rating` | `string` | 否 |  | 评分 |
| `filters` | `object` | 否 |  |  |
| `reviewId` | `string` | 否 |  | 评论ID |
| `userName` | `string` | 否 |  | 评论者名称 |
| `verified` | `boolean` | 否 |  | 是否已验证购买 |
| `domainCode` | `string` | 否 |  | 国家代码 |
| `statusCode` | `integer` | 否 |  | 状态码 |
| `currentPage` | `integer` | 否 |  | 当前页码 |
| `profilePath` | `string` | 否 |  | 评论者个人资料路径 |
| `variationId` | `string` | 否 |  | 变体ID |
| `countRatings` | `integer` | 否 |  | 产品评分数量 |
| `countReviews` | `integer` | 否 |  | 产品评论数量 |
| `imageUrlList` | `array<any>` | 否 |  | 评论图片列表 |
| `productTitle` | `string` | 否 |  | 产品标题 |
| `sortStrategy` | `string` | 否 |  | 排序策略 |
| `videoUrlList` | `array<any>` | 否 |  | 评论视频列表 |
| `productRating` | `string` | 否 |  | 产品评分 |
| `reviewSummary` | `object` | 否 |  |  |
| `statusMessage` | `string` | 否 |  | 状态消息 |
| `variationList` | `array<any>` | 否 |  | 变体列表 |
| `numberOfHelpful` | `integer` | 否 |  | 有用数量 |

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
