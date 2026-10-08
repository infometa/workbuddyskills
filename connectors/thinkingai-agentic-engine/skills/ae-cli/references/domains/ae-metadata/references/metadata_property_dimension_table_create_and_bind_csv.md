# metadata property create-and-bind-csv-dimension-table

> Capability id: `metadata.property.create_and_bind_csv_dimension_table` · Domain: `metadata`.

## Command

```bash
ae-cli metadata property create-and-bind-csv-dimension-table --project-id <project_id> --property-name <name> --property-scope user --input-file-id <input_file_id> --data-table-name datatable_<project_id>_<name> --columns '<columns_json>'
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--property-name` | Yes | Property technical name. |
| `--property-scope` | Yes | Property owner table, for example `event` or `user`. |
| `--input-file-id` | Yes | ID returned by `analysis input-file upload`. |
| `--data-table-name` | No | Optional technical data table name. If supplied, use `datatable_<project_id>_<name>`. |
| `--display-name` | No | Human-readable table name. |
| `--description` | No | Table description. |
| `--columns` | No | Column definitions JSON array. Preferred fields are `column_name`, `select_type`, and `column_desc`; CLI also accepts `name`, `type`, and `display_name` aliases. |
| `--timestamp-join-format` | No | Timestamp join format. |
| `--dict-columns` | No | Dictionary column names JSON array. |

## Decision Rules

- Discover the purpose with `analysis input-file purpose list`, then upload the CSV with `analysis input-file upload --purpose data_table.csv`.
- Do not invent `input_file_id`; use the value returned by upload.
- If you provide `--data-table-name`, it must include the project segment, for example `datatable_2_user_dict`.
- Use this one-step command when the user wants a new CSV dimension table bound to a property.
- This is an ordinary `write` command and does not require CLI confirmation.
