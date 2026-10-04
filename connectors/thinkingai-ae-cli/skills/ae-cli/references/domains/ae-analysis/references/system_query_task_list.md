# system query-task list

Use when the user needs to list query-monitor tasks within a mandatory bounded time range.

Do not use it outside the system query-task operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-task options --company-id <company_id>
ae-cli system query-task list --company-id <company_id> --start-time '2026-07-24 00:00:00' --end-time '2026-07-24 23:59:59' --status-codes '[4]' --content-codes '[101]' --task-type-codes '[6]' --project-ids '[123]'
```

Capability id: `system.query_task.list`.

Always run `query-task options` first and select codes from its returned status, content type, task type, project/workspace, and cluster mappings. Do not guess numeric codes.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--start-time` | Yes | Inclusive ISO date/time lower bound. |
| `--end-time` | Yes | Inclusive ISO date/time upper bound. |
| `--project-ids` | No | Project ID JSON array. |
| `--space-codes` | No | Project space-code JSON array. |
| `--status-codes` | Yes | Task status-code JSON array. |
| `--content-codes` | Yes | Query content-code JSON array. |
| `--task-type-codes` | Yes | Query task-type-code JSON array. |
| `--cluster-names` | No | Optional cluster-name JSON array. |
| `--limit` | No | Maximum returned tasks. Default: 100, max: 1000. |
| `--offset` | No | Zero-based result offset. |
| `--fields` | No | Optional snake_case result field projection JSON array. |
