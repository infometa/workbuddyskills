# agent +update-agent (Update Agent)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Agents / write**

## Use Cases
- Update an existing Agent's name, description, system prompt, model, MCP servers, Skills, or enabled state.
- Only the fields you pass are changed; omitted fields keep their current values.
- `--enabled` on a system/company Agent writes the current user's personal preference (does not change the global state).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Agent record ID (CUID) via `+list-agents` — do not guess.
- Only `personal` Agents can be fully edited by their owner; `company` Agents require root.
- `--instructions` supports `@-` to read from stdin.
- `--mcp-ids` / `--skill-ids` must be JSON array strings when provided; they replace the full list.
- This is an ordinary `write` operation and does not require CLI confirmation.
- PATCH does NOT support `--auto-rename`; a name conflict returns `409`.

## Command
```bash
# Rename
ae-cli agent +update-agent --id <agent-cuid> --name "new-name"

# Replace instructions from stdin
echo "You are now a code reviewer..." | \
  ae-cli agent +update-agent --id <agent-cuid> --instructions @-

# Swap model and MCP list
ae-cli agent +update-agent \
  --id <agent-cuid> \
  --model-id "cm1newuuid" \
  --mcp-ids '["mcp-cuid-new"]'

# Enable a system/company Agent (writes personal preference)
ae-cli agent +update-agent --id <agent-cuid> --enabled true

# Disable
ae-cli agent +update-agent --id <agent-cuid> --enabled false

# Dry-run to inspect the request before executing
ae-cli agent +update-agent --dry-run --id <agent-cuid> --name "new-name"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Agent record ID (CUID) |
| `--name` | No | New Agent name (1–100 chars) |
| `--description` | No | New description (max 2000 chars) |
| `--instructions` | No | New system prompt (use `@-` to read from stdin) |
| `--model-id` | No | New model identifier (uuid or legacy modelId); omit to keep |
| `--mcp-ids` | No | MCP server record IDs as JSON array string (replaces the list; `[]` clears) |
| `--skill-ids` | No | Skill record IDs as JSON array string (replaces the list; `[]` clears) |
| `--enabled` | No | `true` to enable, `false` to disable (system/company: personal preference) |

## Decision Rules
- Confirm the Agent ID with `+list-agents` (or `+get-agent`) before updating.
- `--enabled` is optional; omit it to leave the enabled state unchanged. Pass `--enabled true` / `--enabled false` explicitly to toggle.
- `--mcp-ids` / `--skill-ids` replace the entire list on update — pass the full new set, not just additions.
- Use `--dry-run` first to verify the request shape before executing.
- To rename safely without `409`, check for name conflicts first or use `+create-agent --auto-rename` (PATCH has no auto-rename).

## Next Steps on Failure
- `404` / `Agent 不存在`: re-run `+list-agents` to verify the Agent ID.
- `403` / `无权编辑该 Agent`: the Agent is not yours and you are not root.
- `409` / `NAME_EXISTS`: pick a different `--name` (PATCH cannot auto-rename).
- `模型不存在或已删除`: verify the model ID with `+list-models`.

## Recommended Chaining
- `+list-agents` → confirm `id` → `+update-agent` → `+get-agent` (verify)
