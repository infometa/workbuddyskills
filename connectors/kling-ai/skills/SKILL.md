---
name: kling-ai
description: Create and monitor Kling AI image and video generations through the OAuth-protected Kling MCP server. Use for text-to-image, text-to-video, image-to-image, image-to-video, reference uploads, multi-shot VIDEO 3.0 requests, credit checks, task status, and output retrieval.
description_zh: 通过官方、基于 OAuth 的可灵 MCP 服务（https://klingai.com/mcp）创建并监控可灵 AI 的图片与视频生成：文生图/图生图、文生视频/图生视频、参考图上传、额度与任务状态查询。
version: 1.0.0
author: KLING AI Pte Ltd
license: MIT
category: 图像与视频 / 创意生成
source: kling-ai
---

# Kling AI

Create one well-specified Kling generation, submit it once, and return the
completed media when the task finishes.

## Operating contract

- The `kling-ai` MCP server points at `https://klingai.com/mcp` with OAuth.
  Never ask the user for an API key in chat. If authorization is requested,
  complete it through the host's MCP/plugin connection flow.
- Never expose bearer headers, cookies, credentials, private account fields,
  or signed output URLs in logs.
- Treat image and video generation as credit-consuming write actions.
- Before the billable generation call, show one concise submission summary
  and obtain explicit confirmation. Skip a second confirmation only when the
  user's current message explicitly says to submit immediately or not ask
  again and already contains the final billable settings.
- Submit at most once for each approved intent. Do not retry a failed
  generation automatically.
- Discover live tools and schemas at runtime; provider schemas override
  examples in this skill.
- After a generation is accepted, poll `query_tasks` automatically using the
  returned `generationId` and `taskTraceId` until a terminal state is reached.
  Use delayed adaptive polling: do not query image tasks during the first
  minute; make the first query at 60 seconds, then query every 10 seconds
  until the 5-minute timeout. Do not query video tasks during the first 2
  minutes; make the first query at 120 seconds, then query every 15 seconds
  until the 10-minute timeout. On timeout, return the IDs and ask the user to
  request another status check. Never submit again.

Read [references/tool-workflows.md](references/tool-workflows.md) before a
generation call. Read [references/prompt-examples.md](references/prompt-examples.md)
only when the user wants help writing a prompt or asks how to use this
extension. Read [references/troubleshooting.md](references/troubleshooting.md)
only after an authorization, schema, upload, or status-check failure.

## Interaction flow

1. Identify the requested workflow: text-to-image, image-to-image,
   text-to-video, image-to-video, status check, or credit check.
2. Ask only for missing creative requirements that materially change the
   result: prompt, reference media, duration, aspect ratio, or single-shot
   versus multi-shot intent.
3. State the final billable settings in one compact line before submission.
   Avoid dumping tool schemas or implementation details into the conversation.
4. For local or attached media, upload it with `file_upload` before calling a
   generation tool. Reuse one UUID v7 `taskTraceId` for upload and generation.
5. Select a model from the live provider schema. When these identifiers are
   present, prefer:
   - `kling-video-v3_0_turbo` for one reference image and one continuous shot.
   - `kling-video-v3_0` for explicit multi-shot storytelling.
   - `kling-video-v3_0_omni` for multiple references or element consistency.
6. Call the selected generation tool once.
7. When the tool returns a `generationId`, capture it together with the
   `taskTraceId`. Delay status checks until the expected completion window:
   first query at 60 seconds for images, then every 10 seconds; first query at
   120 seconds for videos, then every 15 seconds. Stop at a terminal state or
   the corresponding timeout (5 minutes for images, 10 minutes for videos).

8. When the task succeeds, return the output URLs in the host's normal media
   response so the generated image or video is displayed automatically. When
   it fails, report the provider error and preserve the IDs. On timeout, return
   the IDs without creating another task.

## Defaults

Use these only when the user does not specify alternatives and the live schema
supports them:

- Video resolution: `720p`
- Video duration: `5` seconds
- Text-to-video aspect ratio: `16:9`
- Image-to-video aspect ratio: derive from the first frame; do not pass one
  unless the schema requires it

For a low-cost diagnostic explicitly approved by the user, prefer the
shortest live duration and `720p`.

## Response style

Before submission, use a compact summary such as:

> 准备生成：图生视频，5 秒，720p，单镜头。提交会消耗可灵 credits。

End the summary with an unambiguous confirmation request. Do not hide the
credit-consuming action inside a long creative explanation.

After submission, report only the useful handoff:

- generation accepted
- selected model and user-facing settings
- note that closing the host does not cancel the already-submitted Kling task

For a direct status request, call `query_tasks` once and report the current
state. If it is still running, resume the corresponding delayed polling policy
until it reaches a terminal state or the corresponding timeout.

## Failure behavior

- Authorization failure: direct the user to the host's MCP/plugin connection
  UI or command, then retry the same tool call after authorization.
- Invalid media input: confirm `file_upload` succeeded and pass only the
  returned Kling URL to the generation tool.
- Invalid model or argument: refresh the live schema and revise only the
  unsupported field.
- Provider task failure: show the provider message in plain language and
  preserve the `generationId`; do not resubmit.
- Submission response lost or timed out: treat billing state as unknown.
  Query existing tasks by the available trace/task identifiers before
  considering another submission; never blind-retry.
- Status-check failure: show the exact message and the `generationId`; retry
  the same status check with the existing IDs, never create a new generation.
