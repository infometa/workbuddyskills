# system mfa get

Use when the user needs to get the company MFA enforcement state.

Do not use it outside the system mfa operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system mfa get --company-id <company-id>
```

Capability id: `system.mfa.get`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
