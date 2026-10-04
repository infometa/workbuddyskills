# analysis-governance operation-record export

Use when the user needs to export one asset batch operation record result through the capability gateway.

Do not use it to list records or export asset rows; resolve one real `record_id` first, then export that operation's result as XLSX.

Command:

```bash
ae-cli analysis-governance operation-record export --project-id <project_id> --payload '{}'
ae-cli analysis-governance operation-record export --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_operation_record.export.

Input sends project_id, payload, record_id. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is an async XLSX descriptor with `run_id`, `artifact_id`, status, and expiry fields. Inspect and download that exact export.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --record-id | No | Operation record ID; required unless provided inside payload. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
