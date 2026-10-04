# agent +list-mcp-market (List MCP Market)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Market (browse) / read**

## Use Cases
- List MCP servers from the market (system / company / personal scopes).
- Endpoint: `GET /api/sandbox/agent/mcp-servers/market`.
- Supports filtering by scope, category, search, and sort, with pagination.
- Use this to discover MCP servers before adding one with `+add-mcp`.

## Mandatory Rules (MUST)
- `--scope` must be one of the market scopes when provided (see below).
- `--category` must be one of the market category keys when provided (see below).
- `--sort` must be one of the sort options when provided (see below).

## Market Scope
`all | system | company | custom` (`custom` = personal; `all` = system + company + personal)

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Sort Options
`newest | calls | likes` (`calls` sorts MCP by call count)

## Command
```bash
ae-cli agent +list-mcp-market
ae-cli agent +list-mcp-market --scope company --category dev_tool --sort calls --format table
ae-cli agent +list-mcp-market --search "weather" --sort newest
ae-cli agent +list-mcp-market --limit 20 --offset 0
ae-cli agent +list-mcp-market --dry-run --scope system
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Market scope (see above; default `all`) |
| `--category` | No | Category key (see above) |
| `--search` | No | Fuzzy search on name/displayName/description/url |
| `--sort` | No | Sort option (see above; default `newest`) |
| `--limit` | No | Page size (1–100, default 50) |
| `--offset` | No | Page offset (>=0, default 0) |

## Decision Rules
- When the user wants to browse available MCP servers, call this first.
- `--scope company` shows same-company MCP servers; `--scope system` shows built-in ones; `--scope custom` shows personal ones.
- Use `--sort calls` to find the most-used MCP servers.
- Use `--format table` for a scannable overview.

## Next Steps on Failure
- `--scope must be one of...`: use one of the market scope values.
- `--category must be one of...`: use one of the category keys.
- Empty result: widen filters (remove `--category` / `--scope`).

## Recommended Chaining
- `+list-mcp-market` (browse) → `+add-mcp` (add to personal) → `+list-mcps` (verify)
