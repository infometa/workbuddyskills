# system smtp delete

Use when the user needs to delete company SMTP configuration.

Do not use it outside the system smtp operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system smtp delete --dry-run --company-id <company-id>
ae-cli system smtp delete --company-id <company-id> --yes
```

Capability id: `system.smtp.delete`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
