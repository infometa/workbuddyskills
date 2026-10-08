# metadata data-table list

> Capability id: `metadata.data_table.list` · Domain: `metadata`.

## Command

```bash
ae-cli metadata data-table list --project-id <project_id> --limit 50 --offset 0
ae-cli metadata data-table list --project-id <project_id> --dry-run
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |

## Request Body

```json
{ "project_id": 1, "limit": 50, "offset": 0 }
```

## Decision Rules

- Use this command to discover `data_table_id` before get, delete, download, or property binding.
- If the list is empty, do not invent IDs; create/upload a table first or ask for the target table.
- Read rows from `data.items`; pagination metadata is always `total`, `limit`, `offset`, `has_more`, and `next_offset`.
