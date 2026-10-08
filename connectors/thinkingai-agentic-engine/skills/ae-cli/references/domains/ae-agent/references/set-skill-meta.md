# agent +set-skill-meta (Set Skill Market Meta)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Category & Icon (meta) / write**

## Use Cases
- Update a Skill's market category and/or icon.
- Endpoint: `PATCH /api/sandbox/agent/skills/[id]/meta`.
- Company scope requires root; system scope is read-only.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- At least one of `--category` / `--icon-emoji` / `--icon-color` must be provided.
- `--category` must be one of the market category keys (see below) when provided.
- Company scope meta requires root; system scope meta is read-only.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command
```bash
ae-cli agent +set-skill-meta --id <skill-cuid> --category data_query
ae-cli agent +set-skill-meta --id <skill-cuid> --icon-emoji robot --icon-color "#1E76F0"
ae-cli agent +set-skill-meta --dry-run --id <skill-cuid> --category dev_tool
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--category` | No* | Market category key (see above) |
| `--icon-emoji` | No* | Market icon emoji (e.g. `robot`) |
| `--icon-color` | No* | Market icon color (e.g. `#1E76F0`) |

\* At least one of these three must be provided.

## Decision Rules
- If the user wants to change a Skill's market category or icon, use this.
- For company-scope Skills, only root users can set meta; for system-scope, meta is read-only.
- `+add-skill` and `+copy-skill` also accept `--category` / `--icon-emoji` / `--icon-color`; use `+set-skill-meta` to adjust them afterwards.

## Next Steps on Failure
- `Provide at least one of --category / --icon-emoji / --icon-color`: add at least one meta field.
- `--category must be one of...`: use one of the category keys.
- Permission error on company scope: the current user is not root.

## Recommended Chaining
- `+list-skills` → confirm `id` → `+set-skill-meta`
- `+add-skill` / `+copy-skill` → `+set-skill-meta` (adjust meta after creation/copy)
