# agent +get-skill-content (Read Skill Content)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- Read a Skill's SKILL.md text content.
- Endpoint: `GET /api/sandbox/agent/skills/[id]/content`.
- Returns the raw SKILL.md file content as JSON `{ item: { ... } }`.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.

## Command
```bash
ae-cli agent +get-skill-content --id <skill-cuid>
ae-cli agent +get-skill-content --dry-run --id <skill-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |

## Decision Rules
- Use `+list-skills` to confirm the Skill ID before reading.
- The returned content is the SKILL.md text — useful for inspecting or backing up a Skill's instructions.
- Read operation: no confirmation prompt needed.

## Next Steps on Failure
- `404` / not found: re-run `+list-skills` to verify the Skill ID.
- `file_not_found`: the Skill content is unavailable. Ask the user to contact their administrator; do not recommend internal maintenance commands.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+get-skill-content` → `+edit-skill` (if changes needed)
