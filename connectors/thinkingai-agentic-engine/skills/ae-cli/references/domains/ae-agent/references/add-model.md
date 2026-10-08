# agent +add-model (Add Custom Model)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Models / write**

## Use Cases
- Add a custom model to the personal or company scope.
- Returns the newly created model object including its `id`.
- `--scope personal` (default) creates a personal model; `--scope company` creates a company model (requires root/agent_admin).

## Mandatory Rules (MUST)
- `--model-id`, `--name`, and `--base-url` are required.
- `--base-url` must be a valid URL.
- `--scope` controls target scope: `personal` (default) or `company`. Company scope requires root/agent_admin; system models are read-only.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli agent +add-model \
  --model-id gpt-4o \
  --name "GPT-4o" \
  --base-url "https://api.openai.com/v1" \
  --api-key "sk-xxx" \
  --provider openai

ae-cli agent +add-model \
  --model-id claude-sonnet \
  --name "Claude Sonnet" \
  --base-url "https://api.anthropic.com/v1" \
  --provider anthropic \
  --context-length 200000

# Dry-run to inspect the request before executing
ae-cli agent +add-model --dry-run --model-id gpt-4o --name "GPT-4o" --base-url "https://api.openai.com/v1"

# Company scope (requires root/agent_admin)
ae-cli agent +add-model \
  --model-id gpt-4o-company \
  --name "GPT-4o (company)" \
  --base-url "https://api.openai.com/v1" \
  --provider openai \
  --scope company
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--model-id` | Yes | Model identifier (e.g. `gpt-4o`) |
| `--name` | Yes | Display name |
| `--base-url` | Yes | API base URL (must be a valid URL) |
| `--api-key` | No | API key |
| `--provider` | No | Provider name |
| `--description` | No | Description |
| `--context-length` | No | Context window length |
| `--scope` | No | Target scope: `personal` (default) or `company` (requires root/agent_admin) |

## Decision Rules
- If the user provides a model spec, map the model identifier to `--model-id` and the human name to `--name`.
- `--api-key` is optional at the CLI level but usually required by the upstream provider; pass it when the user supplies one.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `--base-url must be a valid URL`: check the URL formatting.
- After success, capture the returned `id` for `+toggle-model` / `+del-model` calls.

## Recommended Chaining
- `+list-models` (verify) → `+add-model` → `+toggle-model` (enable) → `+create-automation --model <id>`
