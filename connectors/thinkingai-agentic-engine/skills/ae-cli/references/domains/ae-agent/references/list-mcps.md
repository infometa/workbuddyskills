# agent +list-mcps (List MCP Servers)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / read**

## Use Cases
- List MCP servers visible to the current user (personal / company / system scopes).
- Returns an array of MCP server summaries; key fields include `id`, `name`, `url`, `scope`, `enabled`.

## Mandatory Rules (MUST)
- Do not guess MCP server record IDs. Always call `+list-mcps` first when an ID is needed.

## Command
```bash
ae-cli agent +list-mcps
ae-cli agent +list-mcps --scope personal --format table
ae-cli agent +list-mcps --scope company
ae-cli agent +list-mcps --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Filter by scope: `personal` \| `company` \| `system` |

## Decision Rules
- When the user needs an MCP server ID for `+del-mcp` / `+toggle-mcp` / `+set-mcp-meta`, call this first.
- Use `--format table` for a scannable overview of many servers.

## Next Steps on Failure
- Empty result: confirm account permissions and the active AE host.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+toggle-mcp` / `+del-mcp` / `+set-mcp-meta`
- `+list-mcp-market` (browse) → `+add-mcp` (add) → `+list-mcps` (verify)
