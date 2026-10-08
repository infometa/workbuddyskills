# system ops-alert-contact delete

Use when the user needs to delete an operations-alert contact.

Do not use it outside the system ops-alert-contact operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system ops-alert-contact delete --dry-run --company-id <company-id> --contact-id <contact-id>
ae-cli system ops-alert-contact delete --company-id <company-id> --contact-id <contact-id> --yes
```

Capability id: `system.ops_alert_contact.delete`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--contact-id` | Yes | Contact ID to delete. |
