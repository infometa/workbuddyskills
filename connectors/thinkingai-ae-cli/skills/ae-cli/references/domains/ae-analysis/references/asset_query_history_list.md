# analysis-governance asset-query-history list

Use when the user needs to list query history for one asset through the capability gateway.

Do not use it to execute or inspect an analysis query; it only pages historical query usage associated with one governed asset.

Command:

```bash
ae-cli analysis-governance asset-query-history list --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset-query-history list --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_query_history.list.

Input sends project_id, payload, node_id, query, searchs, rule, limit, offset. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` contains query-history `items`, `total`, `operation_types`, `limit`, and `offset`; treat an empty history as a successful no-usage result.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-id | No | Poseidon asset node ID; required unless provided inside payload. |
| --query | No | Keyword filter. |
| --searchs | No | Quick filter JSON array. |
| --rule | No | Advanced governance Filter JSON. |
| --limit | No | Inline page size. |
| --offset | No | Zero-based page offset. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
