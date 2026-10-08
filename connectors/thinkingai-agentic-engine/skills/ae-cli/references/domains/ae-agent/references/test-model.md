# agent +test-model (Test Model Connectivity)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Models / read**

## Use Cases
- Test whether a model endpoint is reachable and the credentials are valid (LLM models only).
- Probe a brand-new config (with `--api-key`) or reuse the stored key of an existing model (`--id`).
- Run this before `+update-model --connectivity-verified true` to confirm connection changes.

## Mandatory Rules (MUST)
- `--model-id` and `--base-url` are required.
- `--base-url` must be a valid URL.
- Only LLM-type models can be tested; other provider types return `400`.
- Read operation — no confirmation prompt (the test does not modify any state).

## Command
```bash
# Test a brand-new config with an explicit key
ae-cli agent +test-model \
  --model-id gpt-4o \
  --base-url "https://api.openai.com/v1" \
  --api-key "sk-xxx" \
  --provider openai

# Test an existing model's stored key (--id reuses the decrypted key)
ae-cli agent +test-model \
  --model-id gpt-4o \
  --base-url "https://api.openai.com/v1" \
  --id <model-cuid>

# Dry-run to inspect the request before executing
ae-cli agent +test-model --dry-run \
  --model-id gpt-4o \
  --base-url "https://api.openai.com/v1"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--model-id` | Yes | Model identifier (e.g. `gpt-4o`) |
| `--base-url` | Yes | API base URL (must be a valid URL) |
| `--api-key` | No | API key; omit to reuse the stored key of `--id` |
| `--provider` | No | Provider name |
| `--id` | No | Existing model config ID; when `--api-key` is omitted, the stored key is decrypted and reused |

## Decision Rules
- When testing a model that already exists (e.g. before `+update-model`), pass `--id <existing-cuid>` and omit `--api-key` to reuse the stored key.
- When testing a brand-new config, pass `--api-key` (and optionally `--provider`).
- A successful test returns `{ "ok": true }`; a failure returns `{ "ok": false, "message": "<reason>" }` with a localized message.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `--base-url must be a valid URL`: check the URL formatting.
- `仅支持 LLM 类型模型测试` (400): the provider maps to a non-LLM type (e.g. embedding) and cannot be tested via this endpoint.
- `{ "ok": false, "message": "..." }`: the endpoint was unreachable or rejected the credentials. Fix the URL/key/provider and retry.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-models` → confirm `id` → `+test-model --id <cuid>` (verify) → `+update-model --connectivity-verified true`
