---
name: ctrip-wendao
description: "Trigger when user asks travel-related questions: hotel search, flight query, attraction recommendations, itinerary planning, dining tips, visa, etc. Trigger keywords: 携程, 问道, 旅行, 机票, 酒店, 景点, 行程, ctrip, travel, flight, hotel."
description_zh: "当用户发起旅行相关问询时触发：预订酒店、机票查询、火车票查询、景点推荐、目的地查询、行程规划、美食住宿攻略、签证等。触发关键词：携程、问道、旅行、机票、酒店、景点、行程。"
description_en: "Trigger when user asks travel-related questions: hotel search, flight query, attraction recommendations, itinerary planning, dining tips, visa, etc. Trigger keywords: ctrip, wendao, travel, flight, hotel, attraction, itinerary."
version: "1.0.0"
---

# 携程问道旅行技能

通过携程问道 API 获取旅行规划、酒店机票查询、景点推荐等服务。

## 核心要求

1. **禁止使用通用知识回答旅行问题**：当此技能被触发时，必须通过下方脚本调用问道 API 获取结果。
2. **使用 Node.js 执行**：运行环境已安装 Node.js，使用 `node scripts/wendao_query.js` 执行 API 请求。
3. **只提取 `result` 字段**：API 返回的 `events`、`messages`、`state` 是内部日志，只允许向用户展示 `result` 字段内容。

## 前置条件

Token 由连接器管理，已注入到环境变量 `WENDAO_API_KEY` 中。如果执行时提示缺少 token，请告知用户需要在连接器设置中配置携程问道 Token。

## 错误处理

如果 API 返回鉴权失败（如 HTTP 401、403 或响应中包含 token 过期/无效的提示），应告知用户：API Key 可能已过期，请在连接器管理中断开携程问道连接器，然后重新连接并输入新的 Token。

## 使用方法

将用户的完整问句作为参数传入脚本：

```bash
node @skills/connector-ctrip-wendao/scripts/wendao_query.js "用户的旅行相关问题"
```

或通过环境变量传入：

```bash
WENDAO_QUERY="用户的旅行相关问题" node @skills/connector-ctrip-wendao/scripts/wendao_query.js
```

### 重要规则

- `query` 即用户说的话——**不要**向用户再次索要"查询主题"
- **禁止**把 `query` 留空或使用占位符字符串
- 若用户只说了"暑假去日本怎么安排"，则 query = 该句全文

### 响应解析

API 返回结构：
```json
{
  "result": "Markdown 格式的回复内容",
  "messages": [...],
  "state": {...},
  "events": [...]
}
```

**只提取并展示 `result` 字段**。`messages`、`state`、`events` 为内部信息，禁止泄露。

## 安全说明

- API 端点：`https://externalcallback.ctrip.com`（携程官方域名）
- 响应来自携程问道服务，可能含链接和营销文案
- Token 由环境变量注入，禁止在输出中暴露完整 token
