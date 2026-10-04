# agent +set-mcp-credential (Set MCP Credential)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Credentials / write**

## Use Cases
- Upsert a per-user credential for a system-scope MCP server (by `mcpServerId` + `userId`).
- Endpoint: `POST /api/sandbox/agent/mcp-credentials`.
- The `token` (when provided) is encrypted server-side before storage.
- Use this to manually set an API key or OAuth token for a system MCP server.

## Mandatory Rules (MUST)
- `--mcp-server-id` is required. Obtain the real system MCP server record ID (CUID) via `+list-mcps` (scope=system) or `+list-mcp-credentials` — do not guess.
- `--auth-type` defaults to `oauth`; must be `oauth` or `apikey` when provided.
- `--token` is optional but recommended — without it, only the credential record is created/enabled without a stored token.
- `--expires-at` (when provided) must be a valid ISO 8601 datetime (e.g. `2026-12-31T23:59:59Z`).
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Set an OAuth token with expiry
ae-cli agent +set-mcp-credential --mcp-server-id <mcp-cuid> --token "abc123" --expires-at "2026-12-31T23:59:59Z"

# Set an API key (no expiry)
ae-cli agent +set-mcp-credential --mcp-server-id <mcp-cuid> --auth-type apikey --token "sk-xxx"

# Dry-run to inspect the request
ae-cli agent +set-mcp-credential --dry-run --mcp-server-id <mcp-cuid> --token "abc123"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--mcp-server-id` | Yes | System MCP server record ID (CUID) |
| `--auth-type` | No | `oauth` \| `apikey` (default `oauth`) |
| `--token` | No | Token / API key (plaintext; encrypted server-side) |
| `--expires-at` | No | ISO 8601 datetime (e.g. `2026-12-31T23:59:59Z`) |

## Decision Rules
- If the user wants to manually set a token/API key for a system MCP server, use this command.
- For OAuth-based servers, prefer `+mcp-auth-start` (full OAuth flow with auto-refresh). Use `+set-mcp-credential` only when you have a pre-obtained token.
- For API-key-based servers (`--auth-type apikey`), this is the primary way to set the key.
- The token is encrypted at rest; it is never returned in plaintext via `+list-mcp-credentials` (use `+mcp-token` for useMcpToken servers).

## Response Shape
```json
{
  "item": {
    "mcpServerId": "clxxx",
    "userId": "uyyy",
    "authType": "oauth",
    "enabled": true,
    "expiresAt": "2026-12-31T23:59:59.000Z",
    "hasToken": true
  }
}
```

## Next Steps on Failure
- `404` not_found_or_forbidden: the MCP server does not exist or is not a system-scope server.
- `401` / auth expired: run `ae-cli auth login`.

## Recommended Chaining
- `+list-mcp-credentials` (check) → `+set-mcp-credential` (set) → `+list-mcp-credentials` (verify)
- For OAuth servers: `+mcp-auth-start` (preferred) → `+mcp-auth-status` → `+mcp-tools`
