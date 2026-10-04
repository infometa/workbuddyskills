# metadata data-table property-bindings-update

> Capability id: `metadata.data_table.property_bindings_update` · Domain: `metadata`.

```bash
ae-cli metadata data-table property-bindings-update --project-id <project_id> --data-table-id <id> --bind-properties '<bind_json>'
ae-cli metadata data-table property-bindings-update --project-id <project_id> --data-table-id <id> --unbind-properties '<unbind_json>'
```

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--data-table-id` | Yes | Data table ID. |
| `--bind-properties` | No | Properties to bind JSON array. Each item includes `property_name` and `property_scope`. |
| `--unbind-properties` | No | Properties to unbind JSON array. Each item includes `property_name` and `property_scope`. |

This is a write command. Use the direct property dimension-table commands when binding a single property is the user-facing goal.
