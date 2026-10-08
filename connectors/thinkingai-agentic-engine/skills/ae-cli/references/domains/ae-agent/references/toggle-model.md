# agent +toggle-model (Toggle Model)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Models / write**

## Use Cases
- Enable or disable a model.
- Toggle operations on company/system resources only affect the current user's preference, not the global state.

## Mandatory Rules (MUST)
- `--id` and `--enabled` are required.
- Obtain the real model record ID (CUID) via `+list-models` — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli agent +toggle-model --id <model-cuid> --enabled true
ae-cli agent +toggle-model --id <model-cuid> --enabled false
ae-cli agent +toggle-model --dry-run --id <model-cuid> --enabled false
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Model record ID (CUID) |
| `--enabled` | Yes | `true` to enable, `false` to disable |

## Decision Rules
- If the user wants to turn a model on/off, use `--enabled true` / `--enabled false`.
- Toggling a company/system model only changes the current user's preference.

## Next Steps on Failure
- `404` / not found: re-run `+list-models` to verify the model ID.

## Recommended Chaining
- `+list-models` → confirm `id` → `+toggle-model`
