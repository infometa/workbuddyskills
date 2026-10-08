# system ops-alert-contact list

Use when the user needs to list sanitized operations-alert contacts.

Do not use it outside the system ops-alert-contact operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system ops-alert-contact list --company-id <company-id>
```

Capability id: `system.ops_alert_contact.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--limit` | No | Page size. Default: 50, max: 200. |
| `--offset` | No | Zero-based result offset. |
