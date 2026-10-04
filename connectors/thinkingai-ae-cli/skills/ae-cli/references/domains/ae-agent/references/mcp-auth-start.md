# agent +mcp-auth-start (Start MCP OAuth)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Start the OAuth authorization flow for an MCP server (CLI mode).
- Endpoint: `POST /api/sandbox/agent/mcp-servers/[id]/auth/start`.
- The sandbox endpoint always uses `cliMode=true`: the server derives the OAuth callback URL itself, so no `origin` is required.
- Returns an `authorizeUrl` — the user opens it in a browser, authorizes, then polls `+mcp-auth-status` until the status becomes `authenticated`.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- The MCP server must have `authMode=oauth2`; otherwise the server returns `oauth_not_required`.
- `--redirect-after` (when provided) must be same-origin as the service base URL; otherwise it is rejected.
- `--cli` defaults to `true` and is always true on the sandbox endpoint — it is for documentation/compat only.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Start OAuth for an MCP server
ae-cli agent +mcp-auth-start --id <mcp-cuid>

# With a redirect-after URL
ae-cli agent +mcp-auth-start --id <mcp-cuid> --redirect-after "https://app.example.com/mcp/done"

# Dry-run to inspect the request
ae-cli agent +mcp-auth-start --dry-run --id <mcp-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |
| `--redirect-after` | No | URL to redirect to after OAuth completes (must be same-origin as the service base URL) |
| `--cli` | No | CLI mode (always `true` on the sandbox endpoint; server derives the callback URL) |

## Decision Rules
- If the user needs to authorize an OAuth-based MCP server, use this command.
- The command prints the `authorizeUrl` to stderr (when a TTY is detected) with guidance to open it in a browser and then poll `+mcp-auth-status`.
- The response also includes `expiresAt` (the auth session expiry, ~10 minutes) and `redirectUri` (the server-derived callback).
- After the user completes authorization in the browser, poll `+mcp-auth-status --id <id>` until `status` is `authenticated`.

## Response Shape
```json
{
  "authorizeUrl": "https://provider.com/oauth/authorize?...",
  "expiresAt": "2026-07-06T12:10:00.000Z",
  "redirectUri": "https://te-claude.example.com/agent/api/mcp-auth/callback",
  "server": { "id": "clxxx", "name": "my-mcp", "displayName": "My MCP", "scope": "personal", "providerKey": "github" }
}
```

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID.
- `400` oauth_not_required: the MCP server does not use OAuth; check `--auth-mode`.
- `400` origin_required / origin_protocol_unsupported / origin_illegal: check the `--redirect-after` URL.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+mcp-auth-start` → (browser authorize) → `+mcp-auth-status` (poll) → `+mcp-tools` (verify)
