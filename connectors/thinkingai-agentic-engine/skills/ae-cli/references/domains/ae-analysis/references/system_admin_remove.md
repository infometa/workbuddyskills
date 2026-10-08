# system admin remove

Use when the user needs to remove one company-scoped system administrator role.

Do not use it to delete the underlying member or to edit a normal company role.

Command:

```bash
ae-cli system admin remove --dry-run --company-id <company_id> --target-open-id <target_open_id>
ae-cli system admin remove --company-id <company_id> --target-open-id <target_open_id> --yes
```

Capability id: `system.admin.remove`.

Run `--dry-run` first and verify the company and target. The service rejects self-removal and removal of the last administrator. Wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Do not retry a self/last-administrator protection failure unchanged.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target administrator open ID. |
