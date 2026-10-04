# analysis query-context get

Read the full selectable coordinate options for one source from a bounded synchronous analysis preview.

The primary `adhoc run`, `report-data run`, or `dashboard-report-data run` response intentionally returns only a compact `sources[]` summary. Call this command only when that response contains `query_context_id`, `query_context_options_capability_id=analysis.query.context_get`, and an advertised follow-up action.

## Command

```bash
ae-cli analysis query-context get \
  --project-id <project_id> \
  --query-context-id <query_context_id> \
  [--source '{"report_id":1001}']
```

`--project-id` must match the project stored by the context. For a context with multiple sources, copy exactly one `report_id` or `chart_id` selector from the compact primary response. Omit `--source` only when the context contains one source.

The returned `source.drilldown` contains the complete `row_options`, `column_options`, and `metric_options` for the original synchronous preview. Select options and shallow-merge only their `coordinate` fragments as described in [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md). The command never reruns or expands the query and never makes export rows selectable.

If the context is missing, expired, owned by another user, belongs to another project, or the caller no longer has source permission, the command fails. Do not reconstruct coordinates from display text.
