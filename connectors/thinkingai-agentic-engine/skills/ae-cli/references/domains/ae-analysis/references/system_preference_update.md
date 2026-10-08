# system preference update

Use when the user needs to update typed company navigation preference.

Do not use it outside the system preference operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system preference update --company-id <company-id> --navigation-permission-hide <true_or_false>
```

Capability id: `system.preference.update`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--navigation-permission-hide` | Yes | Hide navigation entries without permission. |
