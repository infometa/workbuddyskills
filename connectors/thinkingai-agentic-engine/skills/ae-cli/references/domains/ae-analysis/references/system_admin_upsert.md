# system admin upsert

Use when the user needs to create or update company system-administrator assignments.

Do not use it outside the system admin operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system admin upsert --dry-run --company-id <company-id> --admins <admins_json>
ae-cli system admin upsert --company-id <company-id> --admins <admins_json> --yes
```

Capability id: `system.admin.upsert`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--admins` | Yes | Administrator array with target_user_id and function_names. |
