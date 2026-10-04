# analysis-meta datatable influence-list

Use when the user needs to list metadata and assets affected by data table deletion or column changes.

Do not use it as a delete command. It is a read-only dependency check before table/column mutation.

Command:

```bash
ae-cli analysis-meta datatable influence-list --project-id <project_id> --datatable-id <datatable_id>
ae-cli analysis-meta datatable influence-list --dry-run
```

Capability id: `metadata.data_table.influence_list`.

Input sends `project_id`, `datatable_id`.

Output includes `data.resources[]`, `data.continuable`, and `data.project_info` for the proposed table operation.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--datatable-id` | Yes | Data table ID. |
