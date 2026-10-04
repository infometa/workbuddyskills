# system usage overview

Use when the user needs to get the current company system-usage summary.

Do not use it outside the system usage operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system usage overview --company-id <company-id>
```

Capability id: `system.usage.overview`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
