---
name: arpes-denoise-demesh
description: Denoise ARPES data and remove periodic scan-mesh artifacts through the ARPES MCP service. Use when processing ARPES text matrices, Igor Pro waves, or common image files from local uploads, iphy.ac.cn URLs, or existing reusable input refs.
display_name: "ARPES 数据处理"
display_name_en: "ARPES Data Processing"
description_zh: "对 ARPES 测量数据进行常规降噪或扫描网格伪影去除，并返回处理矩阵和预览结果。"
description_en: "Denoise ARPES measurements or remove scan-mesh artifacts, returning processed matrices and previews."
version: "0.1.2"
author: "Tiannian Zhu"
---

# ARPES Denoising and Demeshing

Use the ARPES MCP tools to process files without putting file paths, Base64, or file contents in MCP arguments.
Tool names below are raw MCP names; let the client resolve namespaces and use each tool's current schema.

## Choose the operation

- Use `arpes_denoise` for ordinary measurement noise.
- Use `arpes_demesh` for periodic scanning-grid or mesh artifacts. Its `sr_mode` is `fast` by default; use `quality` only when higher-resolution refinement is worth the additional processing time. `num_iterations` defaults to 1000.

## Prepare inputs

A task accepts 1–8 distinct input refs. Each file and the combined inputs for one task must fit within 100 MiB.
Choose the input path according to what the user provides:

- Local file: follow the upload steps below.
- HTTP(S) URL at `iphy.ac.cn` or a subdomain: call `arpes_ingest_url(url, filename)` with the URL and a plain filename
  including its supported extension. The Server downloads the file directly and returns a ready `attachment_ref`.
  Redirects are rejected and caller credentials are not forwarded. Repeating the exact URL and filename returns the
  original ref; use the final non-redirecting URL if needed.
- Existing `attachment_ref`: reuse it unchanged. If only a prior `task_id` is available, call `arpes_get_task_status` to
  recover its ordered `attachment_refs`.

Do not use `arpes_prepare_upload` for URL ingestion or to inspect an existing task. If a URL is outside the supported
domain, explain the limit and request a local file or supported URL.

For each local file:

1. Call `arpes_prepare_upload` with only its plain filename, including the supported extension. Size and checksum are not
   tool arguments; the Server measures the uploaded body.
2. Send the raw file bytes with HTTP `PUT` to the returned one-time URL, using the returned headers exactly.
3. After the PUT succeeds, keep the returned `attachment_ref` unchanged. The upload URL is short-lived and single-use;
   the completed input ref is reusable across tasks. Never construct or decode refs, or associate one with another file.

If the client cannot perform the raw HTTP upload, explain that limitation and stop the local-file workflow. Never
work around it by embedding bytes or Base64 in tool content.

## Submit and monitor

Once all selected inputs are ready, call `arpes_denoise` or `arpes_demesh` with their refs in the intended order. Submission is
idempotent for the same operation, ordered refs, and parameters: an exact repeat returns the existing task. If the
submission response is lost, repeat that exact call to recover its task ID. Changing parameters creates a new task
using the same inputs; no new upload is needed. An exact repeat of a failed task does not restart processing.

Use the returned `task_id` with `arpes_get_task_status` while status is `pending` or `running`, until it reaches `succeeded`
or `failed`. If it fails, report the service error. For tool errors, follow `code`, `message`, `retryable`, and optional
`recovery` rather than retrying blindly. Keep the task ID and input refs for later queries or parameter trials.

## Download outputs

After the task succeeds, call `arpes_get_task_outputs`; use `arpes_get_task_status` for polling. `outputs` follows input submission
order. Each entry contains `result`, `source_preview`, and `result_preview`, with optional `mesh_preview` and
`loss_preview` for demeshing. Each file has a `filename`, possibly unknown `size`, and a direct Server HTTP GET `url`.

Download files with non-null URLs outside MCP. Result matrices are the numeric outputs; previews, mesh residuals,
and loss histories are visual diagnostics. A null URL means that artifact is unavailable even though task history
remains queryable. These are direct download URLs, not expiring MCP tickets; calling `arpes_get_task_outputs` again does not
restore removed files. Report the task ID, files saved or returned, and any unavailable artifacts.
