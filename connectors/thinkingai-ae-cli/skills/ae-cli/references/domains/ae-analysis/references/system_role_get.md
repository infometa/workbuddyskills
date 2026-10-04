# system role get

Use when the user needs to get one company role.

Do not use it outside the system role operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system role get --company-id <company-id> --role-name <role-name>
```

Capability id: `system.role.get`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--role-name` | Yes | Role name. |
