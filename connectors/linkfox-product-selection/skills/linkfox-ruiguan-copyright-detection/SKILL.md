---
name: linkfox-ruiguan-copyright-detection
description: 图片版权侵权检测与风险分析。当用户提到版权检测、版权核查、图片侵权检查、图片版权风险、版权相似度搜索、TRO风险分析、权利人查询、版权合规验证、copyright detection, image infringement, copyright risk, TRO risk, copyright lookup, infringement analysis, Ruiguan时触发此技能。即使用户未明确提及"版权"，只要其需求涉及检查图片是否可能侵犯已登记的版权作品，也应触发此技能。
---

# 睿观-版权检测

## 基本信息

- **业务工具名**：`/ruiguan/copyrightDetection`
- **所属分组**：睿观 · 合规检测
- **功能说明**：支持根据图片URL进行版权检测


## 何时使用

当用户意图与“睿观-版权检测”匹配，或需要以下能力时使用本工具：支持根据图片URL进行版权检测

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `imageUrl` | `string` | 是 | 最长 1000 | 检测的版权图片URL |
| `topNumber` | `integer` | 是 | 默认 `100`；最小 10；最大 100 | 召回数量（默认100，最大200） |
| `enableRadar` | `boolean` | 是 | 默认 `true` | 是否开启雷达检测 |


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
    "name": "/ruiguan/copyrightDetection",
    "arguments": {
      "imageUrl": "https://example.com/item",
      "topNumber": 100,
      "enableRadar": true
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 检测结果列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `detectId` | `string` | 否 |  | 检测id |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `link` | `string` | 否 |  | 版权官网链接 |
| `path` | `string` | 否 |  | 版权画图片路径 |
| `troCase` | `boolean` | 否 |  | 是否有TRO维权史 |
| `pathThumb` | `string` | 否 |  | 版权画缩略图路径 |
| `troHolder` | `boolean` | 否 |  | 是否是TRO权利人的版权 |
| `similarity` | `string` | 否 |  | 相似度 |
| `rightsOwner` | `string` | 否 |  | 权利人 |
| `copyrightUrl` | `string` | 否 |  | 来源 |
| `copyrightCode` | `string` | 否 |  | 版权标识码 |
| `subRadarResult` | `integer` | 否 |  | 1-侵权 0-不侵权 ,null 没有进行雷达检测 |

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
