# 视频剪辑操作指南

在调用 `video_editor` 前阅读本文件。它面向出海匠 SaaS 剪辑项目，处理已有素材的时间线剪辑、字幕、旁白、拼接和渲染。

## 两条路径

### 可编辑项目

适合需要多轮修改、字幕/旁白、转场或最终导出的任务：

1. `capabilities`：取得 `contract_revision`、当前支持的 operation/action、画幅和参数范围。
2. 准备稳定素材坐标：视频需要 `video_os_bucket + video_os_key + duration_s`。
   - 用户上传自己的视频：先确认 Agent 能读取附件对应的本地文件；只有公网 URL 时先下载为本地文件。然后走 `upload_file(file_name, accelerated=true)` → 将真实文件字节 PUT 到 `url`，MP4 使用 `Content-Type: video/mp4` → 用 ranged GET/HEAD 校验远端总字节等于本地文件 → 将 `os_bucket/os_key` 映射为 `video_os_bucket/video_os_key`。不要省略 curl `--data-binary @file` 中的 `@`。
   - 复用 SaaS 素材库：`assets(action="list", library_type="resource", content_type="video")`，取 `bucket_name/os_key`。
   - 不要把临时下载 URL 当稳定坐标；上传不会自动出现在 assets 列表里，查不到不代表上传失败。
3. `create_project`：保存 `project_id`、`version`、`edit_version`。当前 tool 没有删除 action，创建前确认确实需要持久项目，并给标题标明用途。
4. `context`：每次写入前读取最新项目、轨道、片段和素材 ID。ID 不靠名称猜，时间统一用整数微秒。
5. `preview`：提交一个业务意图内的有序 operations，检查：
   - `can_apply=true`
   - `warnings` 和逐操作 `operation_results`
   - 服务端 `normalized_operations`
   - `estimated_charge`
   - `expires_at`
6. `apply`：在预演过期前，原样回传同一编辑意图并加入 `preview_id`；同一次重试复用 `client_mutation_id`，新意图生成新 ID。
7. 再次 `context` 验证结果并取得新版本。
8. `render`：预览用 `profile={"quality":"draft","max_width":320}`；最终交付再用 production。随后 `renders` 轮询到 `ready` 或 `failed`，需要下载时才传 `presign=true`。

### 直接合成

只需按顺序拼接现有片段、不需要可编辑时间线时使用：

1. `compose`：每段从 `video_asset_id` 或 `video_os_bucket + video_os_key` 二选一，最多 100 段；`duration_us` 是微秒。
2. `composition_status`：轮询 `assembling → ready/failed`；成片可用后再以 `presign=true` 获取临时地址。

## 并发与幂等

- `contract_revision` 来自本次 `capabilities`，不得硬编码。
- `version` / `edit_version` 来自最近一次 `context` 或写操作回执。任何成功写入、异步动作完成、网页端编辑都可能推进版本。
- 409/422 版本或前置条件失败：重新读取 context、重新构造意图；不要循环重发旧请求。
- 同一请求的网络重试复用幂等 ID；改变素材、操作或参数后必须生成新 ID。
- 一次 preview/apply 只承载一个用户意图，但相关操作应批量提交，避免操作间版本竞争。

## 异步动作

`submit_action` 支持：

- `auto_captions`：可传 `language_code`、`clear_existing_subtitles`。
- `detach_video_audio`：传 context 中真实的 `video_segment_id`；无音轨素材可能直接被拒绝。
- `generate_voiceover`：`source.type` 必须与 text/subtitle/scene/voiceover 负载匹配；音色和语言从 capabilities 获取。

用 `action_status(project_id, job_id)` 轮询。提交成功不等于处理成功；`failed` 时交付 `error_code/error_message`，先检查源素材是否有音频/语音，再决定是否重试。
