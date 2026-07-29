---
name: linkfox-junglescout-sales-estimates
description: Jungle Scout ASIN销售估算查询，按日维度返回指定ASIN在一段时间内的每日预估销量与最新已知价格，覆盖美国、英国、德国、日本等10个站点。当用户提到ASIN销量预估、ASIN日销量、销售估算、竞品销量监控、日均销量、销量趋势、产品销量追踪、Jungle Scout销量数据、sales estimates, daily sales, estimated units sold, ASIN sales tracking, competitor sales monitoring, product sales trend, daily unit sales时触发此技能。即使用户未明确提及"Jungle Scout"，只要其需求涉及查看某个亚马逊ASIN在一段时间内的每日销量估算数据，也应触发此技能。
---

# 查询ASIN销售估算

## 基本信息

- **业务工具名**：`/tool-jungle-scout/sales-estimates/query`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：查询ASIN销售估算：GET sales_estimates_query，按日期区间返回每日估算销量与最后已知价格


## 何时使用

当用户意图与“查询ASIN销售估算”匹配，或需要以下能力时使用本工具：查询ASIN销售估算：GET sales_estimates_query，按日期区间返回每日估算销量与最后已知价格

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 是 | 最长 1000；示例：`B08JYQLKXZ` | 要查询的产品ASIN(10位Amazon标准ASIN) |
| `endDate` | `string` | 是 | 最长 1000；示例：`2025-11-02` | 结束日期(YYYY-MM-DD)；须早于当前日期 |
| `startDate` | `string` | 是 | 最长 1000；示例：`2025-10-01` | 开始日期(YYYY-MM-DD) |
| `marketplace` | `string` | 是 | 最长 1000；示例：`us`, `uk`, `de`, `in`, `ca`, `fr`, `it`, `es` | 目标市场代码 |


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
    "name": "/tool-jungle-scout/sales-estimates/query",
    "arguments": {
      "marketplace": "us",
      "asin": "B08JYQLKXZ",
      "startDate": "2025-10-01",
      "endDate": "2025-11-02"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `salesEstimateList` | `array<object>` | 否 |  | 销售估算结果列表 |

### 嵌套输出结构：`salesEstimateList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `id` | `string` | 否 |  | 销售数据标识(市场/ASIN) |
| `asin` | `string` | 否 |  | 产品ASIN |
| `type` | `string` | 否 |  | 响应资源类型(固定 sales_estimate_result) |
| `isParent` | `boolean` | 否 |  | 是否父ASIN |
| `variants` | `array<any>` | 否 |  | 变体ASIN列表(查询为父体时列出子变体，否则为空数组) |
| `isVariant` | `boolean` | 否 |  | 是否变体ASIN |
| `parentAsin` | `string` | 否 |  | 父产品ASIN；与查询ASIN相同表示查询目标为父体；不同则为变体；为空表示独立ASIN |
| `isStandalone` | `boolean` | 否 |  | 是否独立ASIN |
| `dailyEstimates` | `array<object>` | 否 |  | 按日期的销售估算序列 |

### 嵌套输出结构：`salesEstimateList.dailyEstimates`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `date` | `string` | 否 |  | 销售日期(YYYY-MM-DD) |
| `lastKnownPrice` | `number` | 否 |  | 该日最后已知价格(USD) |
| `estimatedUnitsSold` | `integer` | 否 |  | 该日估算销量(件) |

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
