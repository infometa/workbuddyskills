# agent +list-skill-scripts (List Skill Scripts)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- List all files in a Skill's `scripts` directory.
- Endpoint: `GET /api/sandbox/agent/skills/[id]/scripts`.
- Returns `{ items: [...] }` with file metadata (name, size, etc.).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.

## Command
```bash
ae-cli agent +list-skill-scripts --id <skill-cuid>
ae-cli agent +list-skill-scripts --dry-run --id <skill-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |

## Decision Rules
- Use `+list-skills` to confirm the Skill ID before listing scripts.
- Read operation: no confirmation prompt needed.
- Scripts are executable files that support the Skill's functionality.

## Next Steps on Failure
- `404` / not found: re-run `+list-skills` to verify the Skill ID and scope.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+list-skill-scripts` → `+read-skill-script` or `+upload-skill-script`
