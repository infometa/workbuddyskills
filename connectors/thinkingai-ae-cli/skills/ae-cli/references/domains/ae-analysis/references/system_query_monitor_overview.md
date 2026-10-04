# system query-monitor overview

Use when the user needs to get bounded query queue and resource-monitor charts.

Do not use it outside the system query-monitor operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-monitor overview --company-id <company-id> --cluster-names <cluster-names_json>
```

Capability id: `system.query_monitor.overview`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--duration-minutes` | No | Monitoring duration in minutes. Default: 60. |
| `--project-ids` | No | Project ID JSON array. |
| `--space-codes` | No | Project space-code JSON array. |
| `--cluster-names` | Yes | Query cluster-name JSON array. |
| `--point-interval-seconds` | No | Chart sample interval seconds. Default: 5. |
