# system third-party-login disable

Use when the user needs to disable a third-party login provider.

Do not use it outside the system third-party-login operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system third-party-login disable --dry-run --company-id <company-id> --login-type <login-type>
ae-cli system third-party-login disable --company-id <company-id> --login-type <login-type> --yes
```

Capability id: `system.third_party_login.disable`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--login-type` | Yes | Third-party login type. |
