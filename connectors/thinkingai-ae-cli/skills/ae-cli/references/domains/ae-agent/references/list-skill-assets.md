# agent +list-skill-assets (List Skill Assets)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- List all files in a Skill's `assets` directory.
- Endpoint: `GET /api/sandbox/agent/skills/[id]/assets`.
- Returns `{ items: [...] }` with file metadata (name, size, etc.).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.

## Command
```bash
ae-cli agent +list-skill-assets --id <skill-cuid>
ae-cli agent +list-skill-assets --dry-run --id <skill-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |

## Decision Rules
- Use `+list-skills` to confirm the Skill ID before listing assets.
- Read operation: no confirmation prompt needed.
- Assets include images, documents, and other supporting files for the Skill.

## Next Steps on Failure
- `404` / not found: re-run `+list-skills` to verify the Skill ID and scope.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+list-skill-assets` → `+read-skill-asset` or `+upload-skill-asset`
