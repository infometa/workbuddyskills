# system query-task cancel

Use when the user needs to cancel one running query-monitor task by task_id.

Do not use it outside the system query-task operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-task cancel --dry-run --company-id <company-id> --task-id <task-id>
ae-cli system query-task cancel --company-id <company-id> --task-id <task-id> --yes
```

Capability id: `system.query_task.cancel`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--task-id` | Yes | Query-monitor task ID, not a CLI run_id. |
