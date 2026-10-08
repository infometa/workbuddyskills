# analysis-meta datatable version-list

Use when the user needs to list data table historical versions.

Do not use it for one version's full definition or table row history; use `datatable version-get` for the selected metadata version.

Command:

```bash
ae-cli analysis-meta datatable version-list --project-id <project_id> --datatable-id <datatable_id> --limit 50 --offset 0
ae-cli analysis-meta datatable version-list --dry-run
```

Capability id: `metadata.data_table_version.list`.

Input sends `project_id`, `datatable_id`, `limit`, and `offset`.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--datatable-id` | Yes | Data table ID. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |
