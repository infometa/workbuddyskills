# analysis query create-result-cluster

Save the user or custom-entity population behind one selected synchronous-preview cell as that subject's reusable result cluster.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md) first. The selected metric/action must advertise `create_result_cluster`. `EVENT_LIST` and `NONE` analysis angles cannot be saved as a result cluster.

## Command

```bash
ae-cli analysis query create-result-cluster \
  --project-id <project_id> \
  --query-context-id <sync_preview_query_context_id> \
  [--source '{"report_id":1001}'] \
  --coordinate '<merged returned row/column/metric coordinate>' \
  --cluster-name <unique_name> \
  [--display-name <display_name>] \
  [--zone-offset 8] \
  [--timeout-seconds 180]
```

## Input rules

- `--project-id` must be the project used by the synchronous preview and must match the project stored by `query_context_id`.
- `--query-context-id`, `--source`, and all coordinate fragments must come from the same synchronous `adhoc run`, `report-data run`, or `dashboard-report-data run` response.
- Call `analysis query-context get`, match the desired visible row and column in its `source.drilldown.row_options`/`column_options`, select the correct metric option, and shallow-merge only their `coordinate` fragments.
- Never pass `target_id`, raw QP, display-only dates, option presentation fields, or data from an export/download. Exports do not create query contexts.
- `--cluster-name` must be unique in the project, start with a lowercase letter, contain only lowercase letters, digits, and underscores, and be at most 24 characters. This legacy result-cluster path is stricter than ordinary cluster creation.
- `--display-name`, when provided, must be at most 80 characters.

The saved cluster subject is `source.drilldown.subject` or the selected event metric's `subject`. `USER_LIST` creates a user result cluster. `ENTITY_LIST` creates a result cluster for that custom entity; do not relabel it as a user cluster.

The response must contain the backend cluster creation result. A successful capability envelope without a created cluster identifier/result is not sufficient evidence of completion.
