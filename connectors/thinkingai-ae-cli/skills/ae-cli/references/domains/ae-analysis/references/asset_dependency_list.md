# analysis-governance asset-dependency list

Use when the user needs to list upstream dependencies for one asset through the capability gateway.

Do not use it for downstream impact or a full lineage tree; this command pages direct upstream dependencies for one resolved asset node.

Command:

```bash
ae-cli analysis-governance asset-dependency list --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset-dependency list --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_dependency.list.

Input sends project_id, payload, node_id, query, searchs, rule, limit, offset. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` contains dependency `items`, `total`, `operation_types`, `limit`, and `offset`; continue paging only while the observed total exceeds the current page.

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
