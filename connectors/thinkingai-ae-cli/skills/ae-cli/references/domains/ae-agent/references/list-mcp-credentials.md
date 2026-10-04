# agent +list-mcp-credentials (List MCP Credentials)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Credentials / read**

## Use Cases
- List the current user's per-user credentials for system-scope MCP servers.
- Endpoint: `GET /api/sandbox/agent/mcp-credentials`.
- Returns one entry per system MCP server, with the user's credential (or `null` if none exists).

## Mandatory Rules (MUST)
- No flags required — lists all system MCP servers and the current user's credential status.
- Only system-scope MCP servers are included; personal/company credentials are managed via the MCP server config and OAuth flow.

## Command
```bash
# List all system MCP credentials
ae-cli agent +list-mcp-credentials

# Dry-run to inspect the request
ae-cli agent +list-mcp-credentials --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| (none) | — | — |

## Decision Rules
- If the user wants to check which system MCP servers have credentials configured, use this command.
- Each item shows `mcpServerId`, `mcpServerName`, and a `credential` object (or `null`).
- The `credential` object includes `authType`, `enabled`, `expiresAt`, and whether a token is stored — but the token itself is not returned in plaintext here (use `+mcp-token` for that).

## Response Shape
```json
{
  "items": [
    {
      "mcpServerId": "clxxx",
      "mcpServerName": "te-mcp",
      "credential": {
        "mcpServerId": "clxxx",
        "userId": "uyyy",
        "authType": "oauth",
        "enabled": true,
        "expiresAt": "2026-07-06T13:00:00.000Z",
        "hasToken": true
      }
    },
    {
      "mcpServerId": "clzzz",
      "mcpServerName": "other-mcp",
      "credential": null
    }
  ]
}
```

## Next Steps on Failure
- `401` / auth expired: run `ae-cli auth login`.

## Recommended Chaining
- `+list-mcp-credentials` (check) → `+set-mcp-credential` (set)
- `+list-mcp-credentials` → `+mcp-token` (get plaintext token for useMcpToken servers)
