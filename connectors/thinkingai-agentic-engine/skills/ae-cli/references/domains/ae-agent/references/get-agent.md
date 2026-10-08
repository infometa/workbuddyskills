# agent +get-agent (Get Agent Details)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Agents / read**

## Use Cases
- Fetch full details of a single Agent by ID (system visible to all; company to same company; personal to owner).
- Use this to confirm an Agent's current model, MCP, Skill, and enabled state before updating or deleting.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Agent record ID (CUID) via `+list-agents` — do not guess.
- Read operation — no confirmation prompt.

## Command
```bash
ae-cli agent +get-agent --id <agent-cuid>
ae-cli agent +get-agent --id <agent-cuid> --format table
ae-cli agent +get-agent --dry-run --id <agent-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Agent record ID (CUID) |

## Decision Rules
- When the user references an Agent by name, resolve it to an ID with `+list-agents` first, then call `+get-agent` for full details.
- Use `--format table` for a scannable single-record view.
- The returned `item` includes the resolved model, MCP/Skill ID lists, and the current user's enabled preference (for system/company Agents).

## Next Steps on Failure
- `404` / `Agent 不存在`: the Agent does not exist, is deleted, or is not visible to you (personal Agent owned by another user). Re-run `+list-agents` to discover visible IDs.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-agents` → confirm `id` → `+get-agent` (inspect) → `+update-agent` / `+del-agent` / `+create-automation --agent-id <id>`
