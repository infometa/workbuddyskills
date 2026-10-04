# system smtp get

Use when the user needs to get sanitized company SMTP configuration.

Do not use it outside the system smtp operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system smtp get --company-id <company-id>
```

Capability id: `system.smtp.get`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
