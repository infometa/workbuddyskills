# system member add

Use when the user needs to add one or more company members as one atomic batch.

Do not use it to add existing company members to a project; use the project member flow instead. Validate candidate login names first with `system member-candidate list`.

Command:

```bash
ae-cli system member add --dry-run --company-id <company_id> --members @members.json
ae-cli system member add --company-id <company_id> --members @members.json
```

Capability id: `system.member.add`.

`members` must be a non-empty JSON array. Every item requires `login_name` and `user_name`. If any item is invalid, the entire batch is rolled back.

The successful response returns each generated one-time `initial_password`. Handle it as a secret, deliver it only to the intended member, and do not persist it in logs or reports.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--members` | Yes | Non-empty member JSON array containing `login_name` and `user_name`. |
