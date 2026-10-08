# agent +update-mcp (Update MCP Server Config)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Update an existing MCP server's configuration (name, URL, transport, headers, auth mode, etc.).
- Endpoint: `PATCH /api/sandbox/agent/mcp-servers/[id]`.
- Personal scope: requires ownership. Company scope: requires root. System scope: read-only.
- Includes connectivity validation and OAuth reauth cascade when relevant.
- Use `--auto-rename` to auto-rename on name conflict instead of returning a 409.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- At least one update field must be provided (aside from `--id`).
- `--name` (when provided) must start with a letter and contain only letters, digits, `_`, or `-` (2–64 chars).
- `--url` (when provided) must be a valid `http://` or `https://` URL (file://, ftp://, and other protocols are blocked).
- `--transport` (when provided) must be `sse`, `http`, or `streamable-http` (stdio is disabled by policy on the sandbox endpoint).
- `--auth-mode` (when provided) must be `none`, `oauth2`, `header`, or `manual`.
- `--enabled` accepts `true` or `false`; **omit it to leave the enabled state unchanged**. To simply toggle, prefer `+toggle-mcp`.
- `--headers` / `--secret-headers` must be valid JSON objects when provided. `--secret-headers` values are encrypted server-side.
- The server runs a connectivity check on update; an unreachable URL fails with `connectivity_failed`.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Rename + update URL
ae-cli agent +update-mcp --id <mcp-cuid> --name my-mcp-renamed --url "https://mcp.example.com/mcp"

# Update transport + headers
ae-cli agent +update-mcp --id <mcp-cuid> --transport streamable-http --headers '{"Authorization":"Bearer token"}'

# Enable with auto-rename on conflict
ae-cli agent +update-mcp --id <mcp-cuid> --enabled true --auto-rename

# Disable (explicit)
ae-cli agent +update-mcp --id <mcp-cuid> --enabled false

# Dry-run to inspect the request before executing
ae-cli agent +update-mcp --dry-run --id <mcp-cuid> --name new-name
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |
| `--name` | No* | Server name (2–64 chars, letter start, `[a-zA-Z0-9_-]`) |
| `--url` | No* | MCP server URL (`http://` or `https://` only) |
| `--display-name` | No* | Display name (max 100) |
| `--description` | No* | Description (max 255) |
| `--transport` | No* | `sse` \| `http` \| `streamable-http` |
| `--headers` | No* | HTTP headers as JSON object |
| `--secret-headers` | No* | Secret headers as JSON object (encrypted server-side) |
| `--auth-mode` | No* | `none` \| `oauth2` \| `header` \| `manual` |
| `--enabled` | No* | `true` \| `false` (omit to leave unchanged) |
| `--auto-rename` | No* | Auto-rename on name conflict (default `false`) |

\* At least one of these must be provided.

## Decision Rules
- If the user wants to change any MCP config field, use this command.
- To only enable/disable an MCP (no other changes), prefer `+toggle-mcp` — it is simpler and has no connectivity check.
- `--enabled` is a string (`true`/`false`), not a boolean flag, so that omitting it leaves the state unchanged.
- If the server returns `NAME_EXISTS` (409), re-run with `--auto-rename` or pick a different `--name`.
- After updating URL/transport/headers, the server re-validates connectivity; if it fails, the old config is preserved.
- Updating OAuth-related fields (URL, auth mode, secret headers) may trigger a reauth cascade — affected credentials are expired and `reauthRequired` / `reauthCredentialCount` are returned in the response.

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID and scope.
- `403` company_admin_only: the current user is not root (company-scope update).
- `403` system_mcp_readonly: system-scope MCPs cannot be updated.
- `409` NAME_EXISTS: re-run with `--auto-rename` or a different `--name`.
- `400` connectivity_failed: verify the URL is reachable and transport is correct.
- `400` needs_auth: refresh credentials first (`+mcp-auth-start`), then re-enable.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+update-mcp`
- `+update-mcp` → (if reauth required) → `+mcp-auth-start` → `+mcp-auth-status`
