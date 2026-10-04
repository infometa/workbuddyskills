# analysis-governance operation-record list

Use when the user needs to list asset batch operation records through the capability gateway.

Do not use it to submit a new batch operation; use it to find and inspect records produced by prior asset governance actions.

Command:

```bash
ae-cli analysis-governance operation-record list --project-id <project_id> --payload '{}'
ae-cli analysis-governance operation-record list --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_operation_record.list.

Input sends project_id, payload, type, status, query, sort_field, sort_order, limit, offset. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is the paged batch-operation record result. Use record status to distinguish submitted, running, successful, and failed work before taking another action.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --type | No | Batch operation type. |
| --status | No | Operation status JSON array. |
| --query | No | Keyword filter. |
| --sort-field | No | Sort field. |
| --sort-order | No | Sort order: asc or desc. |
| --limit | No | Inline page size. |
| --offset | No | Zero-based page offset. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
