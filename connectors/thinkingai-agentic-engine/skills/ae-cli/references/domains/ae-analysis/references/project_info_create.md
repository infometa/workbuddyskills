# project info create

Use when the user needs to create a project without exposing unsupported avatar fields.

Do not use it outside the project info operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli project info create --company-id <company-id> --project-name <project-name>
```

Capability id: `project.info.create`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--project-name` | Yes | Project name. |
| `--load-history` | No | Load historical data. Default: false. |
| `--owner-user-id` | No | Optional owner user ID. |
| `--project-remark` | No | Optional project remark. |
