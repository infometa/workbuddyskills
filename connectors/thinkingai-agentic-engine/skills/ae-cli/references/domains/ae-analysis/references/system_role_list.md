# system role list

Use when the user needs to list company roles.

Do not use it outside the system role operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system role list --company-id <company-id>
```

Capability id: `system.role.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--query` | No | Optional keyword filter. |
| `--limit` | No | Page size. Default and maximum depend on the capability schema. |
| `--offset` | No | Zero-based result offset. |
