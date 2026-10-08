# agent +create-agent (Create Agent)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Agents / write**

## Use Cases
- Create a new Agent in the personal scope (default) or company scope (requires root/agent_admin).
- Returns the newly created Agent object including its `id`.
- Wire up an existing model, MCP servers, and Skills in one call.

## Mandatory Rules (MUST)
- `--name` is required (1–100 chars).
- `--scope` defaults to `personal`; `company` requires root/agent_admin privileges.
- `--instructions` maps to the Agent's system prompt; supports `@-` to read from stdin.
- `--mcp-ids` / `--skill-ids` must be JSON array strings when provided.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Do not guess model / MCP / Skill IDs. Discover them with `+list-*` commands first.

## Command
```bash
# Minimal create
ae-cli agent +create-agent --name "daily-report" --description "Daily report agent"

# With model, MCP servers, and Skills
ae-cli agent +create-agent \
  --name "daily-report" \
  --description "Daily report agent" \
  --model-id "cm1uuid" \
  --mcp-ids '["mcp-cuid-1","mcp-cuid-2"]' \
  --skill-ids '["skill-cuid-1"]'

# Instructions from stdin (useful for long prompts)
echo "You are a helpful assistant that..." | \
  ae-cli agent +create-agent --name helper --instructions @-

# Auto-rename on name conflict (appends -1, -2, ...)
ae-cli agent +create-agent --name "daily-report" --auto-rename

# Dry-run to inspect the request before executing
ae-cli agent +create-agent --dry-run --name "daily-report" --description "x"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--name` | Yes | Agent name (1–100 chars) |
| `--description` | No | Agent description (max 2000 chars) |
| `--instructions` | No | Agent system prompt (use `@-` to read from stdin) |
| `--scope` | No | `personal` \| `company` (default `personal`; `company` requires root/agent_admin) |
| `--model-id` | No | Model identifier (`Model.id` uuid or legacy `modelId`); omit to use the global default |
| `--mcp-ids` | No | MCP server record IDs as JSON array string (e.g. `["id1","id2"]`) |
| `--skill-ids` | No | Skill record IDs as JSON array string |
| `--auto-rename` | No | Auto-rename on name conflict (append `-N` suffix) |

## Decision Rules
- If the user provides long instruction text, pipe it via stdin with `--instructions @-` instead of an oversized inline string.
- `--model-id` accepts both the model record UUID and the legacy model identifier; the server resolves and stores the UUID. Omit it to use the global default model.
- `--mcp-ids` / `--skill-ids` replace the full list on create; pass `[]` or omit to leave the list empty.
- Use `--dry-run` first to verify the request shape before executing.
- On name conflict, the server returns `409 NAME_EXISTS`; pass `--auto-rename` to auto-resolve.

## Next Steps on Failure
- `Agent 名称已存在` (409): re-run with `--auto-rename`, or pick a different `--name`.
- `模型不存在或已删除`: verify the model ID with `+list-models`.
- `MCP 数量超过上限` / `Skill 数量超过上限`: reduce the IDs in `--mcp-ids` / `--skill-ids`.
- `stdin is empty; cannot read instructions`: ensure stdin has content when using `@-`.

## Recommended Chaining
- `+list-models` / `+list-mcps` / `+list-skills` (discover IDs) → `+create-agent` → `+get-agent` (verify) → `+create-automation --agent-id <id>`
