# analysis-governance rule update

Use when the user needs to update an asset governance rule through the capability gateway.

Do not use it to create a new rule or guess a rule ID; resolve the existing rule with `rule-list` before updating its full definition.

Command:

```bash
ae-cli analysis-governance rule update --project-id <project_id> --payload '{}'
ae-cli analysis-governance rule update --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_rule.update.

Input sends project_id, payload, rule_id, rule_name, comment, rule. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` returns the updated `rule_id` and `updated=true`; a missing rule is an operation failure, not a create fallback.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --rule-id | No | Rule ID; required unless provided inside payload. |
| --rule-name | No | Rule name; required unless provided inside payload. |
| --comment | No | Rule comment. |
| --rule | No | Governance Filter JSON; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
