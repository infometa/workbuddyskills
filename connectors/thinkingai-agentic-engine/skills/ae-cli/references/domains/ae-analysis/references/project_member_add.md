# project member add

Use when the user needs to add project members.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member add --project-id <project_id> --payload <payload> --type <type>
ae-cli project member add --dry-run --project-id <project_id> --payload <payload> --type <type>
```

Capability id: `project.member.add`.

Input sends `project_id`, `payload`, `type`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Member add payload. Must include user_roles array matching UserRolePo in snake_case. |
| `--type` | Yes | Add type accepted by ProjMemberAddTypeEnum. |
