# analysis-meta asset search

Use when the user needs to search project assets by keyword.

Do not use it to query report/dashboard result data; it discovers asset records only.

Command:

```bash
ae-cli analysis-meta asset search --project-id <project_id> --payload '{"keyword":"revenue"}' --limit 50 --offset 0
ae-cli analysis-meta asset search --dry-run
```

Capability id: `metadata.asset.search`.

Input sends `project_id`, `payload`, `limit`, and `offset`.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`. A blank keyword returns an empty envelope rather than a full asset list.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Search object. Required semantic field: non-blank `keyword`. Optional filters are `own_types` and `res_cats`; do not pass server-owned identity or pagination-test fields. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |
