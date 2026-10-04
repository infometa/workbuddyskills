# analysis-governance rule schema

Use when the user needs to get asset governance rule field schema through the capability gateway.

Do not use it to list saved governance rules; use it before create/update only when the allowed rule fields or operators are unknown.

Command:

```bash
ae-cli analysis-governance rule schema --project-id <project_id>
ae-cli analysis-governance rule schema --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_rule.schema.

Input sends project_id, payload. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the project-specific rule column/operator schema consumed by the `rule` object in rule create and update commands.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
