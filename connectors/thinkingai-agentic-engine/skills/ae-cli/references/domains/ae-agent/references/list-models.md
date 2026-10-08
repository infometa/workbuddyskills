# agent +list-models (List Models)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Models / read**

## Use Cases
- List models visible to the current user (personal / company / system scopes).
- Returns an array of model summaries; key fields include `id`, `modelId`, `displayName`, `scope`, `enabled`.
- The current selected model (from the runtime env) is annotated when available.

## Mandatory Rules (MUST)
- Do not guess model record IDs. Always call `+list-models` first when a model ID is needed.

## Command
```bash
ae-cli agent +list-models
ae-cli agent +list-models --scope personal --format table
ae-cli agent +list-models --scope company
ae-cli agent +list-models --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Filter by scope: `personal` \| `company` \| `system` |

## Decision Rules
- When the user needs a model record ID for `+create-automation --model`, call this first.
- `--scope personal` shows only the user's own custom models; `company` / `system` show shared models.
- Use `--format table` for a scannable overview of many models.

## Next Steps on Failure
- Empty result: confirm account permissions and the active AE host.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-models` → confirm model ID → `+create-automation --model <id>` or `+toggle-model` / `+del-model`
