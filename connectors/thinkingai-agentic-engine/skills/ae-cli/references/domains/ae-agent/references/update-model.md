# agent +update-model (Update Custom Model)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Models / write**

## Use Cases
- Update an existing custom model (the `--id` determines which record to update).
- All connection/display fields can be changed; `--api-key` may be omitted to preserve the stored key.
- Encouraged to verify connectivity with `+test-model` first, then pass `--connectivity-verified true`.
- `--scope` controls target scope: `personal` (default) or `company`. Company scope requires root/agent_admin.

## Mandatory Rules (MUST)
- `--id`, `--model-id`, `--name`, and `--base-url` are required.
- `--base-url` must be a valid URL.
- `--api-key` is optional; omit or leave empty to preserve the existing key (do NOT pass an empty string to clear — the stored key is kept).
- `--scope` controls target scope: `personal` (default) or `company`. Company scope requires root/agent_admin; system models are read-only.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Update display name and provider
ae-cli agent +update-model \
  --id <model-cuid> \
  --model-id gpt-4o \
  --name "GPT-4o (prod)" \
  --base-url "https://api.openai.com/v1" \
  --provider openai

# Rotate the API key
ae-cli agent +update-model \
  --id <model-cuid> \
  --model-id gpt-4o \
  --name "GPT-4o" \
  --base-url "https://api.openai.com/v1" \
  --api-key "sk-newkey" \
  --connectivity-verified true

# Dry-run to inspect the request before executing
ae-cli agent +update-model --dry-run \
  --id <model-cuid> \
  --model-id gpt-4o \
  --name "GPT-4o" \
  --base-url "https://api.openai.com/v1"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Model record ID (CUID) to update |
| `--model-id` | Yes | Model identifier (e.g. `gpt-4o`) |
| `--name` | Yes | Display name |
| `--base-url` | Yes | API base URL (must be a valid URL) |
| `--api-key` | No | API key; omit or empty to preserve the existing key |
| `--provider` | No | Provider name |
| `--description` | No | Description |
| `--context-length` | No | Context window length (positive integer) |
| `--connectivity-verified` | No | Whether connectivity was verified (default `false`; pass `true` after `+test-model`) |
| `--auto-rename` | No | Auto-rename on display name conflict (append `-N` suffix) |
| `--scope` | No | Target scope: `personal` (default) or `company` (requires root/agent_admin) |

## Decision Rules
- Confirm the model ID with `+list-models` before updating.
- To rotate the API key, pass `--api-key <new>`; to keep the stored key, simply omit `--api-key`.
- `--connectivity-verified` defaults to `false`. After a successful `+test-model`, pass `--connectivity-verified true` to confirm the new connection config.
- On display name conflict, the server returns `409`; pass `--auto-rename` to auto-resolve.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `模型不存在` (404): re-run `+list-models` to verify the model ID and scope.
- `模型名称已存在` (409): re-run with `--auto-rename`, or pick a different `--name`.
- `--base-url must be a valid URL`: check the URL formatting.
- `仅支持 LLM 类型模型测试` (from `+test-model`): the provider maps to a non-LLM type and cannot be tested.

## Recommended Chaining
- `+list-models` → confirm `id` → `+test-model` (verify connectivity) → `+update-model --connectivity-verified true` → `+list-models` (verify)
