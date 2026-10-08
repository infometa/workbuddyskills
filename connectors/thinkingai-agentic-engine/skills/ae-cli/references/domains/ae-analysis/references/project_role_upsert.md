# project role upsert

Use when the user needs to create or update a project role.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project role upsert --project-id <project_id> --payload <payload>
ae-cli project role upsert --dry-run --project-id <project_id> --payload <payload>
```

Capability id: `project.role.upsert`.

Input sends `project_id`, `payload`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Role save payload matching RoleSaveRequestDTO in snake_case. |
