# agent +toggle-skill (Toggle Skill)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases
- Enable or disable a Skill.
- Toggle operations on company/system resources only affect the current user's preference, not the global state.

## Mandatory Rules (MUST)
- `--id` and `--enabled` are required.
- Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli agent +toggle-skill --id <skill-cuid> --enabled true
ae-cli agent +toggle-skill --id <skill-cuid> --enabled false
ae-cli agent +toggle-skill --dry-run --id <skill-cuid> --enabled false
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--enabled` | Yes | `true` to enable, `false` to disable |

## Decision Rules
- If the user wants to turn a Skill on/off, use `--enabled true` / `--enabled false`.
- Toggling a company/system Skill only changes the current user's preference.

## Next Steps on Failure
- `404` / not found: re-run `+list-skills` to verify the Skill ID.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+toggle-skill`
