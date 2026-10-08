# system mfa update

Use when the user needs to enable or disable company MFA enforcement.

Do not use it outside the system mfa operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system mfa update --dry-run --company-id <company-id> --enabled <true_or_false>
ae-cli system mfa update --company-id <company-id> --enabled <true_or_false> --yes
```

Capability id: `system.mfa.update`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--enabled` | Yes | Target MFA enforcement state. |
