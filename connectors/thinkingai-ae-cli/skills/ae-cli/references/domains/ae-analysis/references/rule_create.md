# analysis-governance rule create

Use when the user needs to create an asset governance rule through the capability gateway.

Do not use it when a matching saved rule already exists; list rules first and use `rule-update` for an existing `rule_id`.

Command:

```bash
ae-cli analysis-governance rule create --project-id <project_id> --payload '{}'
ae-cli analysis-governance rule create --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_rule.create.

Input sends project_id, payload, rule_name, comment, rule. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data.rule_id` is the created governance rule identity. Preserve it for later update/delete operations.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --rule-name | No | Rule name; required unless provided inside payload. |
| --comment | No | Rule comment. |
| --rule | No | Governance Filter JSON; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
