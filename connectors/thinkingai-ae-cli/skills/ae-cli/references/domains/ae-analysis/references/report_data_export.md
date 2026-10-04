# analysis report-data export

Submit saved report data as a downloadable async artifact. It covers the 12 analysis report models from `ai_models.md` plus tag report data; tags are report-data only and are not ad-hoc `model_type` values.

Typical closed loop: verify saved report definition -> resolve exact filter values and physical query route when needed -> submit export -> preserve the returned run/artifact pair -> inspect to a successful terminal state -> download and verify artifact content.

Before adding overrides, call `analysis report get` for every report. The model matrix is the same as `report-data run`: SQL accepts only saved `definition.params` names through `--sql-params`; non-SQL analysis models accept filters/group/time overrides; tag executes its saved definition. Never put generic overrides and `--sql-params` in one homogeneous-model request.

Routing: read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing this `export` command instead of `report-data run`.

Do not use this command for bounded inline previews; use `report-data run` when the requested result fits the sync data retrieval rule.

Command:

```bash
# Non-SQL analysis report
ae-cli analysis report-data export --project-id <project_id> --report-ids '[1001]' --filters '{"relation":"and","items":[{"field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}]}' --artifact-format jsonl

# SQL report
ae-cli analysis report-data export --project-id <project_id> --report-ids '[2001]' --sql-params '[{"name":"platform","value":"ios"}]' --artifact-format jsonl

# Global cross-cluster export for a supported non-SQL report
ae-cli analysis report-data export --project-id <project_id> --report-ids '[1001]' --cluster-query-scope GLOBAL --artifact-format jsonl
```

Input also accepts optional `cluster_query_scope` and conditional `slave_cluster_id`. Omit both for current-self data. Resolve allowed physical routes with `analysis query-cluster list`; SQL reports reject `GLOBAL`. Async export has no inline row limit. Runtime defaults to and is capped at 21600 seconds (6 hours); cancel earlier with `analysis query cancel --run-id <run_id>`.

The downloaded report-data artifact contains report rows and per-report markers, not `actual_cluster_query_scope` metadata. Therefore resolve an allowed route first, keep the submitted scope/ID with the run record, and do not infer route from row contents.

Timezone contract is identical to `report-data run`: omit `--zone-offset` to match the current user's report UI timezone (falling back to the project default); use an enabled integer from `-12` through `14` for a fixed UTC offset; use `--zone-offset 99` for local-time mode, where rows are not converted to one fixed UTC offset. `99` is a mode identifier, not `UTC+99`, and the option is not persisted.

Override model:

- `filters`: AI-facing intent object `{relation:"and|or", items:[{field:{name,type?}, operator, values?}]}`. `field.type` supports `event_property`, `user_property`, `cluster`, and `tag`; omit it only when the field name is unambiguous. Use field names from `analysis report get` definition output or metadata commands. Do not pass raw QP fields such as `taFilters`, `junctionKind`, `columnName`, `tableType`, or `selectType`.
- `group-by`: AI-facing intent array `[{field:{name,type?}}]`. Use the same field model as report definitions. Do not pass raw `TaGroupByVo`. Time granularity is controlled by `--time-granularity`, not by `--group-by`.
- `sql-params`: SQL report dynamic parameter value overrides. First read `analysis report get`; every name must exist in every target SQL report's `definition.params`. Time fields require a saved `part_date` or time parameter. Send only override values; do not send definition fields such as `type`, `options`, or `use_timezone`.

Mixed-model export batches are best-effort rather than rejected only for being mixed. Prefer one model per overridden export because artifact formats cannot surface submission-time warnings as prominently as inline `meta.warnings`.

Output is the gateway envelope. `data` contains opaque `run_id` and `artifact_id`, lifecycle status and expiration, and effective timeout/deadline fields. Exports do not create `query_context_id`. Inspect/download through the dedicated CLI commands using the IDs.

Keep `run_id` and `artifact_id` from the same export response. Inspect that exact `run_id`, then download only that paired `artifact_id`; never combine IDs from different exports.

An empty artifact is a successful query and means the requested time range has no data. If every requested report explicitly fails, the run reaches `FAILED` instead of completing an error-only artifact. Mixed exports may contain explicit per-report error markers alongside successful report data.

Never use the export response or downloaded rows as a drilldown/result-cluster source. Run a bounded synchronous preview containing the desired cell first.
