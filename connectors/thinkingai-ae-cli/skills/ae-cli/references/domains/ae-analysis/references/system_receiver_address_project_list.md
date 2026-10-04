# system receiver-address project-list

Use when the user needs to list project receiver-address overrides.

Do not use it outside the system receiver-address operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-address project-list --company-id <company-id>
```

Capability id: `system.receiver_address.project_list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
