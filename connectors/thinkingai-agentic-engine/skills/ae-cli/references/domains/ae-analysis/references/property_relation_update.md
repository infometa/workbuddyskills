# analysis-meta property relation-update

Use when the user needs to update property type, connection relation, or event mapping.

Do not use it for display-name/remark-only edits; use `property update`. Choose the same table type and payload variant as the existing property.

Command:

```bash
ae-cli analysis-meta property relation-update --project-id <project_id> --table-type event --payload '{"prop_name":"amount","select_type":"number","super_event_ids":[<event_id>]}'
ae-cli analysis-meta property relation-update --dry-run
```

Capability id: `metadata.property.relation_update`.

Input sends `project_id`, `table_type`, `payload`.

Output is a successful gateway envelope with no business data. Read back with `property get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--payload` | Yes | Complete event/user property object in the same shape documented by `property create`; relation/source fields replace the current definition rather than patching one nested field. |
