# system preference get

Use when the user needs to get typed company preferences exposed to CLI.

Do not use it outside the system preference operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system preference get --company-id <company-id>
```

Capability id: `system.preference.get`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
