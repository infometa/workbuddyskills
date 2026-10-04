# project entity delete

Use when the user needs to delete an analysis entity.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project entity delete --project-id <project_id> --entity-id <entity_id>
ae-cli project entity delete --dry-run --project-id <project_id> --entity-id <entity_id>
```

Capability id: `project.entity.delete`.

Input sends `project_id`, `entity_id`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--entity-id` | Yes | Analysis entity ID. |
