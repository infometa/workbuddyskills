# analysis-governance rule delete

Use when the user needs to delete an asset governance rule through the capability gateway.

Do not use it to disable a rule or with a guessed ID; resolve the saved rule, dry-run the final deletion, and require explicit confirmation.

Command:

```bash
ae-cli analysis-governance rule delete --project-id <project_id> --payload '{}' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-governance rule delete --project-id <project_id> --payload '{}' --yes
```

Capability id: analysis_meta.asset_rule.delete.

Input sends project_id, payload, rule_id. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data.deleted` reports whether the identified rule was deleted; `false` must not be presented as a successful deletion.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --rule-id | No | Rule ID; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
