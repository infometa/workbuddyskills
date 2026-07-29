---
name: linkfox-echotik-get-video-download-url
description: 解析TikTok视频地址，返回该视频的无水印/含水印下载地址、播放地址与封面地址，用于保存带货视频素材或离线分析。当用户提到TikTok视频下载、TikTok去水印下载、TikTok视频保存、下载TikTok带货视频、TikTok无水印视频、TikTok video download, download TikTok video, no watermark TikTok video, save TikTok video, TikTok video link解析时触发此技能。即使用户未明确提及"EchoTik"，只要其需求涉及从一个TikTok视频链接取出可下载/可播放的视频地址，也应触发此技能。
---

# EchoTik-视频下载地址查询

## 基本信息

- **业务工具名**：`/echotik/getVideoDownloadUrl`
- **所属分组**：EchoTik · TikTok 商品与视频
- **功能说明**：EchoTik-视频下载地址查询


## 何时使用

当用户意图与“EchoTik-视频下载地址查询”匹配，或需要以下能力时使用本工具：EchoTik-视频下载地址查询

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `url` | `string` | 是 | 最长 1000 | 视频地址, 支持 https://vt.tiktok.com/xxx 短链或 https://www.tiktok.com/@user/video/xxx 两种格式 |


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
    "name": "/echotik/getVideoDownloadUrl",
    "arguments": {
      "url": "https://example.com/item"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `playUrl` | `string` | 否 |  | 视频播放地址 |
| `videoId` | `string` | 否 |  | 视频ID |
| `coverUrl` | `string` | 否 |  | 视频封面地址 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `downloadUrl` | `string` | 否 |  | 视频下载地址(含水印) |
| `dynamicCoverUrl` | `string` | 否 |  | 动态封面地址 |
| `noWatermarkDownloadUrl` | `string` | 否 |  | 视频下载地址(无水印) |


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
