---
name: wavenote-audio-skill
description: WaveNote 音频技能 - 查询录音、转写和总结，并在用户确认后发起转写任务
version: "1.0.0"
author: "WaveNote"
---

# WaveNote Audio Skill

通过 WaveNote Audio MCP 查询当前授权用户的录音、转写与总结，并为指定录音发起转写任务。

## 使用原则

- 所有数据和操作均属于当前完成 OAuth 授权的 WaveNote 用户。
- 用户没有提供音频 ID 时，先调用 `list_audio` 查找目标音频，不要猜测 ID。
- 查询音频列表、转写和总结需要 `audio.read` 权限；发起转写需要 `audio.write` 权限。
- 发起转写会消耗用户的可用转写时长。执行前必须向用户说明这一影响，并取得对本次操作的明确二次确认。
- `start_audio_transcription` 不得自动调用、批量调用或在超时和结果不明确时自动重试。
- 工具返回的 `status` 是 WaveNote 内部音频处理状态。在没有明确状态映射时，不要自行猜测状态含义。

## 推荐调用流程

1. 用户未指定音频 ID 时，调用 `list_audio` 获取候选音频。
2. 根据用户需求调用 `get_audio_transcription` 或 `get_audio_summary`。
3. 用户要求发起或重新发起转写时，先明确告知会消耗可用转写时长，并询问是否继续。
4. 只有用户作出明确肯定答复后，才调用 `start_audio_transcription`，并将 `user_confirmed` 设置为 `true`。
5. 用户尚未确认、拒绝确认或意思不明确时，不得提交任务；如需调用工具确认状态，将 `user_confirmed` 设置为 `false`。

## 可用工具

### list_audio - 获取音频列表

分页获取当前授权用户有权访问的 WaveNote 音频列表，默认按音频 ID 倒序返回。

**所需权限**：`audio.read`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `page` | integer | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | integer | 否 | 每页数量，范围 10～50，默认 20 |

**返回值**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | integer | 符合条件的音频总数 |
| `page` | integer | 当前页码 |
| `page_size` | integer | 当前每页数量 |
| `items` | array | 当前页音频列表 |
| `items[].id` | string | 音频 ID，调用其他工具时使用 |
| `items[].title` | string | 音频标题 |
| `items[].source` | integer | 音频来源类型 |
| `items[].duration` | integer | 音频时长，单位为秒 |
| `items[].status` | integer | 音频处理状态 |
| `items[].created_at` | integer | 创建时间，Unix 时间戳 |
| `items[].updated_at` | integer | 更新时间，Unix 时间戳 |

**使用示例**：

- “查看我最近的录音”：调用 `list_audio`，使用默认分页参数。
- “再看下一页”：在前一次页码基础上加 1，并保持相同的 `page_size`。

### get_audio_transcription - 获取音频转写

根据音频 ID 获取当前授权用户该音频的转写结果。

**所需权限**：`audio.read`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `audio_id` | string | 是 | 正整数形式的音频 ID，可先通过 `list_audio` 获取 |

**返回值**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `audio_id` | string | 音频 ID |
| `title` | string | 音频标题 |
| `status` | integer | 音频处理状态 |
| `items` | array | 按时间顺序排列的转写片段 |
| `items[].id` | string | 转写片段 ID |
| `items[].lan` | string | 片段语言 |
| `items[].speaker` | string | 说话人名称或标识 |
| `items[].content` | string | 转写文本 |
| `items[].start_sec` | integer | 片段开始时间，单位为秒 |
| `items[].end_sec` | integer | 片段结束时间，单位为秒 |

### get_audio_summary - 获取音频总结

根据音频 ID 获取当前授权用户该音频的总结结果。

**所需权限**：`audio.read`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `audio_id` | string | 是 | 正整数形式的音频 ID，可先通过 `list_audio` 获取 |

**返回值**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `audio_id` | string | 音频 ID |
| `title` | string | 音频标题 |
| `status` | integer | 音频处理状态 |
| `summary` | object | 音频总结结果 |
| `summary.id` | string | 总结 ID |
| `summary.lan` | string | 总结语言 |
| `summary.title` | string | 总结标题 |
| `summary.keywords` | string[] | 总结关键词 |
| `summary.content.content` | string | 总结正文 |
| `summary.tpl_id` | string | 生成总结所使用的模板 ID |
| `summary.tpl_ref_data` | object | 模板引用数据 |

### start_audio_transcription - 发起音频转写

为当前授权用户的指定音频发起转写任务，并使用默认模板生成总结。

该操作会消耗用户的可用转写时长。即使用户最初已经提出转写要求，也必须再次说明消耗并获得明确确认。不得把用户最初的请求自行视为二次确认。

**所需权限**：`audio.write`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `audio_id` | string | 是 | 要发起转写的音频 ID |
| `user_confirmed` | boolean | 是 | 仅当用户已明确二次确认本次转写会消耗可用时长时传 `true`；否则传 `false` |

**返回值**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `audio_id` | string | 申请发起转写任务的音频 ID |
| `accepted` | boolean | 转写请求是否已被接受；`false` 表示未提交 |
| `message` | string | 转写请求的处理结果或二次确认提示 |

**正确交互示例**：

1. 用户：“帮我重新转写录音 2091。”
2. AI：“重新转写会消耗你的可用转写时长。是否确认继续转写录音 2091？”
3. 用户：“确认继续。”
4. 调用 `start_audio_transcription`：`audio_id="2091"`，`user_confirmed=true`。

如果用户没有在第 3 步明确确认，不得执行第 4 步。

## 认证与权限

- 首次连接时，WorkBuddy 会通过浏览器打开 WaveNote OAuth 授权页面。
- 用户应根据需要授予“读取录音、转写及总结”和“发起录音转写”权限。
- Access Token 失效但 Refresh Token 有效时，客户端会自动刷新。
- 如果工具提示缺少 `audio.read` 或 `audio.write` 权限，应提示用户在 WorkBuddy 中重新连接 WaveNote 音频连接器并完成授权。
- 如果登录状态或 Refresh Token 已失效，应提示用户重新授权，不要反复调用工具。

## 错误和边界处理

- `audio_id` 必须是正整数形式的字符串；不知道 ID 时先调用 `list_audio`。
- `page` 从 1 开始，`page_size` 必须在 10～50 之间。
- 转写或总结尚未生成时，应如实告知用户稍后再查询，不要编造内容。
- 发起转写返回 `accepted=false` 时，按照 `message` 提示用户，不得声称任务已经提交。
- 发起转写请求超时或结果不明确时，不得自动重试，应告知用户检查音频状态后再决定是否重新操作。

## English Usage Guide

- Use `list_audio` to find a recording ID when the user has not provided one.
- Use `get_audio_transcription` and `get_audio_summary` only for data owned by the authenticated WaveNote user.
- Starting transcription consumes the user's available transcription time. Explain this consequence and obtain a separate, explicit confirmation before calling `start_audio_transcription`.
- Set `user_confirmed=true` only after that confirmation. Never infer confirmation or automatically retry this non-idempotent operation.
- Read operations require `audio.read`; starting transcription requires `audio.write`.
