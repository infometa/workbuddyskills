# analysis-governance asset batch-delete

Use when the user needs to batch delete governed assets through the capability gateway.

Do not use it for a single unverified name or as cleanup after a failed test; resolve exact `node_ids`, dry-run the final set, and require explicit confirmation.

Command:

```bash
ae-cli analysis-governance asset batch-delete --project-id <project_id> --payload '{}' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-governance asset batch-delete --project-id <project_id> --payload '{}' --yes
```

Capability id: analysis_meta.asset_batch.delete.

Input sends project_id, payload, node_ids. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the batch-operation submission result. Preserve any returned record identity/status and use `operation-record-list` to verify completion.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
