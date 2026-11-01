---
name: microscopy-analysis
description: Detect bright blobs in microscopy images, compare counts and detection scales, and retrieve overlay PNGs and detection JSON. Use for local images or supported institutional image URLs when the user requests microscopy blob analysis or parameter trials.
display_name: "显微图像亮斑分析"
display_name_en: "Microscopy Bright-Blob Analysis"
description_zh: "检测显微图像中的亮斑候选特征，统计数量、位置与尺度，支持检测参数对比，并提供标注叠加图和检测数据。"
description_en: "Detect candidate bright blobs in microscopy images, report counts, positions and scales, compare detection parameters, and retrieve overlays and detection data."
version: "0.1.2"
author: "Tiannian Zhu"
---

# Microscopy Analysis

Use the task-oriented tools from the packaged `microscopy-analysis` MCP
server. Tool names below are raw MCP names; let the client resolve their
namespace.

## Workflow

1. For a local image, call `microscopy_analysis_prepare_upload` with its plain filename. Send
   the raw file bytes using the exact HTTP PUT URL, method, and headers
   returned. Use the returned `attachment_ref` only after the PUT succeeds.
2. For an HTTP(S) image URL under `iphy.ac.cn` or one of its subdomains,
   call `microscopy_analysis_ingest_url` with the URL and a plain filename instead. URLs must
   use the standard HTTP(S) port and contain no user information; redirects
   are rejected. Retain the returned `attachment_ref`.
3. Call `microscopy_analysis_detect_blobs` with one to eight refs in the intended order and
   any requested `params`. Refs are reusable across tasks and may occur
   more than once in a task. Use defaults unless the user specifies a
   parameter trial.
4. Poll `microscopy_analysis_get_task_status` with the returned `task_id` while its status is
   `pending` or `running`. Stop on `failed` and report the returned error.
   Call `microscopy_analysis_get_task_results` only after `succeeded`.
5. Return each image's `source_filename`, `width`, `height`, and
   `blob_count` in submission order, together with the `algorithm_version`
   and `effective_params`. Provide the returned `overlay_png` and
   `detections_json` HTTP GET URLs when files are needed. A null URL means
   the artifact is unavailable; retain the task result and report the
   missing file without inventing a download address.

## Parameters and interpretation

`params` accepts the following fields:

| Field | Default | Meaning and constraint |
| --- | --- | --- |
| `min_sigma` | 2 | Minimum LoG Gaussian sigma in pixels; greater than zero |
| `max_sigma` | 4 | Maximum sigma in pixels; at least `min_sigma` |
| `num_sigma` | 20 | Number of sampled scales; integer from 1 to 100 |
| `threshold` | 0.05 | Nonnegative LoG response threshold, not a confidence probability |
| `exclude_border` | 10 | Nonnegative integer border width in pixels |
| `random_seed` | 0 | Preprocessing seed; integer from 0 to 4294967295 |

The service uses GMM region selection and LoG detection to find local
bright blobs. A detected blob is a candidate image feature, not a
confirmed material defect. The selected region and overlay are not
defect segmentation masks.

Read the returned detection JSON when coordinates or scale details matter.
It records `x`, `y`, `sigma_px`, `radius_px` (approximately
`sqrt(2) * sigma_px`), and `display_radius_px`. The display circle is not
a measured physical radius. Report pixel units unless the user supplies
traceable calibration; do not infer physical dimensions from image size.

A zero count can have different outcomes: `no_detections`, `blank_image`,
or `image_too_small`. Consult the JSON `outcome` before interpreting a
zero count. Preserve these distinctions and compare results with their
effective parameters and input resolution. Task success alone does not
establish detection accuracy on real microscopy samples.

## Transfer and retries

- Never put local paths, Base64, or image bytes in MCP arguments. Raw HTTP
  is used for the upload and download instructions returned by the tools.
  Treat upload URLs and headers as short-lived capabilities; do not copy
  credentials into prose, logs, or retained files.
- Each input and the combined inputs of a task are limited to 100 MiB.
  Supported filename extensions are
  `.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, `.tiff`, and `.webp`. Analysis
  accepts 8-bit grayscale or color images, ignores alpha, and limits
  decoded images to 8192 pixels per side and 16777216 pixels total.
  Do not silently convert high-bit-depth scientific images to 8-bit.
- Reuse refs for parameter trials. Repeating `microscopy_analysis_ingest_url` with the same
  URL and filename returns the original ref rather than refreshing its
  contents. Exact `microscopy_analysis_detect_blobs` retries with the same ordered refs,
  effective parameters, and algorithm version return the original task,
  including a failed task; there is no force-rerun tool.
- Use structured retryability information from tool errors. Do not
  repeatedly resubmit a failed task or treat failure as a zero count.

## Boundaries

If the MCP tools are unavailable, ask the user to connect the packaged
`microscopy-analysis` server. Do not guess results, call private provider
endpoints, or substitute local image processing for this service workflow.
Device control and electronic-lab-notebook writes are separate operations;
this plugin provides image analysis and result retrieval.
