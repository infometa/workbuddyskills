---
name: linkfox-amazon-alexa-search
description: 通过亚马逊前台的 Alexa 购物助手发起自然语言问答，获取与问题相关的导购回答、推荐商品分组、ASIN 列表，以及可继续追问的问题。每次调用仅支持 1 条 prompt，如需追问须由 agent 总结上下文后拼接新问题发起新请求。可用 url 补充亚马逊页面上下文。当用户提到亚马逊 Alexa、Alexa 购物助手、亚马逊智能助手、AI 导购、对话式选品、自然语言购物、亚马逊聊天问答、Amazon Alexa shopping, conversational shopping, AI shopping assistant, follow-up questions、产品推荐对话、上下文追问等场景时触发此技能。即使用户未明确提及"Alexa"，只要其需求是"在亚马逊前台用自然语言问出商品推荐"，也应触发此技能。
---

# 亚马逊-Alexa助手

## 基本信息

- **业务工具名**：`/amazon/alexaSearch`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：通过自然语言向 Amazon Alexa 发起问答，获取与问题相关的回答、推荐商品、商品信息和可继续追问的问题。仅支持单轮对话问答。支持传入 URL 参数，为本次问答补充指定亚马逊页面上下文。
- **关键词**：Amazon Alexa, Alexa助手, 亚马逊Alexa,  对话式查询, 商品推荐, 商品信息, follow-up questions


## 何时使用

当用户意图与“亚马逊-Alexa助手”匹配，或需要以下能力时使用本工具：通过自然语言向 Amazon Alexa 发起问答，获取与问题相关的回答、推荐商品、商品信息和可继续追问的问题。仅支持单轮对话问答。支持传入 URL 参数，为本次问答补充指定亚马逊页面上下文。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `url` | `string` | 否 | 最长 1000；示例：`https://www.amazon.com/` | 联动页面 URL.用于补充 Alexa 当前答复的页面上下文 |
| `format` | `string` | 否 | 默认 `"markdown"`；最长 1000；示例：`markdown`, `json` | 响应格式.可选 markdown 或 json；默认 markdown。 |
| `prompts` | `array<string>` | 是 | 最多 1000 项；示例：`["best wireless earbuds for running"]`, `["best electric kettle","Compare with similar products"]` | 对话提示词数组.用于发起一次 Alexa 多轮问答，至少 1 条，建议不超过 5 条。多个元素表示同一次调用中的连续追问，会按数组顺序依次发送：先发送 prompts[0]，等待 Alexa 回答后再发送 prompts[1]，再继续发送后续问题。若需要基于上一次工具调用结果继续追问，下一次调用是新的问答上下文，agent 需要根据历史回答和推荐商品自行总结上下文，并组织成新的 prompts 再发起调用。 |


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
    "name": "/amazon/alexaSearch",
    "arguments": {
      "prompts": "[\"best wireless earbuds for running\"]"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 返回消息.成功为 ok |
| `code` | `string` | 否 |  | 返回码.成功为 "200" |
| `data` | `array<object>` | 否 |  | Alexa 查询结果列表.仅当 format=json 时返回结构化结果 |
| `type` | `string` | 否 |  | 渲染类型.markdown 为 stdoutWorkbenches，json 为 json |
| `stdout` | `string` | 否 |  | Alexa 查询结果.Markdown 格式，包含用户问题、Alexa回答、推荐商品和可继续追问的问题 |
| `taskId` | `string` | 否 |  | 任务ID.用于排查和追踪本次查询 |
| `costTime` | `integer` | 否 |  | 接口耗时.单位毫秒 |
| `costToken` | `integer` | 否 |  | 消耗 Token 数.按上游成功对话轮次计费 |
| `resultsNum` | `integer` | 否 |  | 对话结果数量.工具统计字段 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `prompt` | `string` | 否 |  | 用户提示词.对应的问题或者追问 |
| `content` | `string` | 否 |  | Alexa回答内容 |
| `products` | `array<object>` | 否 |  | 推荐商品分组列表.商品列表 |
| `screenshot` | `string` | 否 |  | 本轮对话截图链接 |
| `followUpQuestions` | `array<any>` | 否 |  | 可继续追问的问题列表 |

### 嵌套输出结构：`data.products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `items` | `array<object>` | 否 |  | 推荐商品列表 |
| `title` | `string` | 否 |  | 推荐商品分组标题 |

### 嵌套输出结构：`data.products.items`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `url` | `string` | 否 |  | 商品详情页 URL |
| `asin` | `string` | 否 |  | 商品 ASIN |
| `cover` | `string` | 否 |  | 商品封面图 URL |
| `price` | `string` | 否 |  | 现价 |
| `score` | `string` | 否 |  | 评分 |
| `title` | `string` | 否 |  | 商品标题 |
| `describe` | `string` | 否 |  | 商品简介 |
| `ratingsCount` | `string` | 否 |  | 评价数量 |
| `originalPrice` | `string` | 否 |  | 原价或划线价 |

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
