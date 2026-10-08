# analysis adhoc export

Submit one unified ad-hoc analysis export from an AI-facing model definition.

Typical closed loop: define and validate the analysis -> resolve an authorized physical query route if needed -> submit once -> keep the returned run/artifact pair -> inspect -> download -> analyze the complete artifact. Use a separate synchronous run when interactive drilldown is required.

Routing: read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing this `export` command instead of `adhoc run`.

## Command

```bash
ae-cli analysis adhoc export \
  --project-id <project_id> \
  --model-type <model_type> \
  --definition '<json>' \
  [--resolutions '<confirmed_resolution_json>'] \
  [--request-id cli_<32 lowercase hex>] \
  [--use-cache true|false] \
  [--zone-offset <hours>] \
  [--fields '["列名"]'] \
  [--cluster-query-scope GLOBAL|SLAVE] \
  [--slave-cluster-id <id>] \
  [--artifact-format jsonl|csv] \
  [--timeout-seconds <n>] \
  [--wait] \
  [--wait-timeout-seconds <n>] \
  [--output <file>] \
  [--force]
```

## AI models

Read [`ai_models.md`](ai_models.md) for the single 12-model `model_type` registry, AI-facing `definition`, and SQL dynamic params contract.

For SQL model definitions, do not invent table or column names. If the table reference is known, inspect columns with `analysis-meta datatable columns-get`; if the table is unknown, ask for it instead of guessing.

## Definition contract

Rules:

- `export` does not accept `--limit` or `--offset`; use `--fields` for column projection and download the full artifact.

## Input

- `--project-id`: target project ID.
- `--model-type`: one of the 12 AI-facing model names from [`ai_models.md`](ai_models.md). Do not pass `scenario`, `history_tag`, or `cluster`; tags and cohorts/clusters are separate capabilities.
- `--definition`: model-specific AI-facing definition JSON.
- `--resolutions`: only after user confirmation, pass deterministic bindings keyed by compiler error path while keeping `--definition` unchanged. Follow [`../metadata_resolution.md`](../metadata_resolution.md).
- `--artifact-format`: `jsonl` or `csv`.

Async export has no inline row limit. Runtime defaults to and is capped at 21600 seconds (6 hours); cancel earlier with `analysis query cancel --run-id <run_id>`. The routing rule lives in [`analysis_data_retrieval.md`](analysis_data_retrieval.md).

Do not use raw QP, `events`, `event_view`, `visual_view`, removed ad-hoc QP builder outputs, or schema helper outputs as `--definition`.

Timezone contract: fixed `--zone-offset` values are integers from `-12` through `14`. Use `--zone-offset 99` for local-time mode, which analyzes timestamps as stored local time without applying a fixed UTC offset conversion; it does not mean UTC+99. Omit the flag to use the project's analysis default.

Cluster routing is identical to `adhoc run`: omit for current self; discover permissions and physical IDs with `analysis query-cluster list`; `SLAVE` requires an ID. SQL, attribution, and default-interval distribution reject unsupported `GLOBAL` rather than silently changing scope.

## Output

The response is an async artifact descriptor:

- `run_id`: poll or cancel this run.
- `artifact_id`: download this artifact after completion.
- `status` / `artifact_status`: initial lifecycle states.
- `expires_at` / `expires_at_iso`: artifact expiration.
- `effective_timeout_seconds`, `timeout_source`, `deadline_at`: effective lifecycle policy.
- Export descriptors contain lifecycle/artifact metadata only. They do not create `query_context_id` or selectable drilldown options.

Preserve the `run_id` and `artifact_id` from this exact submit response as one pair. Do not infer either ID from a path or reuse an ID from another export.

Export submission compiles the definition before creating an artifact or run. The execute, `--validate`, and `--dry-run` paths return `AI_QP_COMPILE_FAILED` immediately when clarification is required, with `meta.compile_status`, full structured `meta.errors[]`, `meta.resolved`, and `meta.warnings`. Follow [`../metadata_resolution.md`](../metadata_resolution.md), confirm candidates, then retry with `--resolutions`. A compile failure has no `run_id` or `artifact_id`.

Use:

```bash
ae-cli analysis adhoc export ... --wait
ae-cli analysis adhoc export ... --output <file>
ae-cli analysis run wait --run-id <run_id> [--output <file>]
ae-cli analysis run inspect --run-id <run_id>
ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output <file>
ae-cli analysis query cancel --run-id <run_id>
```

Plain export submits only. `--output` implies `--wait`;
`--wait-timeout-seconds` defaults to 600 seconds and controls only the local
CLI wait. `--force` is valid only
with `--output` and permits atomic replacement of an existing file. Local wait
interruption or deadline does not cancel the remote run.

If query execution fails, `run inspect` reaches `FAILED`; it must not produce a completed empty artifact. Download only after the successful terminal states documented in `analysis_data_retrieval.md`.

Exported rows are durable data, not interactive preview coordinates. Never drill down or create a result cluster from the submit response or downloaded artifact. Run a bounded synchronous preview containing the desired cell first.
