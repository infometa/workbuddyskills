# agent +list-attachments (List Attachments)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Attachments / read**

## Use Cases
- List the current user's attachments (paginated).
- Endpoint: `GET /api/sandbox/agent/attachments`.
- Returns an array of attachment summaries; key fields include `id`, `name`, `type`, `size`.

## Mandatory Rules (MUST)
- `--type` must be `image` or `document` when provided.

## Command
```bash
ae-cli agent +list-attachments
ae-cli agent +list-attachments --type image --format table
ae-cli agent +list-attachments --q "report" --page 1 --page-size 20
ae-cli agent +list-attachments --dry-run --type document
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--q` | No | Search keyword |
| `--type` | No | Filter by type: `image` \| `document` |
| `--page` | No | Page number (default 1) |
| `--page-size` | No | Page size (default 20, max 10000) |

## Decision Rules
- When the user needs an attachment ID for `+del-attachment`, call this first.
- `--type image` filters to image attachments; `--type document` filters to documents.
- Use `--format table` for a scannable overview.

## Next Steps on Failure
- `--type must be image or document`: use one of the two values.
- Empty result: no attachments match the filter.

## Recommended Chaining
- `+list-attachments` → confirm `id` → `+del-attachment`
- `+add-attachment` (upload) → `+list-attachments` (verify)
