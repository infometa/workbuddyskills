# system member-mfa unbind

Use when the user needs to unbind one member MFA enrollment.

Do not use it outside the system member-mfa operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system member-mfa unbind --dry-run --company-id <company-id> --login-name <login-name>
ae-cli system member-mfa unbind --company-id <company-id> --login-name <login-name> --yes
```

Capability id: `system.member_mfa.unbind`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--login-name` | Yes | Target member login name. |
