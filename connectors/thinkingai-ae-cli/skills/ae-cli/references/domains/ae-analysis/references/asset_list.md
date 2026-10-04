# analysis-governance asset list

Use when the user needs to list assets for usage governance through the capability gateway.

Do not use it for report/dashboard result data or lineage; it lists governance rows that can be filtered or selected for later asset operations.

Command:

```bash
ae-cli analysis-governance asset list --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset list --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_usage.list.

Input sends project_id, payload, query, searchs, rule, operation_type, limit, offset. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` contains `items`, `total`, `operation_types`, `limit`, and `offset`. An empty `items` array is a successful page with no matching governed assets.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --query | No | Keyword filter. |
| --searchs | No | Quick filter JSON array. |
| --rule | No | Advanced governance Filter JSON. |
| --operation-type | No | Batch operation type filter. |
| --limit | No | Inline page size. |
| --offset | No | Zero-based page offset. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
