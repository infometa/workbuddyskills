---
name: novai-studio
display_name: NovAI Studio 创作助手
display_name_en: NovAI Studio Creative Assistant
description: Use when the user asks to manage NovAI Studio canvases or assets, generate images, videos, or audio, run canvas nodes, or inspect generation tasks and points.
description_zh: 当用户需要管理 NovAI Studio 画布或素材、生成图片视频音频、运行画布节点、查询任务或积分时使用。
description_en: Manage NovAI Studio canvases and assets, generate media, run canvas nodes, and inspect tasks or points.
version: 1.0.0
author: NovAI
---

# NovAI Studio

通过 NovAI Studio MCP 管理用户自己的素材、画布和 AI 生成任务。所有数据访问、任务和积分操作均以当前 OAuth 授权账号为准。

## 开始工作

1. 首次使用或重新连接后，调用 `studio_get_current_account` 核对当前账号和权限。
2. 涉及生成时，调用 `studio_get_balance` 和 `studio_get_generation_catalog` 获取实时余额与能力配置。
3. 不要写死模型、画质、时长、积分价格或上游参数；始终以工具返回值为准。
4. 授权失效时，引导用户在 WorkBuddy 中重新连接，并等待浏览器授权流程自动完成。不要要求用户在对话中回复“已授权”，也不要索要账号密码或 MCP Key。

工具用途与权限见 @references/tool-catalog.md，标准调用流程见 @references/workflows.md，异常处理见 @references/errors.md。

## 付费操作

图片、视频、音频、一键替换、视频抽帧和视频处理都可能消费 Studio 积分。必须遵循：

1. 调用 `generation_estimate`；运行已有画布节点时改用 `canvas_estimate_node`。
2. 清楚展示 `estimated_points`、生成类型和关键参数。
3. 只有用户明确同意本次费用后，才把返回的 `confirmation_token` 传给正式生成工具。
4. 参数变化、令牌失效或用户未确认时重新预估，不能复用旧令牌。
5. 不得绕过预估，不得把一次确认扩展为后续多次生成授权。

## 异步任务

生成工具返回任务后，不要把“已提交”当成“已完成”：

1. 保存 `mcp_task_id`、业务任务 ID 和 `idempotency_key`。
2. 使用 `generation_get_task` 查询统一任务状态；需要原生详情时再使用对应的 `*_get_task`。
3. 图片或音频任务每 5 秒查询一次，最多等待 10 分钟；视频和视频处理任务每 8 秒查询一次，最多等待 30 分钟。
4. 状态为排队、处理中、归档中或结算中时继续等待，不重复提交生成。
5. 状态成功后返回结果素材、可访问地址、实际扣费和画布回填状态。
6. 状态失败或取消后返回公开错误码、可读原因和退款状态。仅在工具明确标记可重试且用户要求重试时，才重新预估并调用 `generation_retry_task`。
7. 达到等待上限时返回现有任务 ID 和当前状态；后续继续查询原任务，不能重新创建任务。

## 幂等与并发

- 每次新的写操作生成 8 到 128 字符的唯一 `idempotency_key`。
- 同一业务操作发生超时或网络重试时必须复用原 Key。
- 修改已有画布前调用 `canvas_get_project`，并使用最新 `revision` 作为 `base_revision`。
- 遇到 `CANVAS_REVISION_CONFLICT` 时重新读取画布，根据最新内容重新构造修改，禁止直接重放旧操作。

## 素材规则

- 先调用 `material_list`，优先复用用户已有素材。
- 公开 HTTPS 素材使用 `material_import_url` 归档到当前账号素材库。
- 本地文件不得编码为 base64 放入 MCP JSON。客户端能执行 multipart 上传时，按 `material_get_upload_instructions` 返回的端点上传；不能上传时，引导用户先在 NovAI Studio 素材库完成上传。
- 画布和生成工具只传当前账号的 `material_id`，不猜测 ID，不引用其他用户素材。

## 高风险操作

- 永久删除画布、恢复历史版本、取消任务和删除任务记录前，必须向用户说明影响并取得明确确认。
- 删除画布只能调用 `canvas_delete_project`，并传入 `confirm=true` 和唯一幂等键。
- 工具返回的权限、积分、任务、退款和素材归属结论是唯一事实来源，不根据对话猜测。

## 返回用户

最终说明应简洁包含：完成了什么、涉及的画布或任务 ID、最终状态、实际积分变化、结果素材或打开地址。失败时说明可执行的恢复动作，不展示内部堆栈、上游原始响应、令牌或签名参数。
