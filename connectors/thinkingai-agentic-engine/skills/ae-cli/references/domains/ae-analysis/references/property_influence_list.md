# analysis-meta property influence-list

Use when the user needs to list assets affected by property changes.

Do not use it as mutation or as proof that deletion is safe without reviewing every returned dependency.

Command:

```bash
ae-cli analysis-meta property influence-list --project-id <project_id> --table-type <table_type> --prop-name <prop_name>
ae-cli analysis-meta property influence-list --dry-run
```

Capability id: `metadata.property.influence_list`.

Input sends `project_id`, `table_type`, `prop_name`.

Output is the snake_case property influence object returned by Common, including dependent assets and operation constraints.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--prop-name` | Yes | Property column name. |
