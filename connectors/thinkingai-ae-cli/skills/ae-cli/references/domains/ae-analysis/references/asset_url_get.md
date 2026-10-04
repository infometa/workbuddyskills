# analysis-meta asset url-get

Use when the user needs to get a clickable resource link through the capability gateway, including post-write resource link completion.

Do not use it to discover assets or query asset data; resolve a real asset first, then use this command only to turn its governance identity or resource ID into a link.

Command:

```bash
ae-cli analysis-meta asset url-get --project-id <project_id> --payload '{}'
ae-cli analysis-meta asset url-get --project-id <project_id> --resource-type dashboard --resource-id 1
ae-cli analysis-meta asset url-get --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_url.get.

Input sends project_id, payload, node_id, resource_id, resource_type, link_info. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` identifies the normalized asset and returns `raw_url` plus `markdown_link` when the resource type supports a link. ae-cli rewrites relative URL/link fields into absolute URLs using the current host. `status=ok` without a URL means no URL mapping was available.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-id | No | Poseidon asset node ID. |
| --resource-id | No | Asset business resource ID. |
| --resource-type | No | Asset resource type. |
| --link-info | No | link_info JSON from asset governance results. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
