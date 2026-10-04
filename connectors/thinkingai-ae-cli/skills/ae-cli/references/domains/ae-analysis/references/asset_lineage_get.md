# analysis-governance asset-lineage get

Use when the user needs to get an asset lineage tree through the capability gateway.

Do not use it for a flat upstream or downstream page; use `dependency-list` or `impact-list` when pagination and filtering are required.

Command:

```bash
ae-cli analysis-governance asset-lineage get --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset-lineage get --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_lineage.get.

Input sends project_id, payload, node_id. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the lineage tree rooted at the requested `node_id`; an absent node is an asset-resolution failure, not an empty lineage result.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-id | No | Poseidon asset node ID; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
