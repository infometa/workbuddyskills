# system member-status update

Use when the user needs to lock or reactivate a company member.

Do not use it outside the system member-status operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system member-status update --dry-run --company-id <company-id> --target-open-id <target-open-id> --status <status>
ae-cli system member-status update --company-id <company-id> --target-open-id <target-open-id> --status <status> --yes
```

Capability id: `system.member_status.update`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target member open ID. |
| `--status` | Yes | Target status. |
