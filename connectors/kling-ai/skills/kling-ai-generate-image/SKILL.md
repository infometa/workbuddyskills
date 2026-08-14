---
name: kling-ai-generate-image
description: Generate or transform images with the OAuth-protected remote Kling MCP server. Use for text-to-image, image-to-image, posters, portraits, product photography, lifestyle scenes, ad creatives, social covers, YouTube thumbnails, conceptual product visuals, and reference-guided image work. Use when the user asks for an image, picture, poster, key visual, product shot, thumbnail, cover, campaign still, or image variation.
---

# Kling AI Image Generation

Turn a creative brief into one well-specified Kling image request. Use only the live remote `kling-ai` MCP tools and schemas at `https://klingai.com/mcp`.

## Contract

- Use host-managed OAuth. Never request or expose API keys, tokens, cookies, authorization headers, or signed URLs.
- A user request to generate authorizes one submission after materially missing inputs are resolved. Do not add a credit-cost warning or a separate confirmation step.
- Submit once per approved intent. Never blind-retry an ambiguous or failed submission.
- Discover the live schema before choosing tools, models, input names, or enumerated values. Live provider fields override examples here.
- Upload attached reference media with the remote upload tool when required, then reuse the returned provider reference exactly.

## Workflow

1. Classify the request using the mode table below.
2. Read [scene patterns](references/scene-patterns.md) for product, advertising, thumbnail, portrait, editorial, or conceptual work.
3. Read [prompt construction](references/prompt-construction.md) when the brief is vague, has references, contains exact copy, or needs multiple controlled variants.
4. Ask only for missing facts that materially change the result: subject/product, intended use, ratio, required copy, or mandatory reference identity.
5. Build one prompt that separates subject, action, environment, composition, lighting, palette, material detail, camera language, and exclusions.
6. Call the live image generation tool once when the request has enough information. Preserve the exact `generationId` and any `taskTraceId`.
7. If the submission is not terminal, poll its status at provider-allowed intervals until success or failure. On user cancellation or current-turn timeout, return the current state and task number.
8. Provide the primary image or result link returned by Kling. Show `generationId` as **任务编号** and keep `taskTraceId` internal unless troubleshooting requires it.

## Generation modes

| User intent | Mode | Required interpretation |
| --- | --- | --- |
| 文生图 / text-to-image | New image | No source image controls identity or composition. Build the scene from the text brief. |
| 图生图 / image-to-image | Edit or reference-guided image | At least one image controls content, identity, product geometry, composition, or style. Assign every input an explicit role. |
| 变体 / restyle | Focused image-to-image change | Lock all unspecified source facts and name the one allowed change. |
| 查进度 / status | Read-only | Do not call a generation tool; query the existing task. |

Do not silently switch modes. An attached image is not automatically an image-to-image instruction: if the user asks for an unrelated new image, ignore it only after confirming it is irrelevant. Conversely, never reduce an explicit 图生图 request to text-to-image after an upload or schema failure.

Before calling the tool, check the selected mode, ratio, reference roles, and
allowed changes internally. Do not show a pre-submission process message unless
you need the user to clarify a missing creative requirement.

## Defaults

- Choose ratio from the destination: `1:1` square social/product, `4:5` feed portrait, `9:16` story/vertical cover, `16:9` landscape banner or thumbnail.
- Prefer a clean image without text unless the user explicitly requires text in the generated artwork.
- For variants, change one named dimension per approved generation: concept, composition, palette, camera distance, or expression. Do not use near-duplicate prompts.
- Preserve supplied brand names, labels, logos, faces, and product geometry as locked constraints. Never invent claims, prices, certifications, ingredients, results, or statistics.

## Quality gate

Before submission, check that the brief has one clear focal subject, a readable hierarchy, destination-appropriate safe space, coherent lighting, and no conflicting camera/composition instructions. When the host can inspect outputs, verify reference fidelity, text accuracy, subject count, and obvious artifacts. Do not claim visual QA when inspection is unavailable.

## Failure behavior

- Authorization failure: direct the user to WorkBuddy's native MCP connection flow.
- Unsupported argument: refresh the live schema and revise only the rejected field.
- Insufficient credits: tell the user to recharge and stop. Do not retry automatically.
- Lost response: treat task creation as unknown and query existing tasks before any new generation.
- Provider failure: report the provider message and preserve IDs; do not resubmit automatically.
