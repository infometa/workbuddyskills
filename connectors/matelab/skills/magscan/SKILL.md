---
name: magscan
description: Analyze magnetic scan TXT inputs with MagScan. Use signal analysis for Interplt channels, profiles, and residual SNR; use field analysis for Bx/By coverage; generate reports from completed analyses. Quantitative magnetic-moment inversion is unavailable.
display_name: "MagScan 磁扫描分析"
display_name_en: "MagScan Magnetic Scan Analysis"
description_zh: "分析 ZIP/RAR 磁扫描归档，生成磁场分布图、剖面、覆盖率和程序定义的信噪比，支持参数对比并导出分析报告。"
description_en: "Analyze ZIP/RAR magnetic scan archives, generate field maps, profiles, coverage and program-defined SNR, compare parameters, and export analysis reports."
version: "0.1.2"
author: "Tiannian Zhu"
---

# MagScan

Use the task-oriented tools from the packaged `magscan` MCP server. Tool names below are raw MCP names; let the client resolve its namespace.

## Workflow

1. For each local TXT input, call `magscan_prepare_upload` with its plain filename. Send the raw file bytes to the returned URL using the returned HTTP method and headers. Use its `attachment_ref` only after the PUT succeeds.
2. For a remote HTTP(S) TXT input, call `magscan_ingest_url` with its URL and plain filename. The Server fetches the file and returns a ready `attachment_ref`. The URL must be on `iphy.ac.cn` or a subdomain, use the standard HTTP(S) port, and contain no user information; redirects are rejected.
3. Choose one analysis operation:
   - `magscan_analyze_signal` takes one `interplt_ref` and optional `params`. Use it for Interplt channel selection, phase rotation, layered profiles, smoothing, and residual SNR. Raw slices are not inputs to this operation.
   - `magscan_analyze_field` takes one `interplt_ref`, ordered `raw_slice_refs`, and optional `params`. Provide 1–1023 distinct raw Y-slice references; none may equal the Interplt reference. Use it for magnetic-field Bx/By and measured-grid coverage. Its only parameter is `sample`.
   Each reference must come from `magscan_ingest_url` or a completed upload. Copy references unchanged. References can be reused across tasks. Keep the Interplt grid and raw slices matched to the selected sample. Apply the user's settings and existing authorization; otherwise state the service defaults. Ask only when an unresolved sample or setting materially affects the requested analysis.
4. Both analysis operations return a `task_id`. Poll `magscan_get_task_status` while status is `pending` or `running`. On `failed`, report its error; call `magscan_get_task_results` only after `succeeded`.
5. Analysis results include `source_filename`, `sample`, `grid_shape` (Y, X), and `warnings`. Signal results also include `snr_pp` and `snr_pp_status`; field results include `field_summary`. Report `algorithm_version` and `effective_params`, and compare scans using their parameters and coverage rather than SNR alone.
6. To create readable outputs and plots, call `magscan_generate_report` with a succeeded signal or field analysis `task_id`. This creates a separate report task. Poll its status and call `magscan_get_task_results` after it succeeds. Analysis results provide `analysis.json`; report results provide PNG, Markdown, HTML, and summary JSON files. Each file has a direct HTTP GET URL when available; a null URL means unavailable. Read `summary.json` when provenance or detailed diagnostics matter. The HTML report embeds its images for standalone viewing.

## Signal parameters

One parameter set applies to the `magscan_analyze_signal` task.

| Field | Default | Meaning and constraint |
| --- | --- | --- |
| `sample` | 1 | Integer 1 or 2; select the matching sample in the Interplt input. |
| `channel` | `lockin_y` | `lockin_x`, `lockin_y`, `signal_x`, `signal_y`, or `tek2110`. |
| `phase_rotation_deg` | 5.0 | Finite angle in degrees; lock-in rotation applies only to lock-in X/Y. |
| `profile_y_index` | null | Zero-based Y row; null selects the middle row. |
| `layers` | 5 | Positive number of Y layers averaged for the profile. |
| `smoothing_window` | 11 | Odd integer at least 3, no greater than profile length. |
| `smoothing_polyorder` | 2 | Nonnegative integer smaller than the smoothing window. |

`magscan_analyze_field` accepts only `sample` (default 1; integer 1 or 2). Defaults come from a standard sample and do not establish optimal settings for another experiment. Invalid smoothing settings fail; do not silently adjust them or claim that the service selected another algorithm.

## Scientific interpretation

- Lock-in X/Y rotation uses X'=X*cos(theta)+Y*sin(theta) and Y'=Y*cos(theta)-X*sin(theta). Interplt grids are supplied as inputs; the service does not generate upstream Interplt data.
- Raw magnetic-field X/Y are measured in nT; `tek2110` is voltage in V. Keep these quantities distinct from the selected Interplt channel. `field_summary` reports extrema, measured/missing cells, and coverage. Raw measurements are averaged onto the nearest grid coordinate, with exact midpoints assigned to the lower coordinate. Missing cells remain missing, rather than becoming zero field.
- Field magnitude is only `sqrt(Bx²+By²)`, without Bz. The service does not perform quantitative magnetic-moment inversion. Do not label these maps as magnetic-moment or magnetic-moment-density distributions.
- `snr_pp` is `peak_to_peak(smoothed_profile) / peak_to_peak(profile - smoothed_profile)` using Savitzky–Golay smoothing. Zero residual noise gives null with `snr_pp_status: zero_noise`, not measured infinite SNR. Ordinary numeric results have status `defined`. Neither task success nor this metric proves instrument calibration or LabVIEW equivalence.
- `summary.json` records provenance, requested settings, input and core source hashes, and dependency versions. Preserve returned warnings about malformed rows, coordinate mismatches, and incomplete field data when interpreting results.

## Transfers and retries

- Never send local paths, Base64, or TXT bytes as MCP arguments. Use raw HTTP for returned upload and download instructions. Treat upload URLs and headers as short-lived capabilities; do not retain credentials in prose, logs, or files.
- `magscan_prepare_upload` accepts one plain TXT filename, not a ZIP/RAR archive. Do not silently rename or alter original evidence to make an input pass validation.
- Repeating `magscan_ingest_url` with the same URL and filename returns the original reference. Exact retries of `magscan_analyze_signal` or `magscan_analyze_field` with the same role-assigned references, effective parameters, and algorithm version return the original task, including a failed task. There is no force-rerun tool. Use separate tasks for deliberate parameter trials.
- Follow structured error `code`, `retryable`, and `recovery` information. If submission acknowledgement is uncertain, retry with the same inputs and settings. Do not repeatedly resubmit a known failed task or present failure as a valid zero-valued scientific result.

## Availability

If the tools are unavailable, ask the user to connect the packaged `magscan` server. If the host cannot perform the required raw HTTP file transfer, explain that limitation. Do not claim analysis ran, guess results, or substitute local processing for this service workflow.
