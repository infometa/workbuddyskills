---
name: linkfox-zhihuiya-fulltext-image
description: 通过专利ID或公开号获取专利文件中的全文附图（图纸、示意图、图表）。当用户询问专利图片、专利图纸、专利示意图、专利插图、全文附图、专利图表、专利技术图或想查看、下载专利文件中的嵌入图片、patent fulltext drawings, patent diagrams, technical drawings, patent images, PatSnap时触发此技能。即使用户未明确提及"全文附图"，只要其需求涉及获取特定专利中的视觉内容（图纸、示意图、图表），也应触发此技能。
---

# 智慧芽-全文附图

## 基本信息

- **业务工具名**：`/zhihuiya/fulltextImage`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：工具中文名：智慧芽-全文附图
描述：可以通过输入专利ID或专利公开号查询具体某条专利的全文附图信息。包含：全文附图图片类型、全文附图图片下载路径。
关键词：智慧芽,全文,附图
- **关键词**：智慧芽,全文,附图


## 何时使用

当用户意图与“智慧芽-全文附图”匹配，或需要以下能力时使用本工具：工具中文名：智慧芽-全文附图
描述：可以通过输入专利ID或专利公开号查询具体某条专利的全文附图信息。包含：全文附图图片类型、全文附图图片下载路径。
关键词：智慧芽,全文,附图

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `limit` | `string` | 否 | 默认 `"100"`；最长 1000 | 返回图片总量，最大100 |
| `offset` | `string` | 否 | 最长 1000 | 偏移量 |
| `patentId` | `string` | 否 | 最长 1000 | 专利ID |
| `patentNumber` | `string` | 否 | 最长 1000 | 公开(公告)号 |


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
    "name": "/zhihuiya/fulltextImage",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 专利列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `pn` | `string` | 否 |  | 公开(公告)号 |
| `patentId` | `string` | 否 |  | 专利Id |
| `imageType` | `string` | 否 |  | 图片类型 |
| `fulltextImagePath` | `string` | 否 |  | 图片路径 |

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
