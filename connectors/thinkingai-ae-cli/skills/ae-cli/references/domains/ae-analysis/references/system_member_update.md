# system member update

Use when the user needs to update a company member display name.

Do not use it outside the system member operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system member update --company-id <company-id> --target-open-id <target-open-id> --user-name <user-name>
```

Capability id: `system.member.update`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target member open ID. |
| `--user-name` | Yes | New display name. |
