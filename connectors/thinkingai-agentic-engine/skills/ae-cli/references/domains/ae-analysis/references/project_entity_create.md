# project entity create

Use when the user needs to create an analysis entity.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project entity create --project-id <project_id> --entity-name <entity_name> --column-name <column_name> --table-type <table_type> --order <order>
ae-cli project entity create --dry-run --project-id <project_id> --entity-name <entity_name> --column-name <column_name> --table-type <table_type>
```

Capability id: `project.entity.create`.

Input sends `project_id`, `entity_name`, `column_name`, `table_type`, `order`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--entity-name` | Yes | Entity display name. |
| `--column-name` | Yes | Property column name to bind. |
| `--table-type` | Yes | Main table type: 0 for event property, 1 for user property. |
| `--order` | No | Optional entity display order. |
