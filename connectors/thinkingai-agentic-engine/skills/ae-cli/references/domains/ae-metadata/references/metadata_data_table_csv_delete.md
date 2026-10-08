# metadata data-table csv-delete

> Capability id: `metadata.data_table.csv_delete` · Domain: `metadata`.

```bash
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli metadata data-table csv-delete --project-id <project_id> --data-table-id <id> --yes
ae-cli metadata data-table csv-delete --project-id <project_id> --data-table-id <id> --dry-run
```

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--data-table-id` | Yes | CSV-backed data table ID. |

This is a write command. Confirm the table with `metadata data-table get` before deleting.
