# analysis report create

Use when the user explicitly wants to create a saved analysis report from an AI QP definition.

Do not use raw QP, `analysis_query`, `events`, `event_view`, or `visual_view`. The gateway accepts `model_type` plus AI QP `definition`.

Read [`ai_models.md`](ai_models.md) for the single AI-facing model registry. Report create supports the 12 analysis models plus `tag` for saved tag report data.

Command:

```bash
ae-cli analysis report create --project-id <project_id> --report-name "Demo" --model-type event --definition '{...}' [--resolutions '<confirmed_resolution_json>'] [--report-desc "..."] [--dashboard-ids "[1001]"]
```

Input sends `project_id`, `report_name`, `model_type`, `definition`, optional user-confirmed `resolutions`, `report_desc`, `cache_seconds`, `query_duration_ms`, and `dashboard_ids`. `--resolutions` is not supported with `--model-type tag`.

Output is the gateway envelope. `data` contains the created `report_id`, creation status, normalized `model_type`, AI QP `definition`, and optional resolution warnings.

Report creation and its `--validate` / `--dry-run` paths use the same compiler contract. `AI_QP_COMPILE_FAILED` preserves the full structured error array. No report is created on this failure; follow [`../metadata_resolution.md`](../metadata_resolution.md), keep the definition unchanged, and pass `--resolutions` only after user confirmation.

## SQL dynamic parameter shortest path

When a SQL report contains a `${...}` placeholder, define its saved default in the same AI-facing `definition`. Example:

```bash
ae-cli analysis report create --project-id <project_id> --report-name "Recent SQL" --model-type sql --definition '{"sql":"select * from events where ${PartDate:ds} limit 100","params":[{"name":"ds","type":"part_date","recent_day":"1-7","use_timezone":true}]}'
```

`use_timezone` is an optional boolean definition field only for `part_date`; it defaults to `false`. `true` makes that parameter use the query's effective timezone. It is a saved definition field, so change it through report create/update `--definition`, never through report-data `--sql-params`.

After creation, keep the `report_id` returned by this exact create response. To verify the report, query the saved default first with `analysis report-data run` and omit `--sql-params`; then make one second query with a value-only `--sql-params` override. Do not rebuild internal `sqlViewParams` or guess an ID.

After any successful report create, call `analysis-meta asset url-get` with that returned `report_id` and output its `markdown_link`.
