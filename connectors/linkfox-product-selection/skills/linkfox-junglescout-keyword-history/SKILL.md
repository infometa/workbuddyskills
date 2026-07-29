---
name: linkfox-junglescout-keyword-history
description: Jungle Scout关键词历史搜索量查询，按7天周期返回亚马逊关键词的精确搜索量趋势，覆盖美国、英国、德国、日本等10个站点。当用户提到关键词搜索量趋势、历史搜索量、搜索热度变化、关键词季节性、搜索量波动、Jungle Scout搜索量、keyword search volume history, keyword trend, search volume over time, seasonal search volume, keyword popularity trend时触发此技能。即使用户未明确提及"Jungle Scout"，只要其需求涉及查看某个亚马逊关键词在一段时间内的搜索量变化趋势，也应触发此技能。
---

# 查询关键词历史精确搜索量

## 基本信息

- **业务工具名**：`/tool-jungle-scout/keywords/historical-search-volume`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：查询关键词历史精确搜索量：GET historical_search_volume，按7天周期返回区间内各周估算搜索量


## 何时使用

当用户意图与“查询关键词历史精确搜索量”匹配，或需要以下能力时使用本工具：查询关键词历史精确搜索量：GET historical_search_volume，按7天周期返回区间内各周估算搜索量

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `endDate` | `string` | 是 | 最长 1000；示例：`2025-02-01` | 结束日期(YYYY-MM-DD)；与开始日期间隔最大366天 |
| `keyword` | `string` | 是 | 最长 1000；示例：`sushi` | 要查询的关键词 |
| `startDate` | `string` | 是 | 最长 1000；示例：`2025-01-05` | 开始日期(YYYY-MM-DD) |
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
    "name": "/tool-jungle-scout/keywords/historical-search-volume",
    "arguments": {
      "marketplace": "us",
      "keyword": "sushi",
      "startDate": "2025-01-05",
      "endDate": "2025-02-01"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `historicalSearchVolumeList` | `array<object>` | 否 |  | 历史搜索量周期列表 |

### 嵌套输出结构：`historicalSearchVolumeList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `id` | `string` | 否 |  | 数据周期标识(市场/关键词/日期范围) |
| `type` | `string` | 否 |  | 响应资源类型(固定 historical_keyword_search_volume) |
| `estimateEndDate` | `string` | 否 |  | 周期结束日期(YYYY-MM-DD，7天统计周期终点) |
| `estimateStartDate` | `string` | 否 |  | 周期开始日期(YYYY-MM-DD，7天统计周期起点) |
| `estimatedExactSearchVolume` | `integer` | 否 |  | 该周期内精确匹配搜索量(次/周) |

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
