---
name: pxrdgen
description: Predict candidate crystal structures from powder X-ray diffraction data and retrieve generated CIF files. Use when a user provides a PXRD .dat input, chemical formula, or PXRDGen task and wants structure candidates or explicit inference trials.
display_name: "PXRDGen 晶体结构预测"
display_name_en: "PXRDGen Crystal Structure Prediction"
description_zh: "根据粉末 X 射线衍射数据和化学式生成晶体结构候选，支持比较不同模型结果，并提供可用的 CIF 文件供后续验证。"
description_en: "Generate candidate crystal structures from powder X-ray diffraction data and a chemical formula, compare model outputs, and retrieve available CIF files for further validation."
version: "0.1.2"
author: "Tiannian Zhu"
---

# PXRDGen

Use the task-oriented tools from the packaged `pxrdgen` MCP server. Tool names
below are raw MCP names; let the client resolve their namespace.

## Workflow

1. For a local XRD `.dat` file, call `pxrdgen_prepare_upload` with its plain filename.
   Send the raw bytes with the exact HTTP `PUT` URL, method, and headers it
   returns. After a successful PUT, retain the returned `attachment_ref`.
2. For a `.dat` file already available at an HTTP(S) URL under `iphy.ac.cn` or
   one of its subdomains, call `pxrdgen_ingest_url` with the URL and plain filename.
   Retain its returned `attachment_ref`.
3. Call `pxrdgen_predict` with exactly one ref and the user-declared chemical formula.
   Preserve any explicit `num_evals`, `cell_params`, `step_lr`,
   `infer_timesteps`, and `model_family` settings. Reuse the same ref for
   comparisons across parameter sets.
4. Poll `pxrdgen_get_task_status` with the returned `task_id`. Stop on `FAILED` and
   report the returned `error` message. Call `pxrdgen_get_task_outputs` only after
   `SUCCEEDED`.
5. Preserve candidate index order and use each available direct HTTP GET URL
   to return the generated CIF file. Report unavailable artifacts rather than
   reconstructing CIF text.

## Input and Parameter Rules

- Never place local paths, Base64, XRD points, or file bytes in MCP tool
  arguments. MCP returns transfer instructions; it does not transport the
  payload.
- A valid input is UTF-8 `.dat` text no larger than 1 MiB, with exactly 7,500
  whitespace-delimited `2theta intensity` rows on the grid from `5.00` through
  `79.99` in increments of `0.01`. Let the Server validate it.
- `num_evals` is 1–256. `model_family` is `flow` or `diffusion` when supplied.
  `cell_params` selects constrained prediction and must represent
  `a,b,c,alpha,beta,gamma`. Use `step_lr` and `infer_timesteps` only as explicit
  inference controls, not as scientific confidence measures.
- Treat upload URLs and their headers as short-lived capabilities. Use them
  only for the specified PUT, and never copy credentials or authentication
  headers into tool arguments, prose, logs, or retained files.

## Retry and Scientific Boundaries

- Repeating `pxrdgen_ingest_url` with the exact URL and filename is idempotent. An
  exact `pxrdgen_predict` retry with the same ref, formula, and all parameters returns
  the existing task. Do not blindly replay any other indeterminate mutation.
- Retry only when a structured tool error marks the operation retryable, and
  follow its recovery guidance. A failed task is not an empty prediction.
- Generated structures are model candidates under the recorded inputs and
  parameters. Do not describe them as experimentally confirmed, uniquely
  solved, thermodynamically stable, or synthesizable without separate evidence.

If the MCP tools are unavailable, ask the user to connect the packaged
`pxrdgen` server. Do not bypass MCP by calling private provider endpoints,
substitute local structure prediction, or guess task, input, or artifact data.
Raw HTTP is used only with upload or download instructions returned by MCP.
