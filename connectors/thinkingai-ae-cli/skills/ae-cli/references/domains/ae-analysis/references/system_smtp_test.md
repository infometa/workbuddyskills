# system smtp test

Use when the user needs to send one SMTP test using the saved configuration.

Do not use it outside the system smtp operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system smtp test --company-id <company-id> --receiver <receiver>
```

Capability id: `system.smtp.test`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--receiver` | Yes | Test email receiver. |
