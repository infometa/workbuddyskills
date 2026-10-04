# analysis-meta property update

Use when the user needs to update property display names and remarks.

Do not use it to change source/event relations or select type; use `property relation-update` with the complete definition.

Command:

```bash
ae-cli analysis-meta property update --project-id <project_id> --table-type <table_type> --prop-name <prop_name> --prop-desc <prop_desc> --prop-remark <prop_remark>
ae-cli analysis-meta property update --dry-run
```

Capability id: `metadata.property.update`.

Input sends `project_id`, `table_type`, `prop_name`, `prop_desc`, `prop_remark`.

Output is a successful gateway envelope with no business data. Read back with `property get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--prop-name` | Yes | Property column name. |
| `--prop-desc` | No | Property display name. |
| `--prop-remark` | No | Property remark. |
