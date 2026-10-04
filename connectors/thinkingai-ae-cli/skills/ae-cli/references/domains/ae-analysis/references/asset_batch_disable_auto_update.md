# analysis-governance asset batch-disable-auto-update

Use when the user needs to batch disable auto update for assets through the capability gateway.

Do not use it to disable backups or freeze dashboard schedules; this operation only changes automatic update behavior for selected nodes.

Command:

```bash
ae-cli analysis-governance asset batch-disable-auto-update --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-disable-auto-update --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.disable_auto_update.

Input sends project_id, payload, node_ids, refresh_type. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the batch-operation submission result. Follow the returned record/status through `operation-record-list` instead of repeating the command.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --refresh-type | No | Dashboard refresh type: 1 enabled, 0 disabled. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
