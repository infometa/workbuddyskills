# Flow node-metric-user

Use this reference when the user asks for users behind a node-level metric segment on the flow canvas.

Mapped CLI commands:

- `ae-cli engage-flow node-metric-user run`
- `ae-cli engage-flow node-metric-user export`

Mapped capabilities:

- `engage-flow.node-metric-user.run`
- `engage-flow.node-metric-user.export`

Hermes SQL source: `FlowNodeReportDataService#buildMetricClusterUserSql`.

## Choose the command

- Use `run` for a bounded inline preview of users behind the selected node metric segment.
- Use `export` for the full user-detail artifact.
- Use `node-user` for node data segments that are not metric-detail segments.
- Use `metric-user` for process-level flow metric cells.

## Required input

- `--project-id`
- one of `--flow-id` or `--flow-uuid`
- `--node-uuid`
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

Prefer the explicit report fields. Set `--indicator-name` to the metric key returned by the node metric report and reuse the report date range. Hermes builds the internal cluster definition.

`--cluster-def` remains available for compatibility. When used, it must come from the selected node metric report segment; do not invent it.

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
ae-cli engage-flow node-metric-user run \
  --project-id 1 \
  --flow-id flow_id_123 \
  --node-uuid node_uuid_123 \
  --indicator-name metric_setting_id_123 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --limit 100 \
  --timeout-seconds 120
```

Export all matched users:

```bash
ae-cli engage-flow node-metric-user export \
  --project-id 1 \
  --flow-id flow_id_123 \
  --node-uuid node_uuid_123 \
  --indicator-name metric_setting_id_123 \
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
  --output ./flow-node-metric-users.csv.gz
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

- `--node-uuid` is required and must be the canvas node UUID.
- Do not use this for node data cells; use `node-user` so Hermes routes to the non-metric SQL builder.
- Use `--data-view-type`, not the report-only `--data-dim-type`, when selecting users without `--cluster-def`.
