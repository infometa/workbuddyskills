# Flow metric-user

Use this reference when the user asks for users behind a process-level flow metric segment, such as a cell in the flow process report.

Mapped CLI commands:

- `ae-cli engage-flow metric-user run`
- `ae-cli engage-flow metric-user export`

Mapped capabilities:

- `engage-flow.metric-user.run`
- `engage-flow.metric-user.export`

Hermes SQL source: `FlowReportDataService#buildClusterUserSql`.

## Choose the command

- Use `run` for a bounded inline preview of matched users.
- Use `export` for the full user-detail artifact.
- This command does not require `--node-uuid`; use `node-user` or `node-metric-user` for node-level cells.

## Required input

- `--project-id`
- one of `--flow-id` or `--flow-uuid`
- either `--cluster-def '<cluster_def_json>'` or all of `--indicator-name`, `--start-time`, and `--end-time`

## Optional input

- `--branch-id`
- `--request-id`
- `--data-view-type` (default: `2`)
- `--is-summary`
- `--push-language-code`
- `--user-time-zone`
- `--show-time-zone`
- `run` only: `--limit`
- `export` only: `--artifact-format csv|jsonl` (default: `jsonl`)
- `--timeout-seconds`

Only pass fields listed above. Hermes rejects extra top-level fields for this capability.

## Segment selector contract

Prefer the explicit report fields. Set `--indicator-name` to the metric key returned by the process report and reuse the report date range. Hermes builds the internal cluster definition.

`--cluster-def` remains available for compatibility. When used, it must come from the selected report segment; do not invent or hand-minify partial JSON.

Required keys:

- `indicatorName`
- `dataViewType`
- `isSummary`

Date keys depend on `isSummary`:

- `isSummary=true`: require `filterStartDate` and `filterEndDate`
- `isSummary=false`: require `startDate` and `endDate`

Dates must use `yyyy-MM-dd`, and start must be earlier than or equal to end.

## Examples

Inline preview:

```bash
ae-cli engage-flow metric-user run \
  --project-id 1 \
  --flow-id flow_id_123 \
  --indicator-name entry \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --limit 100 \
  --timeout-seconds 120
```

Export all matched users:

```bash
ae-cli engage-flow metric-user export \
  --project-id 1 \
  --flow-id flow_id_123 \
  --indicator-name entry \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --artifact-format csv \
  --timeout-seconds 21600
```

## Export lifecycle

`export` returns `run_id` and `artifact_id`. Poll and download with:

```bash
ae-cli engage-query run inspect --run-id <run_id>
ae-cli engage-query artifact download \
  --run-id <run_id> \
  --artifact-id <artifact_id> \
  --output ./flow-metric-users.csv.gz
```

Downloaded artifacts are gzip-compressed; keep the `.gz` suffix. Cancel running async work with:

```bash
ae-cli engage-query query cancel --run-id <run_id>
```

## Output shape

- `run` returns `rows`, `total`, and `column_meta`.
- `export` writes one row per matched user with `#user_id`, `#account_id`, and `#distinct_id`.
- For cross-user data sources, `#account_id` and `#distinct_id` are empty strings.

## Common mistakes

- Do not pass `--node-uuid` unless the process-level report segment actually needs branch/node context; for normal node cells use `node-user`.
- Use `--data-view-type`, not the report-only `--data-dim-type`, when selecting users without `--cluster-def`.
- If `cluster_def` is missing the date pair implied by `isSummary`, Hermes rejects it before SQL execution.
