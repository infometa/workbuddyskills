# analysis-meta exchange rule-list

Use when the user needs to list exchange-rate conversion rules.

Do not use it to validate or persist proposed rules; use `exchange rule-validate` then `exchange rule-update`.

Command:

```bash
ae-cli analysis-meta exchange rule-list --project-id <project_id> --limit 50 --offset 0
ae-cli analysis-meta exchange rule-list --dry-run
```

Capability id: `metadata.exchange_rule.list`.

Input sends `project_id`, `limit`, and `offset`.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0. |
