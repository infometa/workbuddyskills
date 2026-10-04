# system usage-trend query

Use when the user needs to query a bounded company or project usage trend.

Do not use it outside the system usage-trend operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system usage-trend query --company-id <company-id> --start-time <start-time> --end-time <end-time> --metric <metric> --time-granularity <time-granularity>
```

Capability id: `system.usage_trend.query`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--start-time` | Yes | Inclusive ISO date/time lower bound. |
| `--end-time` | Yes | Inclusive ISO date/time upper bound. |
| `--metric` | Yes | Supported usage metric; apollo_token is not available. |
| `--time-granularity` | Yes | Aggregation granularity. |
| `--scope` | No | Aggregation scope. |
| `--project-ids` | No | Project ID JSON array; required for project scope. |
| `--data-type` | No | Optional event-volume data type. |
