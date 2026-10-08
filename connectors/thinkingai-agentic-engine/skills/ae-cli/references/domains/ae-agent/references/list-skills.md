# agent +list-skills (List Skills)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- List Skills visible to the current user (personal / company / system scopes).
- Returns an array of Skill summaries; key fields include `id`, `name`, `description`, `scope`, `enabled`.

## Mandatory Rules (MUST)
- Do not guess Skill record IDs. Always call `+list-skills` first when an ID is needed.

## Command
```bash
ae-cli agent +list-skills
ae-cli agent +list-skills --scope personal --format table
ae-cli agent +list-skills --scope company
ae-cli agent +list-skills --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Filter by scope: `personal` \| `company` \| `system` |

## Decision Rules
- When the user needs a Skill ID for `+del-skill` / `+toggle-skill` / `+copy-skill` / `+submit-skill` / `+share-skill` / `+set-skill-meta`, call this first.
- Use `--format table` for a scannable overview of many skills.

## Next Steps on Failure
- Empty result: confirm account permissions and the active AE host.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+toggle-skill` / `+del-skill` / `+copy-skill` / `+submit-skill` / `+share-skill`
- `+list-skill-market` (browse) → `+add-skill` (create) → `+list-skills` (verify)
