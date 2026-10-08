# system role-user list

Use when the user needs to list users assigned to a company role.

Do not use it outside the system role-user operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system role-user list --company-id <company-id> --role-name <role-name>
```

Capability id: `system.role_user.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--role-name` | Yes | Role name. |
