---
name: "agentearth-web-search-news-media"
description: "通用网页、新闻与多媒体检索：用 Google、Bing、Yahoo、Yandex 搜索网页，检索 Google 近期新闻、图片、视频及频道时长；另查热门头条、来源列表、新闻快讯与正文，按关键词、地区、语言、日期、来源与域名筛选并保留原文出处。"
version: "2.0.22"
author: "AgentEarth"
---

# agentearth-web-search-news-media

通用网页、新闻与多媒体检索：用 Google、Bing、Yahoo、Yandex 搜索网页，检索 Google 近期新闻、图片、视频及频道时长；另查热门头条、来源列表、新闻快讯与正文，按关键词、地区、语言、日期、来源与域名筛选并保留原文出处。

请直接调用下方列出的 MCP 工具，不要自行向任何 HTTP 接口发送请求；身份认证已由连接器处理。

## Available Tools

### GetAccountOverview

Returns the authenticated user's account info. Takes no arguments.

**Response fields**: `user_id`, `user_name`, `key_name`, `credit` (remaining balance), `error_no` (`0` = success).

Call this directly — without `RecommendTools` first — whenever the user asks
about their AgentEarth account, user ID, API key name, or credit balance.

### RecommendTools - discover tools for a task

| 参数 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| query | string | 是 | 面向任务的自然语言描述 |
| limit | integer | - | 返回工具数量上限 (1-50)，默认 5 |

Returns a list of candidate tools, each with:

- `tool_name` — the tool's identifier
- `tool_url` — opaque URL to pass to `ExecuteTool`; **never modify it**
- `description`, `when_to_use` — what the tool does and when to pick it
- `credit` — cost of one call, use this plus task fit to choose among candidates
- `input_schema` — JSON Schema for `ExecuteTool`'s `params`
- `associated_tools` — optional companion tools (e.g. a geocoding/ID lookup tool) that may need to be called first if a required field can't be filled directly from user input

Call this before `ExecuteTool` for any external-tool task. Read every
candidate's `input_schema` and `associated_tools` before picking one — some
fields require an ID or code obtained from a companion lookup tool rather
than free text (e.g. a weather tool that needs a location ID resolved by a
geocoding tool first).

### ListTools - browse tools without semantic search

| 参数 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| page | integer | - | 页码，从 1 开始，默认 1 |
| page_size | integer | - | 每页数量 (1-100)，默认 20 |
| keyword | string | - | 按名称/描述关键词过滤 |
| sort | string | - | 排序方式 |

Use when the user wants to browse or search tools by name/category rather
than describe a task.

### GetToolDetail - inspect one tool by exact name

| 参数 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| tool_name | string | 是 | 精确工具名 |

Returns the same shape as one entry from `RecommendTools`/`ListTools`
(`tool_url`, `description`, `input_schema`, etc). Use when you already know
the exact `tool_name` (e.g. from `associated_tools`, or the user named a
specific tool) and don't need semantic search.

### ExecuteTool - run a tool

| 参数 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| tool_url | string | 是 | 从 `RecommendTools`/`GetToolDetail` 原样取得的 URL，禁止修改、拼接或重排 |
| params | object | - | 按所选工具 `input_schema` 构造的入参 |

Must be called after `RecommendTools` or `GetToolDetail`. `tool_url` must be
passed through byte-for-byte as returned — do not edit, re-encode, or
reconstruct it. Build `params` strictly from the selected tool's
`input_schema.properties`; validate `required`, `type`, `enum`, and
`additionalProperties` before calling.

## Examples

- "What's my AgentEarth credit balance?" → call `GetAccountOverview()` directly (no `RecommendTools`).
- "Use AgentEarth to check today's weather in Shanghai" → `RecommendTools({"query": "current weather in Shanghai"})` → pick a weather tool from the candidates → if its `input_schema` needs a location ID/adcode rather than a free-text city name, call the companion lookup tool named in `associated_tools` first → `ExecuteTool({"tool_url": <candidate's tool_url>, "params": {...}})`.
- "Use AgentEarth to check the current Bitcoin price" → `RecommendTools({"query": "current bitcoin price"})` → `ExecuteTool` with the chosen finance tool's `tool_url` and schema-derived `params`.
- "List the AgentEarth tools related to maps" → `ListTools({"keyword": "map"})` to browse by name instead of describing a task.
- User names a specific tool exactly (e.g. "run ae_qweather_geo_top_city") → `GetToolDetail({"tool_name": "ae_qweather_geo_top_city"})` instead of `RecommendTools`.

## Workflow

1. Account questions (user ID, user name, key name, credit balance) → call
   `GetAccountOverview` directly. Skip `RecommendTools` for these.
2. External-tool tasks → call `RecommendTools` with a natural-language
   description of the task, or `ListTools`/`GetToolDetail` when the user
   wants to browse or inspect tools by name.
3. Review the candidates' `tool_url`, `description`, `when_to_use`, and
   `input_schema`. Pick the best fit by task relevance, schema clarity, and
   `credit` cost; keep a fallback candidate when one exists.
4. If a required param needs an ID/code from a companion tool (see
   `associated_tools`), call that tool first.
5. Call `ExecuteTool` with the exact `tool_url` and `params` built from
   `input_schema`.
6. Never invent a required value (URL, ID, token, code snippet, or other
   concrete input) that the user hasn't provided — ask the user instead.

## Reading the Result

`ExecuteTool`'s MCP result has an `isError` field — that is the reliable
success/failure signal, not a fixed field inside the payload:

- **`isError` absent/false** — the call succeeded. The content is the
  **raw response of the underlying third-party API**, in that API's own
  format (it may or may not contain something resembling `error_no`/status
  fields of its own — don't assume a single universal shape across tools).
- **`isError: true`** — the call failed. The error detail comes back
  wrapped as `<tool_output>...</tool_output>`, often followed by a
  `<platform_annotation>` with a suggestion (e.g. "revise your request
  parameters based on the upstream provider's error message"). Use that
  detail to correct `params` and retry, or fall back to another candidate
  from `RecommendTools` if the issue isn't fixable from user-provided input.

`GetAccountOverview` and `GetToolDetail`/`RecommendTools`/`ListTools` (the
AgentEarth-native lookups, as opposed to `ExecuteTool` passthrough results)
do use `error_no == 0` as their own success signal.

## Credentials

This connector authorizes over OAuth. On the first AgentEarth tool call,
WorkBuddy opens a browser page: signing in to AgentEarth is itself the
authorization — there is no Allow button to click and **no API key to
obtain, paste, or manage**. The page then says the authorization
succeeded, and the user closes it. Tell the user exactly that when they
ask how to connect.

WorkBuddy stores the resulting token and refreshes it on its own; this skill
never sees or handles it. Never ask the user to paste an API key, token, or
any credential in chat, and never mention the AgentEarth API Keys page as a
setup step.

If a call fails with an auth error, or the connector shows as disconnected or
unauthorized, tell the user to (re)connect AgentEarth from the WorkBuddy
Connector page — the same browser authorization page opens again.

## Incorrect Flow

- Calling `ExecuteTool` before `RecommendTools`/`GetToolDetail`.
- Modifying, re-encoding, or reconstructing `tool_url`.
- Inventing required params instead of asking the user.
- Treating `error_no == 0` as the success signal for `ExecuteTool` results —
  use `isError` instead.
- Making raw HTTP requests to AgentEarth endpoints yourself, or asking the
  user for an API key — this connector only ever talks to AgentEarth through
  the 5 MCP tools above, and it authenticates over OAuth, not with a key.
