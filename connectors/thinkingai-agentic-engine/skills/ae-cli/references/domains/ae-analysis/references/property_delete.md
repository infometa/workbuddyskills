# analysis-meta property delete

Use when the user needs to batch delete properties or virtual properties.

Do not use it before `property influence-list` is reviewed for every target, and do not mix event/user table types.

Command:

```bash
ae-cli analysis-meta property delete --project-id <project_id> --table-type event --prop-names '["amount"]' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-meta property delete --project-id <project_id> --table-type event --prop-names '["amount"]' --yes
```

Capability id: `metadata.property.delete`.

Input sends `project_id`, `table_type`, `prop_names`.

Output is a successful gateway envelope with no business data. Verify with `property list`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--prop-names` | Yes | Property names JSON array, or a JSON string accepted by common-service. |
