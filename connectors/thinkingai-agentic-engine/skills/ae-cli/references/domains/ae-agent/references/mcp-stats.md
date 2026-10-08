# agent +mcp-stats (MCP Call Statistics)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / read**

## Use Cases
- Show MCP tool call statistics for the current user over the last N days.
- Endpoint: `GET /api/sandbox/agent/mcp-servers/stats`.
- Returns aggregations: total calls, by-server, daily, and daily-by-server.

## Mandatory Rules (MUST)
- `--days` must be an integer between 1 and 365 when provided; defaults to 30.
- Statistics are scoped to the authenticated user's own MCP usage.

## Command
```bash
# Default: last 30 days
ae-cli agent +mcp-stats

# Last 7 days
ae-cli agent +mcp-stats --days 7

# Dry-run to inspect the request
ae-cli agent +mcp-stats --dry-run --days 7
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--days` | No | Lookback window in days (1-365, default 30) |

## Response Shape
```json
{
  "days": 30,
  "totalCalls": 128,
  "byServer": { "clxxx-server-a": 80, "clxxx-server-b": 48 },
  "daily": [
    { "date": "2026-06-07", "calls": 5 },
    { "date": "2026-06-08", "calls": 0 }
  ],
  "dailyByServer": {
    "clxxx-server-a": { "2026-06-07": 3, "2026-06-08": 0 }
  }
}
```

| Field | Description |
|---|---|
| `days` | The lookback window used for this query |
| `totalCalls` | Sum of all MCP tool calls over the window |
| `byServer` | Map of `mcpServerId` → call count |
| `daily` | Array of `{ date, calls }` for each day in the window (oldest → newest) |
| `dailyByServer` | Map of `mcpServerId` → `{ date: calls }` |

## Decision Rules
- Use `--days 7` for a weekly review, `--days 30` (default) for a monthly review.
- `daily` always contains one entry per day in the window (zero-filled), so it is safe to chart directly.
- `byServer` only contains servers with at least one call in the window; cross-reference IDs with `+list-mcps` to resolve names.

## Next Steps on Failure
- `--days must be an integer between 1 and 365`: pass an integer in range.
- `500` 获取 MCP 调用统计失败: an internal aggregation error — retry, then contact the platform maintainer if it persists.

## Recommended Chaining
- `+mcp-stats` (which servers are active) → `+list-mcps` (resolve server IDs to names)
- `+mcp-stats` (low/no calls) → `+mcp-tools` (verify the server exposes tools) → `+mcp-auth-start` if `needs_auth`
