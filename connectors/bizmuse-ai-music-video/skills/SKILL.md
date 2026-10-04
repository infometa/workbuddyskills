---
name: ai-music-video-generation
description: Create a BizMuse AI music video from audio, reference images, and creative direction. Use when the user asks to create, make, or generate an AI music video.
description_zh: 根据歌曲、参考图片和创作方向生成完整的 AI 音乐视频。
description_en: Create an AI music video from audio, reference images, and creative direction.
version: 0.3.0
author: BizMuse AI
---

# BizMuse AI Music Video Generator

Use the BizMuse MCP tools to create one music video from one audio asset and one to seven reference
images for an eligible BizMuse account. Reply in the user's language. The server owns validation,
entitlement checks, task state, and result normalization.

## Workflow

1. Identify the audio, reference images, and creative direction. Ask only for missing required inputs.
2. Call `list_ai_music_video_models` to confirm the currently available capability and defaults.
3. When WorkBuddy exposes local attachments to the MCP upload flow, call
   `prepare_ai_music_video_upload`, upload the bytes to the returned signed URL using the returned
   headers, and then call `finalize_ai_music_video_upload`. Never put file bytes or Base64 in model
   context. If the input is already available at a public HTTPS URL, use
   `upload_ai_music_video_asset` as the compatibility path.
4. Preserve the returned asset IDs and audio duration. Never pass arbitrary provider URLs directly
   to generation tools.
5. Call `check_ai_music_video_generation` with the audio duration. Do not calculate prices or
   entitlements locally.
6. Present the selected content mode, aspect ratio, quality, resolution, lip-sync choice, and audio
   duration. Ask the user for explicit confirmation before starting generation.
7. Only after confirmation, call `generate_ai_music_video` with `confirmed: true`, one audio asset
   ID, and one to seven image asset IDs. Do not silently retry after a timeout because the first
   request may have been accepted.
8. Poll `get_ai_music_video_status` with increasing intervals while the task is pending or
   processing. Do not block one MCP request waiting for the full render.
9. After success, call `get_ai_music_video_result` and return the video URL, cover URL, task ID, and
   selected parameters.

## Defaults

- `contentMode`: `storytelling`
- `quality`: `standard`
- `resolution`: use the model catalog default
- `aspectRatio`: `16:9`
- `lipSync`: `false`

Supported content modes are `storytelling`, `singing`, `dancing`, and `abstract`. Do not expose
provider names, callback URLs, raw provider options, internal user IDs, or temporary credentials.

## Input constraints

- Audio must be 10-180 seconds and within the current model catalog size limit.
- Reference images must be JPEG, PNG, or WebP, with no more than seven images.
- The prompt is optional and limited by the server catalog.
- `high + 540p` is unavailable; let the server reject or normalize this combination.
- Subtitle controls are not part of this release.

## Safety and recovery

- Treat generation as a state-changing action and always obtain explicit confirmation first.
- Distinguish invalid media, missing account entitlement, expired authorization, unavailable
  options, provider failure, and `submission_unknown`.
- When authorization expires, ask the user to reconnect the BizMuse connector in WorkBuddy.
- Never display prices, credit balances, purchase links, upgrade prompts, auth secrets, or raw
  provider payloads.
- For `submission_unknown`, check task status instead of starting another generation.
