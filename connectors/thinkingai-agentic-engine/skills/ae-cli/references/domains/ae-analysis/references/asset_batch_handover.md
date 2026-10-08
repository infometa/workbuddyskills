# analysis-governance asset batch-handover

Use when the user needs to batch hand over governed assets to another user through the capability gateway.

Do not use it to share assets or modify permissions; it transfers ownership of verified nodes to one verified numeric user ID.

Command:

```bash
ae-cli analysis-governance asset batch-handover --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset batch-handover --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_batch.handover.

Input sends project_id, payload, node_ids, to_user_id. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the ownership-transfer batch submission result. Confirm completion from its operation record rather than assuming submission equals handover.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --node-ids | No | Asset node ID JSON array; required unless provided inside payload. |
| --to-user-id | No | Target user ID; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
