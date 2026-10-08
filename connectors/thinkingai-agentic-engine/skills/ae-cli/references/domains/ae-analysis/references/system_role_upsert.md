# system role upsert

Use when the user needs to create or update a company role and its function set.

Do not use it outside the system role operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system role upsert --dry-run --company-id <company-id> --role-desc <role-desc> --function-names <function-names_json>
ae-cli system role upsert --company-id <company-id> --role-desc <role-desc> --function-names <function-names_json> --yes
```

Capability id: `system.role.upsert`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--role-name` | No | Existing role name for update; omit when creating. |
| `--role-desc` | Yes | Role description. |
| `--function-names` | Yes | Complete function-name JSON array. |
