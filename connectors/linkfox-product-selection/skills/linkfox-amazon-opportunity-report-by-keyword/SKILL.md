---
name: linkfox-amazon-opportunity-report-by-keyword
description: 按关键词查询亚马逊商业洞察报告，涵盖市场潜力、产品特征、用户评论、客户画像、搜索趋势、定价分析六大维度的AI
---

# 亚马逊-商业洞察报告

## 基本信息

- **业务工具名**：`/amazon/opportunity/reportByKeyword`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：工具中文名：亚马逊-商业洞察报告
功能说明:  按亚马逊站点和关键词精准查询亚马逊站内六大核心维度（市场潜力、产品特征、用户评论、客户画像、搜索趋势、定价分析）的原始报告数据，利用 AI 进行多维交叉分析与提炼，最终生成一份极具实操价值的综合性商业洞察报告。
限制：当前仅支持美国站点，本工具的返回值的结果不会存入到databse里面，所以无法使用工具_dataQuery_executeDynamicQuery进行二次加工
时效性：报告基于当前快照数据生成，仅供商业决策参考
关键词：亚马逊选品，市场洞察报告，AI 报告提炼，消费者行为分析，竞争格局调研，细分市场分析
- **关键词**：亚马逊选品，市场洞察报告，AI 报告提炼，消费者行为分析，竞争格局调研，细分市场分析


## 何时使用

当用户意图与“亚马逊-商业洞察报告”匹配，或需要以下能力时使用本工具：工具中文名：亚马逊-商业洞察报告
功能说明:  按亚马逊站点和关键词精准查询亚马逊站内六大核心维度（市场潜力、产品特征、用户评论、客户画像、搜索趋势、定价分析）的原始报告数据，利用 AI 进行多维交叉分析与提炼，最终生成一份极具实操价值的综合性商业洞察报告。
限制：当前仅支持美国站点，本工具的返回值的结果不会存入到databse里面，所以无法使用工具_dataQuery_executeDynamicQuery进行二次加工
时效性：报告基于当前快照数据生成，仅供商业决策参考
关键词：亚马逊选品，市场洞察报告，AI 报告提炼，消费者行为分析，竞争格局调研，细分市场分析

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `site` | `string` | 是 | 默认 `"US"`；最长 1000；示例：`US` | 亚马逊站点代码，当前仅支持 US |
| `keyword` | `string` | 是 | 最长 1000；示例：`iodized salt bulk` | 要查询洞察报告的搜索关键词 |


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
    "name": "/amazon/opportunity/reportByKeyword",
    "arguments": {
      "site": "US",
      "keyword": "iodized salt bulk"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 提示信息或错误信息 |
| `code` | `string` | 否 |  | 响应码 |
| `type` | `string` | 否 |  | 响应类型 |
| `stdout` | `string` | 否 |  | 综合商业洞察报告内容(Markdown格式) |
| `costTime` | `integer` | 否 |  | 总处理耗时（毫秒） |
| `costToken` | `integer` | 否 |  | token消耗量 |


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
