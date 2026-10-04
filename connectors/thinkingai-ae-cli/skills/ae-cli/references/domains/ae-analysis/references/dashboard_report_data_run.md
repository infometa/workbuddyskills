# analysis dashboard-report-data run

Execute bounded inline dashboard report data queries. Dashboard report data follows report-data model coverage: the 12 analysis report models from `ai_models.md` plus tag report data.

Typical closed loop: find the dashboard -> inspect its dashboard context and reports -> resolve exact filter values when needed -> optionally resolve a physical query route -> run -> verify actual route and per-report warnings -> drill down through the returned report source.

Before the first data query for a selected dashboard, run `ae-cli analysis dashboard get` exactly once with the same `project_id` and `dashboard_id`. Preserve non-empty `location.folder_name`, `dashboard_name`, `remark`, and `notes[].note_title/description` as dashboard context for every report result in this dashboard query. A folder name such as `Campaign A` can provide business scope that a generic dashboard name such as `Base Data` does not. Treat notes as authored explanatory context, not as measured evidence. Do not repeat `dashboard get` for each report in the same continuous workflow unless the dashboard changes or the user explicitly requests a refresh.

Routing: read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing this `run` command instead of `dashboard-report-data export`.

Do not use this command for full, unknown-size, larger than the current runtime synchronous maximum, or long-running dashboard report data; use `dashboard-report-data export`.

The dashboard surface also applies its configured response payload row/character
caps after each model query. When that payload cap is smaller than the model
boundary, returned rows are trimmed to the payload cap and `has_more=true` is
based on that observed trim. This is a real dashboard-response truncation, not
a boundary guess. Direct `report-data run` does not apply the dashboard payload
cap.

Command:

```bash
ae-cli analysis dashboard-report-data run --project-id <project_id> --dashboard-id <dashboard_id> [--report-ids '[1,2]'] [--filters '{...}'] [--cluster-query-scope GLOBAL|SLAVE] [--slave-cluster-id <id>] [--preview-rows 100] [--timeout-seconds 180]
```

Cluster routing is optional. Omit it to follow the dashboard's saved physical-cluster configuration; this differs from report/ad-hoc current-self default. `GLOBAL` explicitly aggregates and `SLAVE` requires one ID returned by `analysis query-cluster list`. SQL dashboard reports reject effective `GLOBAL` and are reported as unsupported rather than silently queried elsewhere.

`--filters` uses the same AI-facing filter model as report data. The gateway resolves fields and compiles it to the dashboard backend filter. Do not pass a dashboard UI control dump or raw QP filter. Minimal shape:

```json
{"relation":"and","items":[{"field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}]}
```

Dashboard `filters`, `start_time`, and `end_time` do not apply to SQL reports. The query still succeeds and returns those SQL report results. Inspect `data.warnings[]`; `OVERRIDE_IGNORED_FOR_MODEL` contains the affected SQL `report_ids` and `ignored_fields`. To change SQL conditions, query the SQL report directly with `analysis report-data run` and saved `definition.params` through `--sql-params`.

Output is the gateway envelope. Verify `data.actual_cluster_query_scope`, optional `data.actual_slave_cluster_id`, and `data.cluster_query_scope_source`; `DASHBOARD_CONFIGURATION` means the caller omitted an explicit scope. When at least one report exposes a follow-up action, `data` also contains `query_context_id` and compact per-report action summaries. Detailed coordinate options are available through `analysis query-context get`; a fully non-drillable dashboard result omits query context.

An empty dashboard batch or report result with no rows is a successful query: it means the requested time range has no data. The command fails only when every returned report entry contains an explicit execution error. Mixed dashboard batches keep successful data and return `meta.partial`, counts, and per-report `meta.failures`.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md). Fetch the selected report source with `analysis query-context get` and merge only its returned coordinate fragments for the advertised action. Do not pass raw QP.
