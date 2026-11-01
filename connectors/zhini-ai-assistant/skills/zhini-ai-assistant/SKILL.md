---
name: "zhini-ai-assistant"
description: "使用知你客服查询客户资料与聊天记录、分析会话并识别销售机会；支持用户确认后批量打开选定客户对话、发送文本或图片消息，并查询发送进度和历史群发任务。"
---

# 知你AI助手

通过知你客服 MCP 服务，将客户资料、会话及聊天记录连接到 Codex、WorkBuddy 等 AI 工具，并按用户确认执行批量打开对话和消息发送任务。

## Connection

- 官网：`https://ai.zhinikefu.com/`
- MCP endpoint：`https://mcp.h5bqb.top/mcp`
- 认证方式：MCP 原生 OAuth 2.1（含动态客户端注册与 PKCE）——首次访问受保护资源时由 WorkBuddy 打开浏览器完成知你账号授权，无需配置 API Key；授权可随时在官网吊销。
- 采用 MCP 原生 OAuth 是有意设计：`connector-meta.json` 不设置 `auth_mode`、`mcp.json` 不写静态 `headers`，认证由服务端 OAuth 挑战（`WWW-Authenticate` 与 `/.well-known/oauth-protected-resource`）驱动。

## 授权引导（连接器未配置或未授权时）

用户请求查询数据但连接器未配置或未授权时，先完成连接器自举，再输出下方引导，等用户回复「已连接」后重试查询：

**请先完成授权，否则无法查询数据。**

我先把知你AI助手连接器写入本机配置（`~/.workbuddy/mcp.json` 的 `mcpServers` 中合并以下条目，保留既有连接器）：

```json
"知你AI助手": {
  "type": "streamableHttp",
  "url": "https://mcp.h5bqb.top/mcp",
  "timeout": 30000
}
```

连接器已加到本机，按下面 3 步操作：

1. 打开 **连接器管理**，找到 **「知你AI助手」**，点 **「信任」**
2. 浏览器会打开知你登录页，**登录知你账号**（手机号 + 密码），页面显示「授权已完成」后自动返回 WorkBuddy
3. 完成后回我 **「已连接」**，我立即为你查询

![连接器管理中的「知你AI助手」连接器（示例图）](https://mcp.h5bqb.top/dashboard/assets/connector-trust-guide.png)

引导话术面向用户，不要省略步骤；授权窗口为知你登录页（账号密码登录，无需扫码）；授权一次长期有效，令牌过期或吊销时会重新弹出登录页。

## Channel coverage

渠道统一通过知你客服接入和查询。

## 用户可以这样问

- 查看今天知你客服中正在排队、长时间未回复的客户会话。
- 查找最近 30 天咨询过价格但还没有成交的客户。
- 汇总客户本周最常咨询的问题及负面反馈。
- 筛选咨询过商品、订单或售后的高意向客户，并查看完整聊天记录。
- 分析今天的客户会话，找出购买意向、投诉风险和需要重点跟进的客户。
- 查找某位客户在知你客服接入渠道中的历史沟通记录，整理需求变化与跟进脉络。
- 把这些已选客户的对话打开到我的对话。
- 向已确认的客户批量发送跟进文本和图片，并查看发送进度。
- 查询最近的历史群发任务。

## Capability routing

根据用户意图选择对应流程；一个请求涉及多项能力时，可在保持证据链清晰的前提下组合调用。

### 当前会话分诊

适用于当前队列、等待接待、我的会话、同事会话或 AI 会话查询。

1. 需要区分“我的会话”时，先调用 `zhini_get_current_kefu` 获取 `kfid`。
2. 调用 `zhini_list_active_sessions` 获取实时队列，不把当前快照当作历史统计。
3. 选定会话后，用 `sid` 调用 `zhini_fetch_messages`，用 `uid` 调用 `zhini_get_customer_profile`。

### 客户查询与画像

适用于按姓名、手机号、微信号、渠道、客服、标签、时间或已知 `uid` 定位客户。

1. 客户名、渠道名、客服名或标签名先通过 `zhini_list_channels`、`zhini_list_kefu` 或 `zhini_search_tags` 解析为稳定 ID。
2. 将明确的结构化条件交给 `zhini_search_customers`，避免空条件查询。
3. 已知 `uid` 时直接调用 `zhini_get_customer_profile`；需要聊天内容时再调用 `zhini_fetch_messages`。
4. 多个候选时保留 `uid` 供核对，不把推断当成客户身份事实。

### 历史会话研判

适用于历史咨询、投诉、订单、退款、问题处理、关键词命中或客户前情复盘。

1. 按客户、消息关键词或 `msg_stime` 调用 `zhini_search_sessions`。
2. 关键词只用于召回候选；调用 `zhini_fetch_messages` 读取上下文后再总结。
3. 需要更多结果时按 `page` 翻页；输出会话 ID、时间范围和关键证据。
4. 已知 `uid` 时可调用 `zhini_get_customer_profile` 补充资料。

### 客户分群

适用于按标签、渠道、客服、联系人类型、性别和时间条件构建客户或会话分群。

1. 先将用户明确提到的标签、渠道和客服名称解析为稳定 ID。
2. 结构化条件使用 `zhini_search_customers`；必须按消息内容判断时使用 `zhini_search_sessions` 和 `zhini_fetch_messages`。
3. 多个相似标签或候选需要保留核对点。
4. 分页查询并记录实际条件、页码和返回数量，避免把单页结果当成完整分群。

### API Key 用量

适用于查询当前 API Key 所属账号的总额度、账号已使用量和账号剩余额度，以及当前请求 API Key 的实时已使用量。

1. 调用 `zhini_get_apikey_usage`。
2. 分别汇总账号总配额、账号已使用量、账号剩余额度和当前请求 API Key 实时已使用量；仅校验账号级 `total = used + remaining` 是否一致。
3. 仅展示额度摘要，不输出完整 API Key 或内部鉴权细节。

`zhini_get_apikey_usage` 返回 `total`、`used`、`remaining`（当前 API Key 所属账号整体配额）和 `current_api_key_used`（当前请求 API Key 实时已使用量）。

### 客户触达与消息发送

适用于用户确认后批量打开客户对话、发送文本或图片消息，并查询发送进度和历史群发任务。

**批量打开对话**

1. 如果用户只提供姓名、手机号、微信号、标签或渠道等条件，先查询并展示候选客户；不要直接把搜索结果、当前队列或整个分群作为操作名单。
2. 展示用户选定的客户及对应 UID，取得明确确认后调用 `zhini_open_sessions`，每次最多 20 个 UID。
3. 根据工具结果汇报打开情况。该操作不会转接已由其他客服接待的客户，也不会发送消息。

**批量发送文本/图片消息**

1. 收件客户应来自用户明确选定或查询工具已核对的结果；不要把未确认的搜索结果或整批分群直接作为收件人。
2. 确认目标客户 UID、任务标题和最终消息内容。每次最多 100 个 UID，每个任务最多 2 条按顺序发送的文本或图片消息。
3. 有图片时先调用 `zhini_upload_image_for_message_sending` 上传，并将返回的 CDN `url` 用作图片消息内容。仅支持 PNG、JPEG、GIF；Base64 解码后单张不超过 10 MiB，不接受远程图片 URL。
4. 首次调用 `zhini_create_message_sending_task` 只准备任务并返回短时 `confirmation_token`，不会创建或发送任务。向用户展示收件客户、标题和最终内容，等待明确确认。
5. 用户确认后，以完全相同的 UID、标题和消息内容再次调用，并附上 `confirmation_token` 与 `user_confirmed=true`。创建成功后保存 `task_id`；任务创建成功不代表所有消息都已发送。
6. 使用 `zhini_get_message_sending_task_status` 查询进度和逐客户结果；按标题或发送时间查询历史群发任务时，使用 `zhini_list_message_sending_tasks`。
7. 仅当用户明确要求删除某个任务时，先查询并核对任务标题、发送时间和状态，再调用 `zhini_delete_message_sending_task`。删除任务不会撤回已发送消息，删除前先保存用户需要的结果明细。

## Available tools

- `zhini_get_current_kefu`
- `zhini_list_active_sessions`
- `zhini_search_customers`
- `zhini_get_customer_profile`
- `zhini_search_sessions`
- `zhini_fetch_messages`
- `zhini_search_tags`
- `zhini_list_channels`
- `zhini_list_kefu`
- `zhini_get_apikey_usage`
- `zhini_open_sessions`
- `zhini_upload_image_for_message_sending`
- `zhini_create_message_sending_task`
- `zhini_get_message_sending_task_status`
- `zhini_list_message_sending_tasks`
- `zhini_delete_message_sending_task`

## Boundary

仅访问当前 API Key 可访问的数据；批量打开对话和发送消息严格按上述用户确认流程执行。保持结果可核验，不虚构工具、客户身份、消息证据或筛选结果；不修改客户资料、不批量修改资料、不执行数据导出。
