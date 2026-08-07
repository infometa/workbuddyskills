---
name: picset-commerce-images
description: WorkBuddy 用户需要通过 Picset AI MCP 连接器生成电商主图、详情图或 Amazon A+ 图片时使用。
---

# Picset AI 电商图片 Skill

## 目标

引导 WorkBuddy 用户完成需求澄清、服务端提示词预估、明确确认、异步生图和结果反馈。

服务端是提示词、价格、鉴权、任务归属和生成状态的唯一可信来源。Skill 只负责对话澄清、参数收集、确认门槛、轮询和结果展示；服务端负责 SK 鉴权、两段提示词生成、计费校验、幂等提交和任务聚合。

## 回复语言

除非用户明确要求其他语言，所有面向用户的回复、确认提示、错误解释、积分预估说明和任务状态反馈均使用简体中文。

工具名、参数名、接口字段和服务端返回的结构化字段可以保留英文；但解释这些字段时必须使用简体中文。

## 配置

WorkBuddy MCP 模式连接 `mcp.json` 中声明的远程 streamable HTTP endpoint，并通过 `token-schema.json` 中的 `PICSET_AGENT_SK` 字段注入用户 SK。

- SK 只能通过 `Authorization: Bearer <SK>` 发送。
- 不要要求用户把完整 SK 粘贴到聊天中。
- 不要打印或记录完整 SK、确认 token、完整提示词或用户隐私需求。
- 如果 SK 缺失，提示用户在 Picset AI 用户中心创建 Agent SK，并填写到 WorkBuddy 连接器 token 表单。

## 用户首次授权流程

当 WorkBuddy 首次安装或启用连接器时：

1. WorkBuddy 读取 `connector-meta.json`，识别这是 `auth_mode: "token"` 的 MCP 连接器。
2. WorkBuddy 读取 `token-schema.json`，弹出 `Picset AI Secret Key` 密码输入框。
3. 用户打开 Picset AI 用户中心，进入 Agent SK 管理，创建一把新的 SK。
4. Picset AI 只展示一次 SK 明文，用户把它粘贴到 WorkBuddy 的 token 表单中。
5. 用户保存后，WorkBuddy 将 `${PICSET_AGENT_SK}` 替换到 `mcp.json` 的请求头：
   `Authorization: Bearer <SK>`。
6. MCP 请求到达 Picset AI 后，服务端校验 SK 状态，并把后续积分、任务和日志归属到该 SK 绑定的用户。

不要索要包含完整 SK 的截图。排查问题时，只能让用户提供可见前缀或 WorkBuddy 错误文本。

## 可用工具

只使用以下 MCP tools：

- `get_reference_image_upload_token`
- `register_reference_image`
- `estimate_commerce_image_generation`
- `generate_commerce_images`
- `get_generation_task_status`

这些工具对应服务端 Agent 操作：

- `POST /upload-token`
- `POST /register-reference`
- `POST /estimate`
- `POST /generate`
- `GET /task-status?task_id=...`

不要调用 SSE endpoint。不要自行构造生图提示词或积分价格。

## 必需输入

调用 estimate 前，先收集：

- `image_type`：`main`、`detail` 或 `aplus`。
- `image_count`：用户要生成的张数。
- `requirements`：商品事实、卖点、视觉方向和文字要求。
- `reference_image_urls`：可选，已经被 Picset AI 接受的参考图 URL。

如果用户在 WorkBuddy 中提供本地参考图：

1. 调用 `get_reference_image_upload_token` 获取受限 OSS 上传凭证。
2. 将图片上传到返回的 `pathPrefix` 范围内。
3. 调用 `register_reference_image`，传入上传后的相对 `oss_path`，可附带 `file_type` 和 `file_size`。
4. 使用返回的 `reference_image_urls` 继续 estimate 和 generate。

不要编造商品事实。如果图片类型、数量或核心商品需求不清楚，先向用户追问。

## 流程

### 1. 预估

调用 `estimate_commerce_image_generation`，传入原始输入。向用户展示：

- 图片类型和张数；
- 服务端生成的提示词预览；
- `estimated_credits` 预计消耗积分。

预估不会开始生图，也不会扣积分。展示预估后，必须等待用户明确确认。

### 2. 确认规则

用户没有明确表达“确认”“提交”“开始生成”等同等含义时，不得调用 generate。

如果用户在 estimate 后修改图片类型、张数、需求或参考图：

1. 丢弃旧确认上下文；
2. 重新调用 estimate；
3. 展示新的提示词预览和预计积分；
4. 再次请求确认。

不要复用已变更输入对应的确认上下文。

### 3. 正式生成

用户确认后：

1. 生成一个稳定的 UUID 作为 `request_id`。
2. 调用 `generate_commerce_images`，传入未变化的原始输入、`confirmed=true` 和 `request_id`。
3. 同一次 generate 请求的所有重试必须复用同一个 `request_id`。
4. 保存返回的 `task_id`，用于后续轮询。

不要把客户端生成的提示词或积分价格发给 generate。不要因为 HTTP 超时就换新的 `request_id`。

### 4. 状态查询

使用有上限的退避策略轮询 `get_generation_task_status`。

- `processing`：告诉用户仍在生成，并在本地等待预算内继续轮询。
- `success`：展示全部图片。
- `partial_success`：展示成功图片，并说明失败数量。
- `failed`：展示服务端返回的用户可读失败原因。

如果本地轮询预算耗尽，不要报告生成失败。告诉用户任务仍在处理中，保留 `task_id`，之后可继续查询。

## 错误处理

- `401`：提示用户 SK 缺失、无效、已禁用或已删除。
- `REESTIMATE_REQUIRED`：重新 estimate 并再次请求确认，不要静默生成。
- 余额不足：展示服务端返回的所需和可用积分信息后停止。
- 限流：提示用户稍后重试；如果服务端说明确认上下文仍有效，则保留当前上下文。
- generate 网络错误：只允许用同一个 `request_id` 重试。
- 未知服务端错误：展示简短错误信息，并附带 `request_id` 或 `task_id`，不得暴露密钥。

## 本地日志

远程 MCP 调用由 Picset AI 后端记录脱敏请求元数据。日志只记录排查所需字段：

- timestamp、endpoint、HTTP status、duration；
- request_id、task_id；
- image type/count、是否带参考图；
- estimated/charged credits；
- SK 前缀、错误码和脱敏 message。

不要记录完整 SK、确认 token、完整提示词、用户隐私文本或完整敏感图片 URL。

## 硬性停止条件

- 用户未明确确认：不得 generate。
- 输入在 estimate 后改变：必须重新 estimate。
- generate 重试：必须复用 `request_id`。
- token 无效、过期或价格变化：必须重新 estimate。
- 本地轮询超时：不得宣告服务端失败。
- 服务端返回部分成功：不得隐藏失败项。
