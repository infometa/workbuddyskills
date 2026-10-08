# project entity list

Use when the user needs to list analysis entities in a project.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project entity list --project-id <project_id> --query <query> --fields <fields> --limit <limit> --offset <offset> --event-name <event_name>
ae-cli project entity list --dry-run --project-id <project_id>
```

Capability id: `project.entity.list`.

Input sends `project_id`, `query`, `fields`, `limit`, `offset`, `event_name`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--query` | No | Optional keyword filter. |
| `--fields` | No | Optional snake_case fields to return. |
| `--limit` | No | Optional page size. Default: 50, maximum: 200. |
| `--offset` | No | Optional page offset. Default: 0. |
| `--event-name` | No | Optional event name. When present, return entities related to the event. |
