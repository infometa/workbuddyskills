# system project-usage list

Use when the user needs to list project storage and usage statistics in a bounded time range.

Do not use it outside the system project-usage operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system project-usage list --company-id <company-id> --start-time <start-time> --end-time <end-time>
```

Capability id: `system.project_usage.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--start-time` | Yes | Inclusive ISO date/time lower bound. |
| `--end-time` | Yes | Inclusive ISO date/time upper bound. |
| `--fields` | No | Optional snake_case result field projection JSON array. |
| `--limit` | No | Page size. Default and maximum depend on the capability schema. |
| `--offset` | No | Zero-based result offset. |
| `--sort-by` | No | Sort field. |
| `--sort-order` | No | Sort direction. |
