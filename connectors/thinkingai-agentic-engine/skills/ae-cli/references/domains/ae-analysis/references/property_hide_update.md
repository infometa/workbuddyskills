# analysis-meta property hide-update

Use when the user needs to batch hide or show properties.

Do not use it for deletion: this keeps the property but changes metadata visibility. Keep all targets in one table type.

Command:

```bash
ae-cli analysis-meta property hide-update --project-id <project_id> --table-type event --prop-names '["amount"]' --is-hide true
ae-cli analysis-meta property hide-update --dry-run
```

Capability id: `metadata.property.hide_update`.

Input sends `project_id`, `table_type`, `prop_names`, `is_hide`.

Output is a successful gateway envelope with no business data. Verify with `property list|get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--prop-names` | Yes | Property names JSON array, or a JSON string accepted by common-service. |
| `--is-hide` | Yes | Whether to hide the properties. |
