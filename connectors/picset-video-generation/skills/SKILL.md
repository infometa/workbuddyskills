---
name: picset-video-generation
description: WorkBuddy 用户需要通过 Picset AI MCP 连接器生成电商短视频时使用。
---

# Picset AI 视频生成 Skill

## 目标

引导 WorkBuddy 用户完成视频需求澄清、积分预估、明确确认、异步生成和结果反馈。

服务端是模型、价格、鉴权、任务归属和生成状态的唯一可信来源。

## 回复语言

除非用户明确要求其他语言，所有面向用户的回复、确认提示、错误解释、积分预估说明和任务状态反馈均使用简体中文。

工具名、参数名、接口字段和服务端返回的结构化字段可以保留英文；但解释这些字段时必须使用简体中文。

## 配置

WorkBuddy MCP 模式连接 `mcp.json` 中声明的远程 streamable HTTP endpoint，并通过 `token-schema.json` 中的 `PICSET_AGENT_SK` 字段注入用户 SK。

- SK 只能通过 `Authorization: Bearer <SK>` 发送。
- 不要要求用户把完整 SK 粘贴到聊天中。
- 不要打印或记录完整 SK、内部 token、完整 prompt 或敏感素材 URL。
- 如果 SK 缺失，提示用户在 Picset AI 用户中心创建 Agent SK，并填写到 WorkBuddy 连接器 token 表单。

## 可用工具

只使用以下 MCP tools：

- `get_reference_image_upload_token`
- `register_reference_image`
- `estimate_video_generation`
- `generate_video`
- `get_video_task_status`

## 模型

当前 MVP 只允许以下模型：

- `Seedance 2.0`：默认标准模型。
- `Seedance 2.0 Fast`：快速模型。
- `Seedance 2.0 Mini`：轻量模型。

如果用户没有指定模型，使用 `Seedance 2.0`。

## 必需输入

调用 estimate 前，先收集：

- `prompt`：视频内容、商品卖点、镜头和风格要求。
- `model`：可选，`Seedance 2.0`、`Seedance 2.0 Fast` 或 `Seedance 2.0 Mini`。
- `duration_sec`：可选，视频时长。必须传 JSON 数字，例如 `4`，不得传字符串 `"4"`。
- `resolution`：可选，默认由服务端处理。
- `aspect_ratio`：可选，默认由服务端处理。
- `product_image_refs`：必填，必须是字符串数组，例如 `["https://cdn.picsetai.cn/temp/user/agent-uploads/ref.jpg"]`，不得传 `{ "item": "url" }` 对象。

不要编造商品事实。如果视频主体、用途或核心卖点不清楚，先向用户追问。
如果没有商品参考图，不得调用 `estimate_video_generation` 或 `generate_video`，先引导用户上传商品图。
如果用户提供的是 WorkBuddy 附件、本地剪贴板图片或 `/Users/...`、`file://...`、Windows 盘符路径，必须先执行商品图上传流程。不得把本地文件路径填入 `product_image_refs`。

## 工具参数格式

调用 `estimate_video_generation` 和 `generate_video` 时，必须严格使用以下结构：

```json
{
  "prompt": "视频内容、商品卖点、镜头和风格要求",
  "model": "Seedance 2.0",
  "duration_sec": 4,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "product_image_refs": [
    "https://cdn.picsetai.cn/temp/user-id/agent-uploads/ref.jpg"
  ]
}
```

`generate_video` 还必须额外传：

```json
{
  "confirmed": true,
  "request_id": "稳定 UUID"
}
```

禁止以下错误格式：

- `"duration_sec": "4"`：错误，`duration_sec` 必须是数字。
- `"product_image_refs": { "item": "https://..." }`：错误，`product_image_refs` 必须是数组。
- `"product_image_refs": "https://..."`：错误，单张图也必须写成数组。

## 流程

### 0. 商品图上传

用户提供本地商品图后：

1. 调用 `get_reference_image_upload_token` 获取 OSS 上传凭证、`pathPrefix` 和 `cdnBaseUrl`。
2. 将图片上传到 `pathPrefix` 下。
3. 调用 `register_reference_image` 登记上传后的 `oss_path`。
4. 使用返回的 `reference_image_urls` 作为后续 `product_image_refs`。

登记后的 Agent 图片由 Picset 服务端标记为已通过审核。不要跳过登记步骤。
任一上传、登记或预估步骤返回 `isError=true`、`error` 字段或失败状态时，立即停止当前流程，向用户解释错误，不得继续调用 `generate_video`。

### 1. 预估

调用 `estimate_video_generation`，传入原始输入和 `product_image_refs`。向用户展示：

- 模型、时长、比例和分辨率；
- `estimated_credits` 预计消耗积分；
- 用户需要确认的生成参数。

预估不会开始生成，也不会扣积分。展示预估后，必须等待用户明确确认。

### 2. 确认规则

用户没有明确表达“确认”“提交”“开始生成”等同等含义时，不得调用 generate。

如果用户在 estimate 后修改 prompt、模型、时长、比例、分辨率或参考素材，必须重新 estimate 并再次请求确认。

### 3. 正式生成

用户确认后：

1. 生成一个稳定的 UUID 作为 `request_id`。
2. 调用 `generate_video`，传入未变化的原始输入、`confirmed=true` 和 `request_id`。
3. 同一次 generate 请求的所有重试必须复用同一个 `request_id`。
4. 保存返回的 `task_id`，用于后续轮询。

### 4. 状态查询

使用有上限的退避策略轮询 `get_video_task_status`。

- `processing`：告诉用户仍在生成，并在本地等待预算内继续轮询。
- `success`：展示视频结果。
- `failed`：展示服务端返回的用户可读失败原因。

如果本地轮询预算耗尽，不要报告生成失败。告诉用户任务仍在处理中，保留 `task_id`，之后可继续查询。

## 错误处理

- `401`：提示用户 SK 缺失、无效、已禁用或已删除。
- 余额不足：展示服务端返回的所需和可用积分信息后停止。
- 限流：提示用户稍后重试。
- generate 网络错误：只允许用同一个 `request_id` 重试。
- 未知服务端错误：展示简短错误信息，并附带 `request_id` 或 `task_id`，不得暴露密钥。

## 硬性停止条件

- 用户未明确确认：不得 generate。
- 未获取到至少 1 张已登记商品参考图：不得 estimate 或 generate。
- 遇到本地文件路径：必须先上传和登记，不得直接填入 `product_image_refs`。
- 上传、登记或预估失败：必须停止，不得继续 generate。
- 输入在 estimate 后改变：必须重新 estimate。
- generate 重试：必须复用 `request_id`。
- 本地轮询超时：不得宣告服务端失败。
