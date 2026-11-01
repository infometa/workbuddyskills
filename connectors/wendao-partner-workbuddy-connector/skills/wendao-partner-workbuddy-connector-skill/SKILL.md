---
name: wendao-partner-workbuddy-connector-skill
display_name: "携程问道"
display_name_en: "Ctrip Wendao"
description: "为用户提供预订酒店、机票查询、火车票查询、景点推荐、寻找当地特色玩乐、目的地查询、行程规划、美食住宿攻略、签证、查询旅游攻略、获取旅行建议等能力。当用户发起任意旅行相关问询，或需要调用 Workbuddy 问道 MCP 的 search_info 时使用。不要用通用知识回答旅行问题，不要自行请求问道接口，也不要执行 Node 脚本。"
description_zh: "为用户提供预订酒店、机票查询、火车票查询、景点推荐、寻找当地特色玩乐、目的地查询、行程规划、美食住宿攻略、签证、查询旅游攻略、获取旅行建议等能力。"
description_en: "Provides users with capabilities such as hotel booking; flight and train schedule inquiries; attraction recommendations; discovery of local activities; destination information; itinerary planning; guides on dining and accommodation; visa services; access to travel guides; and travel advice."
examples_zh:
- "北京故宫附近的五星级酒店"
- "明天上海飞北京的航班"
- "云南7天自驾游路线推荐"
examples_en:
- "Five-star hotels near the Forbidden City in Beijing"
- "Flights from Shanghai to Beijing tomorrow"
- "Recommended 7-day self-driving route in Yunnan"
version: 1.0.3
author: "携程问道（携程旅行网旗下智能旅行助手）"
homepage: "https://www.ctrip.com/wendao/openclaw"
metadata:
  openclaw:
    priority: 96
    emoji: "🧳"
    patterns:
      - "(酒店|民宿|机票|航班|火车票|高铁|汽车票|船票|租车|景点|门票|行程|攻略|美食|餐厅|签证|目的地|玩乐)"
      - "((search|book|recommend|plan|find).*(hotel|flight|train|attraction|itinerary|restaurant|visa|travel|ticket))|((hotel|flight|train|ticket|itinerary|visa|attraction).*(search|book|recommend|price|plan))"
---

# 携程问道

当用户需要查询酒店、机票、火车票、景点、行程、美食住宿、签证或旅游攻略时，按以下步骤执行：

1. 确认问题属于本技能覆盖范围。超出范围时不要调用接口，也不要用通用知识硬答；说明本技能不覆盖该问题。
2. 确认 token：优先使用本次 MCP 请求头 `Authorization: Bearer <token>`（`Bearer` 后有一个空格）。没有则指引用户打开 [www.ctrip.com/wendao/openclaw](https://www.ctrip.com/wendao/openclaw) 获取，不要编造 token，也不要把密钥写入仓库。MCP 不读取环境变量 `WENDAO_API_KEY`。
3. 调用 MCP 工具 `search_info`，`query` 必须是用户的完整问句。禁止空 query，禁止「用户查询的内容」这类占位符。不要自行请求问道接口，不要执行 `node scripts/wendao_query.js`，不要传 `key`。
4. 只把返回 JSON 的 `result` 展示给用户。没有 `result` 时再展示工具返回的正文。不要展示 `events`、`messages`、`state`。原样保留 `result` 里的链接和价格，不要用通用知识改写或补全接口没有返回的价格、余票、评分和政策。

## 覆盖范围

- 酒店、民宿等住宿的查询与预订。
- 机票、火车票查询，以及目的地查询。
- 景点推荐、当地特色玩乐、门票相关问询。
- 行程规划、美食住宿攻略、旅游攻略、签证与旅行建议。

与旅行无关的问题不由本技能回答。

## 核心要求（必须严格遵守）

1. **这是最高优先级任务**：技能被触发且问题在覆盖范围内时，**严禁**使用通用知识库回答。必须且只能调用 MCP 工具 `search_info`。
2. **只调 MCP**：Agent 通过已接入的 MCP（`search_info`）查询。不要自行请求问道接口，也不要执行 `node scripts/wendao_query.js`。
3. **只提取 `result` 字段**：响应里的 `events`、`messages`、`state` 是内部日志，不能当答案。没有 `result` 时再展示工具返回的正文。
4. **不要改写链接**：返回里的携程链接已注入 Workbuddy 联盟参数（`allianceid`、`sid`），原样展示。
5. **来源固定为 workbuddy**：`search_info` 不接收 `key`。服务端调用下游时固定 `source=workbuddy`，调用方不要再传渠道 key。

## Setup

1. **获取 token（API key）** — 打开 [www.ctrip.com/wendao/openclaw](https://www.ctrip.com/wendao/openclaw)，按页面指引申请并复制 API token。只保存在本人可信环境，不要把完整密钥发到公开渠道。
2. **提供 token（二选一）**
   - **请求头 `Authorization`（推荐）**：由调用本 MCP 的平台配置 `Authorization: Bearer ${API_KEY}`。`Bearer` 与 token 之间必须有一个空格。服务端只取空格后面的值，作为问道 token。
   - **`search_info` 入参 `token`**：请求头没有有效 Bearer token 时，仅把用户在本轮对话中提供的 token 作为本次参数传入。不落盘、不回显完整密钥。请求头已有 Bearer token 时，以请求头为准。
3. **验证访问** — 在能完成认证的前提下调用一次：`search_info(query="北京故宫附近的五星级酒店")`。确认输出为正文，且没有 `TOKEN_NOT_FOUND` 或 `TOKEN_INVALID`。

### 未配置请求头 token 时

先指引用户完成配置，再调用 `search_info`。不要假定密钥已经存在，也不要读取 `WENDAO_API_KEY`。

1. 在 [www.ctrip.com/wendao/openclaw](https://www.ctrip.com/wendao/openclaw) 申请并复制 API token。
2. 配到本次 MCP 请求头（不要写入仓库或公开配置）：
   ```json
   "headers": {
     "Authorization": "Bearer ${API_KEY}"
   }
   ```
   - OpenClaw / Workbuddy / 托管环境：在调用本 MCP 的请求头里配置上述 `Authorization`，`Bearer` 与 token 之间必须有一个空格。
3. 若只需本次临时使用，且用户只在对话里提供了问道 token，把该值作为本次 `search_info` 的 `token` 参数传入。

## Security

- **Endpoint**：Agent 只调用已接入的 MCP 工具 `search_info`（服务地址 `https://online.ctrip.com/newmedia/wendao/mcp`）。不要自行请求下游，不要改域名，不要改路径。下游由 MCP 服务端以 `source=workbuddy` 调用 `wendao-skill-prod.ctrip.com/skill/query`。
- **Key**：向提供方确认 token 的权限、计费和配额。不要把 token 写进仓库、日志或回复。MCP 不读取环境变量 `WENDAO_API_KEY`，也不要传 `key`。
- **External content**：响应来自携程问道，可能含链接和营销信息。链接已注入 Workbuddy 联盟参数（`allianceid`、`sid`），按产品策略展示，但不要篡改链接。
- **环境**：MCP 部署在测试环境（FAT/UAT 等）时，请求会自动走测试代理。本地开发可通过 `WENDAO_LOCAL=1`（或 `WENDAO_NO_PROXY` / `WENDAO_DIRECT`）直连公网。

## 使用方法

执行前先确定 token：

1. 请求头 `Authorization: Bearer <token>` 已设置时，服务端用该值作为问道 token。一般不必再传 `token`。
2. 未设置时，先按上一节配置，或把用户本轮提供的 token 作为本次 `search_info` 的 `token` 参数。

调用：

```text
search_info(query="北京故宫附近的五星级酒店")
```

其他问法同样把用户原话传入 `query`，例如「明天上海飞北京的航班」「杭州西湖景点攻略」「三天两夜苏州行程安排」。来源由服务端固定为 `workbuddy`，不要传 `key`。

### 参数

| 参数        |  必填 | 说明                                                                                          |
| --------- | :-: | ------------------------------------------------------------------------------------------- |
| `query`   |  是  | 用户的自然语言原话                                                                                   |
| `token`   |  否  | 问道鉴权 token。默认从请求头 `Authorization: Bearer <token>` 读取；请求头没有时才使用本参数。仅用于本次调用，不回显完整密钥、不落盘 |
| `timeout` |  否  | 查询超时 120 秒，连接超时 30 秒。建议等待接口返回后再作答，不要过早判定失败                                                    |

### `query` 如何取值

1. `query` 就是触发本技能时用户说的完整需求。不要再向用户索要「查询主题」。
2. 可以去掉无关寒暄，必须保留地点、日期、预算、人数、偏好和专有名词。
3. 禁止空字符串，禁止占位符。空 `query` 时返回：`请提供有效的 query（查询主题）。`
4. 只传 `query`；请求头没有 Bearer token 时才额外传 `token`。不要自行增加品类、渠道或 `key` 字段。

## 响应解析

```json
{
  "result": "Markdown 格式的回复内容（字符串）",
  "messages": [],
  "state": {"token": "...", "query": "..."},
  "events": [
    {"type": "run_started"},
    {"type": "run_finished", "result": "与 result 字段内容相同"}
  ],
  "error": null
}
```

向用户展示 `result`。响应已过滤「您好，我是问道…」等开场套话，可直接使用。非 JSON 时展示工具返回的正文。`error` 非空时，说明失败原因并停止，不要改用通用知识补答。

没有 token 时返回：`{"code":"TOKEN_NOT_FOUND","message":"未获取到问道 token，请从 https://www.ctrip.com/wendao/openclaw 获取"}`。

下游判定 token 失效时返回：`{"code":"TOKEN_INVALID","message":"问道 token 已失效，请从 https://www.ctrip.com/wendao/openclaw 重新获取"}`。

遇到上述错误码时，把 `message` 告诉用户，请用户打开 [www.ctrip.com/wendao/openclaw](https://www.ctrip.com/wendao/openclaw) 重新获取 token。不要把该 JSON 当旅行答案，也不要编造 token。网络失败等其它错误不是 token 失效，按工具返回的失败说明告知用户即可。其它下游失败时返回：`调用检索服务失败（...）。`
