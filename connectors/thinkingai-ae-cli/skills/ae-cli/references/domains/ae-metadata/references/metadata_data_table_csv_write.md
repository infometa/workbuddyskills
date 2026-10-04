# metadata data-table csv-write

> Capability id: `metadata.data_table.csv_write` · Domain: `metadata`.

## Command

```bash
ae-cli metadata data-table csv-write --project-id <project_id> --operation create --input-file-id <input_file_id> --data-table-name datatable_<project_id>_<name> --columns '<columns_json>'
ae-cli metadata data-table csv-write --project-id <project_id> --operation incremental_update --data-table-id <id> --input-file-id <input_file_id>
ae-cli metadata data-table csv-write --project-id <project_id> --operation replace_update --data-table-id <id> --input-file-id <input_file_id>
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--operation` | Yes | `create`, `incremental_update`, or `replace_update`. |
| `--input-file-id` | Yes | ID returned by `analysis input-file upload`. |
| `--data-table-id` | For updates | Existing data table ID. |
| `--data-table-name` | No | Optional technical data table name. If supplied, use `datatable_<project_id>_<name>`. |
| `--display-name` | No | Human-readable table name. |
| `--description` | No | Table description. |
| `--columns` | No | Column definitions JSON array. Preferred fields are `column_name`, `select_type`, and `column_desc`; CLI also accepts `name`, `type`, and `display_name` aliases. |

## Decision Rules

- Discover the purpose with `analysis input-file purpose list`, then upload the CSV with `analysis input-file upload --purpose data_table.csv`.
- Do not invent `input_file_id` or `data_table_id`; use upload/list outputs.
- If you provide `--data-table-name`, it must include the project segment, for example `datatable_2_orders`.
- This is an ordinary `write` command and does not require CLI confirmation.
