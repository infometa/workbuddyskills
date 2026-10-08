# system member delete

Use when the user needs to delete a company member after every project membership and owned asset has been cleared or handed over.

Do not use it to remove a member from one project; use the project member flow instead.

Command:

```bash
ae-cli system member delete --dry-run --company-id <company_id> --target-user-id <target_user_id>
ae-cli system member delete --company-id <company_id> --target-user-id <target_user_id> --yes
```

Capability id: `system.member.delete`.

Run `--dry-run` first and verify the company, target member, project membership, and asset-protection result. Wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. A protection rejection is not retryable until the member's project membership or owned assets change.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-user-id` | Yes | Target member user ID. |
