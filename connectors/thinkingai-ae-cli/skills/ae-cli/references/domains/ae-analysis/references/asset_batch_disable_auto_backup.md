# analysis-governance asset batch-disable-auto-backup

Use when the user needs to batch disable auto backup for assets through the capability gateway.

Do not use it to disable auto updates; this command disables backup behavior and optionally clears tag history for selected nodes.

Command:

```bash
ae-cli analysis-governance asset batch-disable-auto-backup --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-disable-auto-backup --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.disable_auto_backup.

Input sends project_id, payload, node_ids, clear_history_tag. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the batch-operation submission result. Preserve its record/status so the operation can be audited without resubmission.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --clear-history-tag | No | Whether to clear tag history: 1 yes, 0 no. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
