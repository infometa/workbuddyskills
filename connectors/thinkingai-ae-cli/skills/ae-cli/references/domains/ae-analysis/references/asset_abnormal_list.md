# analysis-meta asset-abnormal list

Use when the user needs to list abnormal assets by resource type.

Do not use it for one known asset's detailed reason or for a general asset inventory; use `asset abnormal-get` or `asset search`.

Command:

```bash
ae-cli analysis-meta asset-abnormal list --project-id <project_id> --resource-types <resource_types> --limit 50 --offset 0
ae-cli analysis-meta asset-abnormal list --dry-run
```

Capability id: `metadata.asset_abnormal.list`.

Input sends `project_id`, `resource_types`, `limit`, and `offset`.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--resource-types` | Yes | Resource types to query. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |
