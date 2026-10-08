# agent +del-skill-script (Delete Skill Script)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases
- Delete a file from a Skill's `scripts` directory.
- Endpoint: `DELETE /api/sandbox/agent/skills/[id]/scripts/[...path]`.
- Physical delete — cannot be undone.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--path` is required and specifies the relative file path within the scripts directory.
- This is a **physical delete** — prefer `--dry-run` before executing.
- This is a high-risk-write operation; never execute it before the dry-run impact is explicitly confirmed.

## Command
```bash
ae-cli agent +del-skill-script --id <skill-cuid> --path helper.sh --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli agent +del-skill-script --id <skill-cuid> --path helper.sh --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--path` | Yes | Relative file path within scripts to delete |

## Decision Rules
- Use `+list-skill-scripts` to confirm the file path before deleting.
- This is a physical delete, not a soft delete — proceed only when the user clearly intends to remove it.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-scripts` to verify the file path.
- `文件不存在`: the file path does not exist in the scripts directory.

## Recommended Chaining
- `+list-skill-scripts` → confirm `path` → `+del-skill-script` → `+list-skill-scripts` (verify)
