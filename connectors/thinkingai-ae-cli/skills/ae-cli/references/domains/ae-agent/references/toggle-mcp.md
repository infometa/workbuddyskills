# agent +toggle-mcp (Toggle MCP Server)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Enable or disable an MCP server.
- Toggle operations on company/system resources only affect the current user's preference, not the global state.
- For company/system MCP servers there is no copy flow — use `+toggle-mcp` to enable a system/company MCP per-user.

## Mandatory Rules (MUST)
- `--id` and `--enabled` are required.
- Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli agent +toggle-mcp --id <mcp-cuid> --enabled true
ae-cli agent +toggle-mcp --id <mcp-cuid> --enabled false
ae-cli agent +toggle-mcp --dry-run --id <mcp-cuid> --enabled false
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |
| `--enabled` | Yes | `true` to enable, `false` to disable |

## Decision Rules
- If the user wants to turn an MCP server on/off, use `--enabled true` / `--enabled false`.
- Toggling a company/system server only changes the current user's preference.
- MCP has no copy flow (unlike Skills); to use a system/company MCP, toggle it on per-user.

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+toggle-mcp`
