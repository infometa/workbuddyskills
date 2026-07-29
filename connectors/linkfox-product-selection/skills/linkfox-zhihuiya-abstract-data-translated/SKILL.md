---
name: linkfox-zhihuiya-abstract-data-translated
description: 从智慧芽（PatSnap）专利数据库获取专利标题和摘要的翻译版本。当用户要求专利摘要翻译、专利标题翻译、翻译后的专利摘要、其他语言的专利内容、中文/英文/日文的专利摘要，或需要通过专利ID或公开号查询特定专利的摘要、标题、patent abstract translation, patent title translation, PatSnap, patent translation, abstract lookup时触发此技能。当用户提到智慧芽、PatSnap或专利摘要查询时也应触发，即使未明确说"翻译"。
---

# 智慧芽-摘要翻译

## 基本信息

- **业务工具名**：`/zhihuiya/abstractDataTranslated`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：工具中文名：智慧芽-摘要翻译
描述：可以通过输入专利ID或专利公开号查询具体某条专利的标题和摘要的翻译文本（支持中文、英文、日文任意一种）
关键词：智慧芽,摘要,翻译
- **关键词**：智慧芽,摘要,翻译


## 何时使用

当用户意图与“智慧芽-摘要翻译”匹配，或需要以下能力时使用本工具：工具中文名：智慧芽-摘要翻译
描述：可以通过输入专利ID或专利公开号查询具体某条专利的标题和摘要的翻译文本（支持中文、英文、日文任意一种）
关键词：智慧芽,摘要,翻译

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `lang` | `string` | 否 | 默认 `"en"`；最长 1000；示例：`en`, `cn`, `jp` | 翻译语言，支持cn、en、jp |
| `patentId` | `string` | 否 | 最长 60000 | 专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开 |
| `patentNumber` | `string` | 否 | 最长 60000 | 公开(公告)号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开 |
| `replaceByRelated` | `integer` | 否 | 默认 `0`；示例：`1`, `0` | 摘要无法获取时是否用同族专利摘要替代：1是 0否 |


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
    "name": "/zhihuiya/abstractDataTranslated",
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
| `title` | `string` | 否 |  | 标题翻译 |
| `patentId` | `string` | 否 |  | 专利Id |
| `pnRelated` | `string` | 否 |  | 替代专利的公开号（仅当使用同族专利替代时提供） |
| `abstractText` | `string` | 否 |  | 摘要翻译 |

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
