# Cancel a running Engage report query


Cancel a running data query by requestId.

Mapped capability: `engage-setting.query.cancel` (L3)

## Input

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | Yes | Query requestId |

## Safety Constraints

This command is a **write operation** and cancels an existing query.

## Examples

```bash
ae-cli capability run engage-setting.query.cancel \
  --input '{"request_id":"00000000-0000-0000-0000-000000000000"}'
```
