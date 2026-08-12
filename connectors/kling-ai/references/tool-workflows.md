# Tool workflows

Use the live MCP schema as the source of truth. The endpoint has previously
exposed tools such as `file_upload`, `image_to_image`, `image_to_video`,
`query_membership_and_credits`, `query_tasks`, `text_to_image`,
`text_to_video`, and `who_am_i`; this observed list is not a compatibility
promise.

## Text generation

1. Choose `text_to_image` or `text_to_video` from the user intent.
2. Inspect the live tool schema and model options.
3. Present the final billable settings and obtain explicit confirmation
   unless the current user message already authorizes immediate submission
   with those settings.
4. Send the prompt and approved settings once.
5. Capture `generationId` and `taskTraceId` from the result.
6. Capture the `generationId` and `taskTraceId`, then delay status checks:
   make the first image query at 60 seconds and the first video query at 120
   seconds. Continue every 10 seconds for images or every 15 seconds for
   videos. Stop at a terminal state, 5 minutes for images, or 10 minutes for
   videos.

## Attached or local media

Do not pass a local path, chat attachment URL, data URL, external URL, or
legacy `first_frame_url` directly to a generation tool.

1. Generate one UUID v7 `taskTraceId`.
2. Call `file_upload` with `contentType`, `filename`, `size`, and the trace
   ID.
3. Use only the Kling URL returned by `file_upload`.
4. Reuse the same trace ID for the generation call.
5. Keep upload and generation separate in the user-facing flow: upload
   success does not authorize the billable generation call.

For single-frame image-to-video, the verified request shape is:

```json
{
  "model": "kling-video-v3_0_turbo",
  "arguments": [
    { "name": "prompt", "value": "Slow, stable camera push-in; preserve subject identity" },
    { "name": "duration", "value": "5" },
    { "name": "resolution", "value": "720p" }
  ],
  "inputs": [
    { "name": "first_image", "inputType": "URL", "url": "<Kling upload URL>" }
  ],
  "rationale": "Single reference image and one continuous shot",
  "taskTraceId": "<same UUID v7>"
}
```

All `arguments[].value` values are strings. Model identifiers, input names,
durations, and optional fields can change; inspect the live schema before
calling.

If the generation request times out before a response is received, do not
assume it failed. Treat the outcome as unknown and query existing tasks using
the available trace/task identifiers before asking the user about a new
submission.

## Multi-shot video

Use `kling-video-v3_0` when the user explicitly requests multiple shots. If
the live schema allows it, send `prefer_multi_shots` as the string `"true"`.
Describe shots with durations whose total matches the requested video
duration.

Use `kling-video-v3_0_omni` when the user supplies multiple references or
asks to preserve named elements across scenes. Map every uploaded reference
to the exact input name declared by the live schema.

## Status and credits

- Use `query_membership_and_credits` only when the user asks about
  availability or credits, or when a provider error specifically requires
  that check.
- Use `query_tasks` once for an explicit status request.
- After submission, continue calling `query_tasks` with the same IDs until the
  task completes, fails, or reaches its type-specific timeout. Do not resubmit.

## Result normalization

Do not label provider URLs as generic numbered results. Preserve provider
metadata and classify outputs when evidence allows:

- `video/main` → 生成视频（主结果）
- `image/cover` → 视频封面（预览图），not a second video
- `image/main` → 生成图片（主结果）
- unknown/other → 补充结果，without guessing
