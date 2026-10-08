# analysis-governance asset batch-sql-export

Use when the user needs to batch export asset SQL definitions through the capability gateway.

Do not use it for general asset information or query execution; it exports SQL definitions for verified asset `node_ids` as XLSX.

Command:

```bash
ae-cli analysis-governance asset batch-sql-export --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-sql-export --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.sql_export.

Input sends project_id, payload, node_ids, reports_version, zone_offset, schedule_ui_config, dashboard_status, refresh_type, cache_config, clear_history_tag. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is an async XLSX descriptor with `run_id`, `artifact_id`, status, and expiry fields. Reuse those IDs for lifecycle inspection and download.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
