# analysis-governance asset batch-dashboard-schedule-freeze

Use when the user needs to batch freeze dashboard schedules for governed assets through the capability gateway.

Do not use it for non-dashboard assets or ordinary dashboard content edits; it changes schedule, cache, refresh, and freeze settings in one batch.

Command:

```bash
ae-cli analysis-governance asset batch-dashboard-schedule-freeze --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-dashboard-schedule-freeze --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.dashboard_schedule_freeze.

Input sends project_id, payload, node_ids, reports_version, zone_offset, schedule_ui_config, dashboard_status, refresh_type, cache_config. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the dashboard batch-operation submission result. Verify its returned operation record before reporting the schedules as frozen.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --dashboard-status | No | Dashboard status, such as freeze or normal. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
