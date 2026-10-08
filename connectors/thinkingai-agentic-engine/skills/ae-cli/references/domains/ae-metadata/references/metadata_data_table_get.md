# metadata data-table get

> Capability id: `metadata.data_table.get` · Domain: `metadata`.

## Command

```bash
ae-cli metadata data-table get --project-id <project_id> --data-table-id <id>
ae-cli metadata data-table get --project-id <project_id> --data-table-id <id> --include-preview true
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--data-table-id` | Yes | Data table ID from `metadata data-table list`. |
| `--include-preview` | No | Include preview rows when true. |

## Request Body

```json
{ "project_id": 1, "data_table_id": 42, "include_preview": true }
```
