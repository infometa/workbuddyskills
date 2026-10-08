# analysis-meta datatable columns-get

Use when the user needs to get columns for a project table reference.

Do not use it to read table rows or infer a table reference; discover the exact table first and use a data query for row values.

Command:

```bash
ae-cli analysis-meta datatable columns-get --project-id <project_id> --table-ref <table_ref>
ae-cli analysis-meta datatable columns-get --dry-run
```

Capability id: `metadata.data_table.columns_get`.

Input sends `project_id`, `table_ref`.

Output contains resolved `data.table_ref` and `data.columns[]` from SQL IDE metadata.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-ref` | Yes | Project table reference. |
