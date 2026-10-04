# agent +del-skill (Delete Personal Skill)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases
- Delete a personal-scope Skill (physical delete).
- Only `personal` scope Skills can be deleted via CLI; company/system Skills are read-only.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- This is a **physical delete** — prefer `--dry-run` before executing.
- This is a high-risk-write operation; never execute it before the dry-run impact is explicitly confirmed.

## Command
```bash
ae-cli agent +del-skill --id <skill-cuid> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli agent +del-skill --id <skill-cuid> --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |

## Decision Rules
- Confirm the Skill ID with `+list-skills` before deleting.
- This is a physical delete, not a soft delete — proceed only when the user clearly intends to remove it.
- If the Skill is company/system scope, deletion is not available via CLI (use `+toggle-skill` to disable it per-user instead).

## Next Steps on Failure
- `404` / not found: re-run `+list-skills` to verify the Skill ID and scope.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+del-skill`
