# agent +attachment-stats (Attachment Library Statistics)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Attachments / read**

## Use Cases
- Show the current user's attachment library statistics: total file count, total size, image count, document count.
- Endpoint: `GET /api/sandbox/agent/attachments/stats`.
- No parameters; returns a single statistics object for the authenticated user's own data.

## Mandatory Rules (MUST)
- No flags. The command always returns the current user's own attachment statistics.

## Command
```bash
ae-cli agent +attachment-stats

# Dry-run to inspect the request
ae-cli agent +attachment-stats --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| _(none)_ | — | This command takes no flags. |

## Response Shape
```json
{
  "totalCount": 42,
  "totalSize": 10485760,
  "imageCount": 15,
  "documentCount": 27
}
```

| Field | Description |
|---|---|
| `totalCount` | Total number of ready attachments |
| `totalSize` | Total size in bytes (sum of all ready attachments) |
| `imageCount` | Number of image attachments (type=image) |
| `documentCount` | Number of document attachments (type=document) |

## Next Steps on Failure
- `500` 获取附件统计失败: an internal aggregation error — retry, then contact the platform maintainer if it persists.

## Recommended Chaining
- `+attachment-stats` (overview) → `+list-attachments` (drill into the list)
- `+add-attachment` (upload) → `+attachment-stats` (verify totals changed)
