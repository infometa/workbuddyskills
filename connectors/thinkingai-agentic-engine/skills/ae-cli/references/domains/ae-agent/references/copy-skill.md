# agent +copy-skill (Copy Skill to Personal)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Copy to personal / write**

## Use Cases
- Copy a system/company Skill to an independent personal copy.
- Endpoint: `POST /api/sandbox/agent/skills/[id]/copy`.
- The copy is an independent duplicate — changes to the source do not affect the copy and vice versa.
- Optional `--category` / `--icon-emoji` / `--icon-color` override the copy's market meta; omit them to inherit the source's.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real source Skill record ID (CUID, system or company scope) via `+list-skill-market` or `+list-skills` — do not guess.
- `--category` must be one of the market category keys (see below) when provided.
- This is an ordinary `write` operation and does not require CLI confirmation.
- MCP has no copy flow (use `+toggle-mcp` to enable a system/company MCP per-user).

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command
```bash
# Copy with inherited meta
ae-cli agent +copy-skill --id <skill-cuid>

# Copy with overridden category and icon
ae-cli agent +copy-skill --id <skill-cuid> --category dev_tool --icon-emoji robot

# Dry-run to inspect the request before executing
ae-cli agent +copy-skill --dry-run --id <skill-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Source Skill record ID (CUID, system or company scope) |
| `--category` | No | Market category key for the copy (see above) |
| `--icon-emoji` | No | Override market icon emoji (e.g. `robot`) |
| `--icon-color` | No | Override market icon color (e.g. `#1E76F0`) |

## Decision Rules
- If the user wants a personal version of a system/company Skill, use `+copy-skill` (not `+add-skill`).
- Omit `--category` / `--icon-emoji` / `--icon-color` to inherit the source's meta; provide them to override.
- MCP has no copy — to use a system/company MCP, toggle it on per-user with `+toggle-mcp`.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `--category must be one of...`: use one of the category keys.
- `404` / not found: re-run `+list-skill-market` / `+list-skills` to verify the source Skill ID and scope.

## Recommended Chaining
- `+list-skill-market` (browse) → `+copy-skill` (copy to personal) → `+list-skills` (verify) → `+set-skill-meta` (adjust)
