# agent +mcp-token (Get MCP Token)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Credentials / read**

## Use Cases
- Get the plaintext MCP token for `useMcpToken=true` system MCP servers.
- Endpoint: `GET /api/sandbox/agent/mcp-credentials/mcp-token`.
- All such servers share one token; the server decrypts and returns it.
- This is a product behavior (consistent with the web UI) — the token is returned in plaintext so it can be used as a Bearer credential for MCP API calls.

## Mandatory Rules (MUST)
- No flags required.
- The returned token is **plaintext** — handle it as a secret:
  - Do NOT write it to shell history (avoid `export MCP_TOKEN=$(ae-cli agent +mcp-token)` without precautions).
  - Do NOT log it or commit it to version control.
  - Prefer piping directly to the consuming process or a secure store.
- The command prints a security warning to stderr (when a TTY is detected) reminding the user to safeguard the token.

## Command
```bash
# Get the MCP token (prints to stdout as JSON)
ae-cli agent +mcp-token

# Pipe to a file (avoid shell history)
ae-cli agent +mcp-token --format json > /dev/shm/mcp-token.json 2>/dev/null

# Dry-run to inspect the request
ae-cli agent +mcp-token --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| (none) | — | — |

## Decision Rules
- If the user needs the shared MCP token to call MCP-enabled APIs, use this command.
- The token is shared across all `useMcpToken=true` system MCP servers — a single call returns it.
- If `token` is `null`, no shared MCP token is available on the current server.
- Prefer `+list-mcp-credentials` to check credential status without exposing the plaintext token.

## Response Shape
```json
{
  "token": "mcp-xxxxxxxxxxxxxxxx"
}
```

When no token is provisioned:
```json
{
  "token": null
}
```

## Next Steps on Failure
- `401` / auth expired: run `ae-cli auth login`.
- `token: null`: ask the server administrator whether a shared MCP token is expected in this environment.

## Recommended Chaining
- `+mcp-token` (retrieve) → use as `Authorization: bearer <token>` for MCP API calls
