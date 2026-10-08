# agent +del-mcp (Delete Personal MCP Server)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **MCP Servers / write**

## Use Cases
- Delete a personal-scope MCP server.
- Only `personal` scope MCP servers can be deleted via CLI; company/system servers are read-only.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real MCP server record ID (CUID) via `+list-mcps` — do not guess.
- Prefer `--dry-run` before executing a destructive delete.
- This is a high-risk-write operation; never execute it before the dry-run impact is explicitly confirmed.

## Command
```bash
ae-cli agent +del-mcp --id <mcp-cuid> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli agent +del-mcp --id <mcp-cuid> --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | MCP server record ID (CUID) |

## Decision Rules
- Confirm the server ID with `+list-mcps` before deleting.
- If the server is company/system scope, deletion is not available via CLI (use `+toggle-mcp` to disable it per-user instead).

## Next Steps on Failure
- `404` / not found: re-run `+list-mcps` to verify the server ID and scope.

## Recommended Chaining
- `+list-mcps` → confirm `id` → `+del-mcp`
