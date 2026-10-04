# agent +mcp-auth-status (Query MCP OAuth Status)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / read**

## Use Cases
- Query the OAuth authorization status of an MCP server.
- Endpoint: `GET /api/sandbox/agent/mcp-servers/[id]/auth/status`.
- Used as the polling step after `+mcp-auth-start`: the user authorizes in a browser, then polls this command until `status` becomes `authenticated`.
- Internally attempts an auto-refresh of soon-to-expire tokens before reporting status.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.

## Command
```bash
# Poll OAuth status
ae-cli agent +mcp-auth-status --id <mcp-cuid>

# Dry-run to inspect the request
ae-cli agent +mcp-auth-status --dry-run --id <mcp-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |

## Decision Rules
- Poll this command after `+mcp-auth-start` until `status` is `authenticated`.
- The `status` field can be:
  - `not_required` — the MCP does not use OAuth (authMode ≠ oauth2).
  - `needs_auth` — no credential exists yet; run `+mcp-auth-start`.
  - `reauth_required` — the credential has expired; run `+mcp-auth-start` to re-authorize.
  - `disabled` — the MCP server is disabled; run `+toggle-mcp --enabled true`.
  - `authenticated` — the credential is valid and ready to use.
- `authenticated` is `true` only when `status` is `authenticated`.
- `expiresAt` is the credential expiry (ISO string) or `null` if not applicable.

## Response Shape
```json
{
  "status": "authenticated",
  "authenticated": true,
  "expiresAt": "2026-07-06T13:00:00.000Z",
  "updatedAt": "2026-07-06T12:30:00.000Z",
  "reason": "oauth_not_required"
}
```

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID.

## Recommended Chaining
- `+mcp-auth-start` → (browser authorize) → `+mcp-auth-status` (poll until `authenticated`) → `+mcp-tools` (verify tools are accessible)
