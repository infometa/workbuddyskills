# system third-party-login list

Use when the user needs to list sanitized third-party login configurations.

Do not use it outside the system third-party-login operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system third-party-login list --company-id <company-id>
```

Capability id: `system.third_party_login.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
