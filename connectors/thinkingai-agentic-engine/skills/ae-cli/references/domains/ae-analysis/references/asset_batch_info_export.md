# analysis-governance asset batch-info-export

Use when the user needs to batch export asset information through the capability gateway.

Do not use it to change the selected assets or export SQL definitions; it creates an XLSX information artifact for verified `node_ids` only.

Command:

```bash
ae-cli analysis-governance asset batch-info-export --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-info-export --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.info_export.

Input sends project_id, payload, node_ids, reports_version, zone_offset, schedule_ui_config, dashboard_status, refresh_type, cache_config, clear_history_tag. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is an async XLSX descriptor with `run_id`, `artifact_id`, status, and expiry fields. Inspect and download the returned artifact IDs.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
