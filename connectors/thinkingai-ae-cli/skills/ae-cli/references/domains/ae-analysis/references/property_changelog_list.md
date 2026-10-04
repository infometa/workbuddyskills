# analysis-meta property changelog-list

Use when the user needs to list property metadata change logs.

Do not use it for the current property definition or historical data values; use `property get` or an analysis query.

Command:

```bash
ae-cli analysis-meta property changelog-list --project-id <project_id> --table-type <table_type> --prop-name <prop_name>
ae-cli analysis-meta property changelog-list --dry-run
```

Capability id: `metadata.property.changelog_list`.

Input sends `project_id`, `table_type`, `prop_name`.

Output `data.changelogs[]` contains metadata change records for the property.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--prop-name` | Yes | Property column name. |
