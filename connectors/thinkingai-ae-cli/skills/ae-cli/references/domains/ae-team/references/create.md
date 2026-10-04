# team +create (Create Team)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team management / write**

## Use Cases
- Create a new AI Agent team with a given name and TeamConfig.
- Returns the newly created team object including its `id`.

## Mandatory Rules (MUST)
- `--config` must be a valid TeamConfig JSON (see structure below). Do not invent `agentId`, `mcpServerIds`, `skillIds`, or `knowledgeBaseIds` — obtain real IDs from the user or the appropriate resource discovery commands.
- `--name` must be 1–100 characters.
- `--description` must be ≤2000 characters if provided.
- `--scope` must be `personal` or `company` if provided; defaults to `personal` on the server.
- This is an ordinary `write` operation and does not require CLI confirmation.

## TeamConfig Structure

```json
{
  "version": 1,
  "mode": "serial | parallel | leader",
  "steps": [
    {
      "id": "s1",
      "name": "Step name",
      "agentId": "<real agent ID>",
      "prompt": "Step instructions (≤50000 chars)",
      "role": "agent | leader | reviewer",
      "retryLimit": 2,
      "dependencies": [],
      "resourceOverride": {
        "mcpServerIds": [],
        "skillIds": [],
        "knowledgeBaseIds": [],
        "model": null
      }
    }
  ],
  "maxConcurrency": 5,
  "output": {
    "format": "markdown | json | xlsx | pptx | pdf | docx"
  }
}
```

**Mode constraints:**
- `serial` / `parallel`: `steps` ≥ 1
- `leader`: `steps` ≥ 2 (all `role: "agent"`), requires `leaderConfig`

**leaderConfig** (required when `mode: "leader"`):
```json
"leaderConfig": {
  "agentId": "<leader agent ID>",
  "maxIterations": 10,
  "availableAgents": [
    { "id": "a1", "agentId": "...", "name": "...", "description": "...", "capabilities": "..." }
  ]
}
```

## Command
```bash
ae-cli team +create \
  --name "日报分析团队" \
  --config '{"version":1,"mode":"serial","steps":[{"id":"s1","name":"分析师","agentId":"xxx","prompt":"分析数据","role":"agent"}]}'

ae-cli team +create --name "My Team" --config '...' --scope company
ae-cli team +create --dry-run --name "Test" --config '{}'
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--name` | Yes | Team name (1–100 chars) |
| `--config` | Yes | TeamConfig JSON object |
| `--description` | No | Description (≤2000 chars) |
| `--scope` | No | `personal` (default) \| `company` |
| `--enabled` | No | `true` (default) \| `false` |

## Decision Rules
- If the user provides a goal description instead of a config, call `+ai-generate` first to get a draft, then ask the user to review before calling `+create`.
- If the user wants to base a team on a template, call `+list-templates` first to get the template config.
- Always use `--dry-run` first when building a complex config to verify the request shape before executing.

## Next Steps on Failure
- `Invalid JSON`: check TeamConfig structure, especially `version`, `mode`, `steps[].id`, `steps[].agentId`.
- `400 / validation error`: verify that `mode` constraints are satisfied (e.g. `leader` requires `leaderConfig`).
- After success, capture the returned `id` for subsequent `+run-start` calls.

## Recommended Chaining
- `+ai-generate` → review draft → `+create` → `+run-start`
- `+list-templates` → pick template config → `+create` → `+run-start`
