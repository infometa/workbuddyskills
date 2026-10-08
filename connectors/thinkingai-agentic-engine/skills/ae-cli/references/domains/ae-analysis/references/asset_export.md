# analysis-governance asset export

Use when the user needs the complete asset usage governance result as an asynchronous JSONL artifact.

Do not use it for a small interactive preview; use `asset list` when bounded inline rows are sufficient.

Command:

```bash
ae-cli analysis-governance asset export --project-id <project_id> --payload '{}'
ae-cli analysis-governance asset export --dry-run --project-id <project_id>
```

Capability id: analysis_meta.asset_usage.export.

Input sends project_id, payload, query, searchs, rule, operation_type, limit, offset. Payload keys must follow the common-service snake_case input schema; do not send camelCase aliases.

Output `data` is an async export descriptor with `run_id`, `artifact_id`, status, and expiry fields. Inspect and download that exact artifact rather than resubmitting the export.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| --project-id | Yes | Numeric project ID. |
| --query | No | Keyword filter. |
| --searchs | No | Quick filter JSON array. |
| --rule | No | Advanced governance Filter JSON. |
| --operation-type | No | Batch operation type filter. |
| --limit | No | Inline page size. |
| --offset | No | Zero-based page offset. |
| --payload | No | Optional snake_case object carrying the same fields. Use this for complex governance filters or backend-shaped payloads. |
