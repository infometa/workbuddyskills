---
name: kling-ai
description: Create and monitor Kling AI image and video generations through the OAuth-protected remote Kling MCP server. Use for text-to-image, image-to-image, text-to-video, image-to-video, uploads, task status, and credit checks.
---

# Kling AI

Use the `kling-ai` MCP server at `https://klingai.com/mcp`.

## Route specialized generation

- Route 文生图, 图生图, text-to-image, image-to-image, posters, covers, product stills, and image concept requests to `kling-ai-generate-image`.
- Route 文生视频, 图生视频, text-to-video, image-to-video, animation, camera motion, storyboards, and video concept requests to `kling-ai-generate-video`.
- Keep OAuth, uploads, credit checks, cross-media requests, and task status in this Skill.
- Route follow-ups on an existing output through the result workflow instead of creating a new generation.

An attachment does not determine its own role. When the user has not said how to use attached media, ask whether it is a first frame, identity/product reference, editable source, or style inspiration before submission.

## Safety and submission contract

- Use OAuth through the host MCP connection flow. Never ask for an API key or expose credentials, cookies, authorization headers, private account fields, or signed URLs in logs.
- A user request to generate authorizes one submission after materially missing inputs are resolved. Do not add a credit-cost warning or a separate confirmation step.
- Submit at most once per approved intent. Do not automatically retry failed or ambiguous submissions.
- Discover the live remote tools and schemas at runtime; the provider schema overrides examples in this Skill.
- Upload attached media with the remote upload tool before generation when required. Reuse the returned provider reference exactly as the live schema requires.
- If submission returns a non-terminal state, poll with the status tool declared by the live schema at provider-allowed intervals until the task succeeds or fails. Stop only if the user cancels or the current turn times out; then return the current state and task number.

Read [references/tool-workflows.md](references/tool-workflows.md) before a generation call. Read troubleshooting guidance only after an authorization, schema, upload, or provider failure.

## OAuth client identity

Before OAuth dynamic client registration, include `client_name: "Plugin-WorkBuddy"`. This is OAuth metadata, not a tool argument, URL parameter, or secret. If the host cannot inject it, stop before authorization and report the limitation.

## Workflow

1. Identify the requested generation or read-only operation.
2. Ask only for missing creative requirements that materially affect the result.
3. Resolve only missing settings that materially change the result.
4. Call the selected remote generation tool exactly once.
5. Preserve the exact `generationId` and any `taskTraceId` returned by the provider. Show `generationId` to the user only as **任务编号**. Keep `taskTraceId` internal unless support or troubleshooting specifically needs it.
6. If the submission is not terminal, poll its status at provider-allowed intervals until success or failure. On user cancellation or current-turn timeout, return the current state and task number.
7. Report the result returned by the remote tool. Provide the primary image, video, text, or one Markdown link to the main output when available.
8. For a direct status request, call the live status tool once and report the current state; do not start a new long-running poll.

## Defaults

Use defaults only when the user did not specify alternatives and the live schema supports them:

- video resolution: `720p`
- video duration: `5` seconds
- text-to-video aspect ratio: `16:9`
- image-to-video aspect ratio: derive from the first frame unless required

## Failure behavior

- Authorization failure: direct the user to the host MCP connection flow, then retry only after authorization succeeds.
- Invalid model or argument: refresh the live schema and revise only the unsupported field.
- Provider task failure: explain the provider message and preserve the `generationId`; do not resubmit.
- Insufficient credits: tell the user the balance is insufficient and ask them to recharge before trying again. Do not retry automatically.
- Lost or timed-out submission response: treat task creation as unknown and query existing tasks before considering any new submission.
