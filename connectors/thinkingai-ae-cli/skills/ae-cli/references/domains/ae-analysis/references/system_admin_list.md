# system admin list

Use when the user needs to list company system administrators.

Do not use it outside the system admin operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system admin list --company-id <company-id>
```

Capability id: `system.admin.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
