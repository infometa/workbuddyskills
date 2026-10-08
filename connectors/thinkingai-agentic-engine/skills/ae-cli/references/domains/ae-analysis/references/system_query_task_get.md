# system query-task get

Use when the user needs to get a sanitized query-monitor task detail.

Do not use it outside the system query-task operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-task get --company-id <company-id> --task-id <task-id>
```

Capability id: `system.query_task.get`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--task-id` | Yes | Query-monitor task ID. |
| `--sql-max-chars` | No | Maximum returned SQL characters. |
