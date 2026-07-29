---
name: linkfox-zhihuiya-patent-forward-citation
description: 从智慧芽专利数据库查询专利的前向引用详情。当用户询问专利引用、被引用专利、引用文献、专利参考文献、前向引用、在先技术引用或想查看特定专利在申请过程中引用了哪些专利、非专利文献、patent cited references, forward citations, patent references, citation analysis, PatSnap时触发此技能。当用户提供专利ID或公开号并需要引用信息时，即使未明确说"前向引用"，任何关于专利引用了哪些参考文献的请求都适用。
---

# 智慧芽-专利引用

## 基本信息

- **业务工具名**：`/zhihuiya/patentForwardCitation`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：工具中文名：智慧芽-专利引用
描述：可以通过输入专利ID或专利公开号查询具体某条专利在申请过程中引用专利和文献的详情。
关键词：智慧芽,专利,引用,文献
- **关键词**：智慧芽,专利,引用,文献


## 何时使用

当用户意图与“智慧芽-专利引用”匹配，或需要以下能力时使用本工具：工具中文名：智慧芽-专利引用
描述：可以通过输入专利ID或专利公开号查询具体某条专利在申请过程中引用专利和文献的详情。
关键词：智慧芽,专利,引用,文献

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `patentId` | `string` | 否 | 最长 60000 | 专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条 |
| `patentNumber` | `string` | 否 | 最长 60000 | 公开公告号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条 |


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
    "name": "/zhihuiya/patentForwardCitation",
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
| `citedOthers` | `array<object>` | 否 |  | 引用非专利文献 |
| `citedPatents` | `array<object>` | 否 |  | 引用专利 |

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
