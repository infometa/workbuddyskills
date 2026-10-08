# Flow metric-detail report

Use this reference when the user asks for a flow node metric-detail report, or wants to export the detailed metric table behind a node on the flow canvas.

Mapped CLI commands:

- `ae-cli engage-flow report metric-detail run`
- `ae-cli engage-flow report metric-detail export`

Mapped capabilities:

- `engage-flow.report.metric-detail.run`
- `engage-flow.report.metric-detail.export`

## Choose the command

- Use `run` for quick inline inspection. It returns the original Hermes report object under `report`.
- Use `export` when the user needs a downloadable, flattened artifact.
- Use `--report-mode node` or omit it for normal nodes.
- Use `--report-mode ab` for AB split node metric details.

Do not use the older generic capability form unless the structured command is unavailable.

## Required input

- `--project-id`
- one of `--flow-id` or `--flow-uuid`
- `--node-uuid`
- `--start-time yyyy-MM-dd`
- `--end-time yyyy-MM-dd`

## Optional input

- `--report-mode node|ab` (default: `node`)
- `--branch-id`
- `--indicator-name` for normal node metric selection
- `--indicators-uuid` for AB metric selection
- `--data-dim-type uv|pv`
- `--push-language-code`
- `--show-time-zone`
- `--request-id`
- `--timeout-seconds`
- `run` only: `--limit` is accepted for command consistency, but metric-detail reports are not row-limited by Hermes
- `export` only: `--artifact-format csv|jsonl` (default: `jsonl`)

## Parameter guidance

- Prefer `flow_uuid` when the user is talking about a specific flow version; prefer `flow_id` when they mean the current logical flow.
- `node_uuid` must be the canvas node UUID, not the node type.
- Dates are inclusive report dates and must be in `yyyy-MM-dd`.
- For AB mode, pass the AB node UUID and usually `--indicators-uuid`; `--branch-id` is optional and only use it when the selected report cell is branch-specific.
- If both `flow-id` and `flow-uuid` are supplied, Hermes checks they match.

## Examples

Inline normal node metric detail:

```bash
ae-cli engage-flow report metric-detail run \
  --project-id 1 \
  --flow-id flow_id_123 \
  --node-uuid node_uuid_123 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --timeout-seconds 120
```

Export normal node metric detail as CSV:

```bash
ae-cli engage-flow report metric-detail export \
  --project-id 1 \
  --flow-id flow_id_123 \
  --node-uuid node_uuid_123 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --artifact-format csv \
  --timeout-seconds 21600
```

Inline AB node metric detail:

```bash
ae-cli engage-flow report metric-detail run \
  --project-id 1 \
  --flow-id flow_id_123 \
  --node-uuid ab_node_uuid_123 \
  --report-mode ab \
  --indicators-uuid indicator_uuid_123 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07
```

## Export lifecycle

`export` returns `run_id` and `artifact_id`. Poll and download with:

```bash
ae-cli engage-query run inspect --run-id <run_id>
ae-cli engage-query artifact download \
  --run-id <run_id> \
  --artifact-id <artifact_id> \
  --output ./flow-metric-detail.csv.gz
```

Downloaded artifacts are gzip-compressed; keep the `.gz` suffix. Cancel running async work with:

```bash
ae-cli engage-query query cancel --run-id <run_id>
```

## Output rows

Normal node export rows:

- `time`
- `indicator`
- `value_index`
- `value`

AB node export rows:

- `time`
- `branch_id`
- `branch_name`
- `indicator`
- `value`
- `total`

## Common mistakes

- Do not pass `report-mode ab` for a normal node; Hermes will call the AB report backend.
- Do not use `indicator_name` and `indicators_uuid` interchangeably: normal node uses `indicator_name`, AB mode usually uses `indicators_uuid`.
- Do not save a gzip artifact as `.csv` or `.jsonl`; use `.csv.gz` or `.jsonl.gz`.
