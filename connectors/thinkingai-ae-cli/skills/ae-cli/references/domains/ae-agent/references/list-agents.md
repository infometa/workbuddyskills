# agent +list-agents (List Agents)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Agents / read**

## Use Cases
- List Agents visible to the current user (personal / company / system scopes).
- Returns an array of Agent summaries; key fields include `id`, `name`, `description`, `scope`.
- Use this to discover a real Agent ID before creating an automation with `--agent-id` or `--agent-name`.

## Mandatory Rules (MUST)
- Do not guess Agent IDs. Always call `+list-agents` first when an Agent reference is needed.
- If the user references an Agent by name, match the name against the returned list before proceeding.

## Command
```bash
ae-cli agent +list-agents
ae-cli agent +list-agents --scope personal
ae-cli agent +list-agents --scope company --q "daily" --format table
ae-cli agent +list-agents --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Filter by scope: `personal` \| `company` \| `system` |
| `--q` | No | Search by Agent name or description |

## Decision Rules
- When the user needs an Agent ID for `+create-automation` (`--agent-id` / `--agent-name`), call this first.
- If many Agents are returned, summarize by `id`, `name`, and `scope` to help the user pick the right one.
- `--scope personal` shows only the user's own Agents; `company` / `system` show shared resources.

## Next Steps on Failure
- Empty result: confirm account permissions and the active AE host.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-agents` → confirm `agent-id` → `+create-automation`
