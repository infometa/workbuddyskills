# system admin-function update

Use when the user needs to replace functions assigned to a system administrator.

Do not use it outside the system admin-function operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system admin-function update --dry-run --company-id <company-id> --target-open-id <target-open-id> --function-names <function-names_json>
ae-cli system admin-function update --company-id <company-id> --target-open-id <target-open-id> --function-names <function-names_json> --yes
```

Capability id: `system.admin_function.update`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target member open ID. |
| `--function-names` | Yes | Complete function-name JSON array. |
