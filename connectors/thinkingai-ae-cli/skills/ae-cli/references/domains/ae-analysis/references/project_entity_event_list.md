# project entity-event list

Use when the user needs to list entity mappings for events.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project entity-event list --project-id <project_id> --event-names <event_names>
ae-cli project entity-event list --dry-run --project-id <project_id>
```

Capability id: `project.entity_event.list`.

Input sends `project_id`, `event_names`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-names` | No | Optional event names JSON array to resolve entity mappings for. |
