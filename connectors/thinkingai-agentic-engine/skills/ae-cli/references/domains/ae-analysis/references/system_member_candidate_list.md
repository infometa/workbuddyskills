# system member-candidate list

Use when the user needs to resolve candidate company members by login name.

Do not use it outside the system member-candidate operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system member-candidate list --company-id <company-id> --login-names <login-names_json>
```

Capability id: `system.member_candidate.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--login-names` | Yes | Login-name JSON array. |
