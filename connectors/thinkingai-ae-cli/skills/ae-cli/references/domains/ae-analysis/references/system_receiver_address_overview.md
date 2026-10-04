# system receiver-address overview

Use when the user needs to get company receiver-address overview.

Do not use it outside the system receiver-address operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-address overview --company-id <company-id>
```

Capability id: `system.receiver_address.overview`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
