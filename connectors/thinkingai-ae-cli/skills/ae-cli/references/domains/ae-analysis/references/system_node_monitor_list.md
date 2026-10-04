# system node-monitor list

Use when the user needs to list sanitized cluster node usage.

Do not use it outside the system node-monitor operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system node-monitor list --company-id <company-id>
```

Capability id: `system.node_monitor.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--limit` | No | Page size. Default: 50, max: 200. |
| `--offset` | No | Zero-based result offset. |
| `--fields` | No | Optional snake_case result field projection JSON array. |
