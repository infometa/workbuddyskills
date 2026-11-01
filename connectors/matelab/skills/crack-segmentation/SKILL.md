---
name: crack-segmentation
description: Segment cracks in SiCf/SiC composite microscopy images, compare crack statistics, and retrieve mask and overlay PNG results. Use when a user provides local images or supported institutional image URLs for crack detection or parameter trials.
display_name: "复合材料裂纹分割"
display_name_en: "Composite Crack Segmentation"
description_zh: "对 SiCf/SiC 复合材料图像进行裂纹分割，统计裂纹像素与比例，支持置信度阈值对比，并提供可用的掩膜和叠加图。"
description_en: "Segment cracks in SiCf/SiC composite images, report crack pixel counts and ratios, compare confidence thresholds, and retrieve available masks and overlays."
version: "0.1.2"
author: "Tiannian Zhu"
---

# Crack Segmentation

Use the task-oriented tools from the packaged `crack-seg` MCP server. Tool
names below are raw MCP names; let the client resolve their namespace.

## Workflow

1. For each local image, call `crack_seg_prepare_upload` with its plain filename. Send
   the raw file bytes with the exact HTTP `PUT` URL, method, and headers it
   returns. After a successful PUT, retain the returned `attachment_ref`.
2. For an image already available at an HTTP(S) URL under `iphy.ac.cn` or one
   of its subdomains, call `crack_seg_ingest_url` with the URL and a plain filename.
   Retain its returned `attachment_ref`.
3. Call `crack_seg_segment_cracks` with one to eight distinct refs in the intended
   order. Set `stride` and `confidence_threshold` explicitly when the user
   requests a parameter trial; otherwise use the tool defaults.
4. Poll `crack_seg_get_task_status` with the returned `task_id`. Stop on `FAILED` and
   report the returned `error` message. Call `crack_seg_get_task_results` only after
   `SUCCEEDED`.
5. Return the per-image `crack_pixels` and `crack_ratio`. Use the direct HTTP
   GET URLs returned for each mask and overlay PNG when the user needs files.
   A null URL means that artifact is unavailable; report it without inventing
   a download address.

## Transfer and Retry Rules

- Never place local paths, Base64, or image bytes in MCP tool arguments. MCP
  returns transfer instructions; it does not transport the image payload.
- Treat upload URLs and their headers as short-lived capabilities. Use them
  only for the specified PUT, and never copy credentials or authentication
  headers into tool arguments, prose, logs, or retained files.
- Each input and the complete task are limited to 100 MiB. Supported plain
  filenames end in `.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, `.tiff`, or
  `.webp`.
- Reuse an unchanged `attachment_ref` for parameter trials. Exact
  `crack_seg_segment_cracks` retries with the same ordered refs and parameters are
  idempotent. Do not blindly replay an indeterminate mutation unless its
  structured result or tool contract identifies that exact retry as safe.
- Use only structured retryability information from tool errors. A failed
  task is not an empty segmentation result.

## Boundaries

If the MCP tools are unavailable, ask the user to connect the packaged
`crack-seg` server. Do not bypass MCP by calling private provider endpoints,
substitute local image processing, or guess task or result data. Raw HTTP is
used only with upload or download instructions returned by the MCP workflow.

Treat model output as segmentation evidence under the recorded stride and
confidence threshold, not as ground truth. Preserve input order, parameters,
warnings, failed items, and missing artifacts when comparing results.
