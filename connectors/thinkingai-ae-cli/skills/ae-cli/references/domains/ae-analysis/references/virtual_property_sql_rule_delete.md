# analysis-meta virtual-property sql-rule-delete

Use when the user needs to delete or revoke SQL virtual property rule.

Do not use it for physical/super properties. Omit `--operation` for permanent deletion; pass `revoke` only when the user explicitly wants revocation instead.

Command:

```bash
ae-cli analysis-meta virtual-property sql-rule-delete --project-id <project_id> --v-prop-id <v_prop_id> --operation <operation> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-meta virtual-property sql-rule-delete --project-id <project_id> --v-prop-id <v_prop_id> --operation <operation> --yes
```

Capability id: `metadata.virtual_property.sql_rule_delete`.

Input sends `project_id`, `v_prop_id`, `operation`.

Output is a successful gateway envelope with no business data.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--v-prop-id` | Yes | Virtual property ID. |
| `--operation` | No | Delete operation. Use revoke to revoke instead of delete. |
