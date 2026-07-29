---
name: linkfox-echotik-product-video
description: 查询TikTok商品的关联带货视频数据，包括播放量、点赞、评论、分享、视频销量与GMV，分析商品的视频营销表现与达人内容效果。当用户提到TikTok商品视频、TikTok带货视频、商品关联视频、视频营销分析、达人视频表现、TikTok视频销量、TikTok video sales, product video analysis, influencer video performance, TikTok promotional videos, product marketing videos时触发此技能。即使用户未明确提及"EchoTik"或"商品视频"，只要其需求涉及查看某个TikTok商品有哪些带货视频、视频的播放和转化数据，也应触发此技能。
---

# EchoTik-TikTok商品视频

## 基本信息

- **业务工具名**：`/echotik/listProductVideo`
- **所属分组**：EchoTik · TikTok 商品与视频
- **功能说明**：工具中文名: EchoTik-TikTok商品视频
功能说明: 根据TikTok商品ID查询该商品关联的带货推广视频列表,提供视频播放量、点赞、评论、分享、收藏及视频销量与GMV等数据,并支持按播放量、点赞数、分享数、视频销量、视频GMV、发布时间排序,用于分析商品的视频营销表现与达人内容效果。
关键词: EchoTik, TikTok视频, TikTok商品视频, 商品关联视频, 带货视频, 视频播放量, 视频销量, 达人视频分析, EchoTik-TikTok, EchoTik-TikTok商品视频


## 何时使用

当用户意图与“EchoTik-TikTok商品视频”匹配，或需要以下能力时使用本工具：工具中文名: EchoTik-TikTok商品视频
功能说明: 根据TikTok商品ID查询该商品关联的带货推广视频列表,提供视频播放量、点赞、评论、分享、收藏及视频销量与GMV等数据,并支持按播放量、点赞数、分享数、视频销量、视频GMV、发布时间排序,用于分析商品的视频营销表现与达人内容效果。
关键词: EchoTik, TikTok视频, TikTok商品视频, 商品关联视频, 带货视频, 视频播放量, 视频销量, 达人视频分析, EchoTik-TikTok, EchoTik-TikTok商品视频

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `userId` | `string` | 否 | 最长 1000 | 达人ID |
| `pageNum` | `integer` | 否 | 默认 `1` | 分页页码 |
| `pageSize` | `integer` | 否 | 默认 `50` | 分页条数(须为10的倍数, 最大100; 官方接口单页上限10, 内部按10每页多次拉取后合并) |
| `sortType` | `integer` | 否 | 默认 `1`；示例：`0`, `1` | 排序方式, 0=升序 1=降序 |
| `productId` | `string` | 是 | 最长 1000 | 商品ID |
| `maxCreateTime` | `integer` | 否 |  | 视频发布时间区间-结束(秒级时间戳) |
| `minCreateTime` | `integer` | 否 |  | 视频发布时间区间-开始(秒级时间戳) |
| `productVideoSortField` | `integer` | 否 | 默认 `1`；示例：`1`, `2`, `3`, `4`, `5`, `6` | 排序字段, 1=播放量 2=点赞数 3=分享数 4=视频销量 5=视频销售GMV 6=发布时间 |


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
    "name": "/echotik/listProductVideo",
    "arguments": {
      "productId": "example-id",
      "pageSize": 50,
      "sortType": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 视频列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `ratio` | `string` | 否 |  | 视频清晰度 |
| `width` | `string` | 否 |  | 视频宽度 |
| `height` | `string` | 否 |  | 视频高度 |
| `region` | `string` | 否 |  | 区域代码 |
| `userId` | `string` | 否 |  | 达人ID |
| `hashTag` | `string` | 否 |  | 话题标签 |
| `videoId` | `string` | 否 |  | 视频ID |
| `coverUrl` | `string` | 否 |  | 视频封面URL |
| `dataSize` | `string` | 否 |  | 视频文件大小 |
| `duration` | `integer` | 否 |  | 视频时长(秒) |
| `playAddr` | `string` | 否 |  | 视频播放地址(可能过期) |
| `productId` | `string` | 否 |  | 商品ID |
| `videoDesc` | `string` | 否 |  | 视频描述 |
| `createDate` | `string` | 否 | 格式 `date` | 视频发布日期 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 商品来源 |
| `officialUrl` | `string` | 否 |  | TikTok官方视频地址 |
| `totalDiggCnt` | `integer` | 否 |  | 点赞数 |
| `totalViewsCnt` | `integer` | 否 |  | 播放量 |
| `totalSharesCnt` | `integer` | 否 |  | 分享数 |
| `totalCommentsCnt` | `integer` | 否 |  | 评论数 |
| `totalFavoritesCnt` | `integer` | 否 |  | 收藏数 |
| `totalVideoSaleCnt` | `integer` | 否 |  | 视频销量(估算) |
| `totalVideoSaleGmvAmt` | `integer` | 否 |  | 视频销售GMV(估算) |

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
