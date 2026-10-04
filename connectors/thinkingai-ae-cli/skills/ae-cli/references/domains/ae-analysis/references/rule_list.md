# analysis-governance rule list

Use when the user needs to list asset governance rules through the capability gateway.

Do not use it to discover rule field syntax; use `rule-schema` for construction metadata and this command for existing rule IDs and definitions.

Command:

```bash
ae-cli analysis-governance rule list --project-id <project_id> --limit 50 --offset 0
ae-cli analysis-governance rule list --dry-run --project-id <project_id>
```

Capability id: `governance.rule.list`.

Input sends `project_id`, optional `payload`, `limit`, and `offset`. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`. Resolve a real `rule_id` from `items` before update or delete.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |
