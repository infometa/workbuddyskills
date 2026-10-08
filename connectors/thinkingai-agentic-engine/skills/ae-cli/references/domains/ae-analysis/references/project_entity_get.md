# project entity get

Use when the user needs to get one analysis entity.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project entity get --project-id <project_id> --entity-id <entity_id>
ae-cli project entity get --dry-run --project-id <project_id> --entity-id <entity_id>
```

Capability id: `project.entity.get`.

Input sends `project_id`, `entity_id`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--entity-id` | Yes | Analysis entity ID. |
