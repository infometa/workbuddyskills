# system role delete

Use when the user needs to delete a company role and optionally migrate its users.

Do not use it outside the system role operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system role delete --dry-run --company-id <company-id> --role-name <role-name>
ae-cli system role delete --company-id <company-id> --role-name <role-name> --yes
```

Capability id: `system.role.delete`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--role-name` | Yes | Role name. |
| `--new-role-name` | No | Replacement role for affected users. |
