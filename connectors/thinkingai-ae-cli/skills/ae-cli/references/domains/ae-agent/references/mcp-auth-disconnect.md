# agent +mcp-auth-disconnect (Disconnect MCP OAuth)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Disconnect the OAuth authorization for an MCP server.
- Endpoint: `POST /api/sandbox/agent/mcp-servers/[id]/auth/disconnect`.
- Clears the stored token / credentialJson / identityJson and marks the server `enabled=false`.
- Use this to revoke a stale credential before re-authorizing, or to fully detach from an OAuth provider.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- After disconnect, the MCP server is disabled (`enabled=false`); re-enable with `+toggle-mcp --enabled true` after re-authorizing.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Disconnect OAuth
ae-cli agent +mcp-auth-disconnect --id <mcp-cuid>

# Dry-run to inspect the request
ae-cli agent +mcp-auth-disconnect --dry-run --id <mcp-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |

## Decision Rules
- If the user wants to revoke an MCP's OAuth credential and disable the server, use this command.
- After disconnecting, to use the MCP again: run `+mcp-auth-start` to re-authorize, then `+toggle-mcp --enabled true` (if not auto-enabled).
- Disconnect does NOT delete the MCP server record — it only clears the OAuth credential. To delete the record, use `+del-mcp`.

## Response Shape
```json
{
  "ok": true,
  "status": "disconnected",
  "server": { "id": "clxxx", "name": "my-mcp", "displayName": "My MCP", "scope": "personal", "providerKey": "github" }
}
```

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+mcp-auth-disconnect` → `+mcp-auth-start` (re-authorize) → `+mcp-auth-status` (verify) → `+toggle-mcp --enabled true`
