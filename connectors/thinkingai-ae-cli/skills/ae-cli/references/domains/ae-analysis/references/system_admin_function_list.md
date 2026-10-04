# system admin-function list

Use when the user needs to list functions assigned to a system administrator.

Do not use it outside the system admin-function operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system admin-function list --company-id <company-id> --target-open-id <target-open-id>
```

Capability id: `system.admin_function.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target member open ID. |
