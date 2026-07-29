---
name: linkfox-ruiguan-gun-parts-search
description: 基于睿观的产品图片政策合规检测，通过视觉相似度匹配识别潜在违规商品。当用户提到政策合规检查、产品图片合规、违规检测、禁售商品筛查、基于图片的合规审查、上架前风险排查、policy compliance detection, product compliance review, violation detection, image compliance check, product image risk screening, Ruiguan时触发此技能。即使用户未明确说"合规"，只要其需求涉及将产品图片与违规数据库进行比对，也应触发此技能。
---

# 睿观-政策合规检测（纯图检测）

## 基本信息

- **业务工具名**：`/ruiguan/gunPartsSearch`
- **所属分组**：睿观 · 合规检测
- **功能说明**：支持通过产品图片URL搜寻相似的违规产品


## 何时使用

当用户意图与“睿观-政策合规检测（纯图检测）”匹配，或需要以下能力时使用本工具：支持通过产品图片URL搜寻相似的违规产品

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `imageUrl` | `string` | 是 | 最长 1000 | 检测的版权图片URL |


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
    "name": "/ruiguan/gunPartsSearch",
    "arguments": {
      "imageUrl": "https://example.com/item"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 检测出的政策违规产品列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `detectId` | `string` | 否 |  | 检测记录 id |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `cosine` | `number` | 否 |  | 检测产品与违规产品相似度 |
| `pdTitle` | `string` | 否 |  | 匹配到的违规产品标题 |
| `pdImgOssUrl` | `string` | 否 |  | 匹配到的违规产品图片 URL |
| `pdTitleCHNCensored` | `string` | 否 |  | 匹配到的违规产品中文标题 |

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
