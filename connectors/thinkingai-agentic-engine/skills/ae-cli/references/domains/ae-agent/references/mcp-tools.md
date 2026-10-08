# agent +mcp-tools (List MCP Server Tools)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / read**

## Use Cases
- List the tools exposed by an MCP server (name, description, input schema).
- Endpoint: `GET /api/sandbox/agent/mcp-servers/[id]/tools`.
- Includes OAuth auto-refresh: if the credential is about to expire, the server attempts a refresh before listing tools.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- The MCP server must be enabled and properly configured; otherwise the server returns a structured error.

## Command
```bash
ae-cli agent +mcp-tools --id <mcp-cuid>

# Dry-run to inspect the request
ae-cli agent +mcp-tools --dry-run --id <mcp-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |

## Decision Rules
- If the user wants to see what tools an MCP server provides, use this command.
- The response includes `server` (id, name, transport) and `tools` (array of `{name, description, inputSchema}`).
- If the server returns `needs_auth` (400), run `+mcp-auth-start` to start OAuth, then retry.
- If the server returns `reauth_required` (428), the credential has expired — run `+mcp-auth-start` to re-authorize.
- If the server returns `disabled` (400), enable the MCP first with `+toggle-mcp --enabled true`.

## Response Shape
```json
{
  "server": { "id": "clxxx", "name": "my-mcp", "transport": "http" },
  "tools": [
    { "name": "search", "description": "Search the web", "inputSchema": { "type": "object", "properties": {} } }
  ]
}
```

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID.
- `400` needs_auth: run `+mcp-auth-start --id <id>`, then poll `+mcp-auth-status`.
- `428` reauth_required: credential expired — run `+mcp-auth-start` to re-authorize.
- `400` disabled: run `+toggle-mcp --id <id> --enabled true`.
- `502` connection_failed: verify the MCP server URL is reachable.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+mcp-tools`
- `+mcp-tools` (fails needs_auth) → `+mcp-auth-start` → `+mcp-auth-status` → `+mcp-tools`
