# metadata property bind-existing-dimension-table

> Capability id: `metadata.property.bind_existing_dimension_table` · Domain: `metadata`.

## Command

```bash
ae-cli metadata property bind-existing-dimension-table --project-id <project_id> --property-name <name> --property-scope user --data-table-id <id>
ae-cli metadata property bind-existing-dimension-table --project-id <project_id> --property-name <name> --property-scope event --data-table-id <id> --dict-columns '["display_name"]'
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--property-name` | Yes | Property technical name. |
| `--property-scope` | Yes | Property owner table, for example `event` or `user`. |
| `--data-table-id` | Yes | Existing dimension data table ID. |
| `--timestamp-join-format` | No | Timestamp join format. |
| `--dict-columns` | No | Dictionary column names JSON array. The CLI converts each string to the canonical `{"column_name":"..."}` object required by the capability. |

## Decision Rules

- Confirm the property with `analysis-meta property get` or `analysis-meta property list`.
- Confirm the data table with `metadata data-table get`.
- This is an ordinary `write` command and does not require CLI confirmation.
