# agent +add-mcp (Add MCP Server)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Add an MCP server to the personal or company scope.
- Returns the newly created MCP server object including its `id`.
- `--scope personal` (default) creates a personal MCP server; `--scope company` creates a company MCP server (requires root/agent_admin).
- Optional market meta (`--category` / `--icon-emoji` / `--icon-color`) is applied via a follow-up PATCH to `/api/sandbox/agent/mcp-servers/[id]/meta`.

## Mandatory Rules (MUST)
- `--name` and `--url` are required.
- `--name` must start with a letter and contain only letters, digits, `_`, or `-` (2–64 chars).
- `--url` must be a valid `http://` or `https://` URL (file://, ftp://, and other protocols are blocked).
- `--transport` must be `sse` or `http` (default `http`).
- `--headers` must be a valid JSON object when provided.
- `--category` must be one of the market category keys (see below) when provided.
- **MCP creation does NOT validate server connectivity** — an unreachable URL is accepted at create time and only fails when the agent calls the MCP at runtime. Double-check the URL.
- `--scope` controls target scope: `personal` (default) or `company`. Company scope requires root/agent_admin.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command
```bash
ae-cli agent +add-mcp \
  --name my-mcp \
  --url "https://mcp.example.com/mcp" \
  --transport http \
  --headers '{"Authorization":"Bearer token"}'

# With market category and icon
ae-cli agent +add-mcp \
  --name my-mcp \
  --url "https://mcp.example.com/mcp" \
  --transport http \
  --headers '{"Authorization":"Bearer token"}' \
  --category dev_tool \
  --icon-emoji robot

# Dry-run to inspect the request before executing
ae-cli agent +add-mcp --dry-run --name my-mcp --url "https://mcp.example.com/mcp"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--name` | Yes | Server name (2–64 chars, letter start, `[a-zA-Z0-9_-]`) |
| `--url` | Yes | MCP server URL (`http://` or `https://` only) |
| `--display-name` | No | Display name (max 100) |
| `--description` | No | Description (max 255) |
| `--transport` | No | `sse` \| `http` (default `http`) |
| `--headers` | No | HTTP headers as JSON object |
| `--category` | No | Market category key (see above) |
| `--icon-emoji` | No | Market icon emoji (e.g. `robot`) |
| `--icon-color` | No | Market icon color (e.g. `#1E76F0`) |
| `--scope` | No | Target scope: `personal` (default) or `company` (requires root/agent_admin) |

## Decision Rules
- If the user provides an MCP spec, map the server identifier to `--name` and the endpoint to `--url`.
- Always verify the URL is reachable before creating — the CLI will not check connectivity.
- `--category` / `--icon-emoji` / `--icon-color` are optional market meta; they are applied via a follow-up PATCH after creation. If the meta update fails, the MCP is still created and a warning is printed to stderr.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `--name must start with a letter...`: rename the server to match the pattern.
- `--url only supports http:// or https:// protocols`: switch to an http(s) URL.
- Warning `MCP created but meta update failed`: the MCP exists; retry the meta with `+set-mcp-meta`.

## Recommended Chaining
- `+list-mcp-market` (browse) → `+add-mcp` → `+list-mcps` (verify) → `+set-mcp-meta` (adjust meta)
