# agent +edit-skill (Edit Skill Content)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases

- Edit a personal Skill's content (name, description, instructions, display name, category, icon).
- Endpoint: `PUT /api/sandbox/agent/skills/[id]`.
- Only `personal` scope Skills can be edited via CLI.

## Mandatory Rules (MUST)

- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- At least one editable field must be provided (`--name` / `--description` / `--instructions` / `--display-name` / `--category` / `--icon-emoji` / `--icon-color`).
- `--name` must be 1–80 chars when provided.
- `--instructions` supports `@-` to read from stdin (useful for piping long instruction text).
- `--category` must be one of the market category keys when provided.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Market Category Keys

`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command

```bash
# Edit instructions only
ae-cli agent +edit-skill --id <skill-cuid> --instructions "Updated instructions..." --version 1.1

# Edit name and description
ae-cli agent +edit-skill --id <skill-cuid> --name new-name --description "New description" --version 2.0

# Instructions from stdin
echo "You are a helpful assistant..." | \
  ae-cli agent +edit-skill --id <skill-cuid> --instructions @- --version 1.1

# Dry-run to inspect the request before executing
ae-cli agent +edit-skill --dry-run --id <skill-cuid> --name new-name --version 2.0
```

## Parameters

| Parameter        | Required                | Description                                                                                                           |
| ---------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `--id`           | Yes                     | Skill record ID (CUID)                                                                                                |
| `--version`      | Yes for content changes | New `major.minor` version. It must be higher than the current version when name, description, or instructions change. |
| `--name`         | No*                     | New Skill name (1–80 chars)                                                                                           |
| `--description`  | No*                     | New Skill description                                                                                                 |
| `--instructions` | No*                     | New instructions (use `@-` to read from stdin)                                                                        |
| `--display-name` | No*                     | New display name (max 100)                                                                                            |
| `--category`     | No*                     | Market category key (see above)                                                                                       |
| `--icon-emoji`   | No*                     | Market icon emoji (e.g. `robot`)                                                                                      |
| `--icon-color`   | No*                     | Market icon color (e.g. `#1E76F0`)                                                                                    |

\* At least one of these must be provided.

## Decision Rules

- Use `+list-skills` to confirm the Skill ID before editing.
- If the user provides long instruction text, pipe it via stdin with `--instructions @-`.
- Use `--dry-run` first to verify the request shape before executing.
- Editing a Skill does not change its scope; company/system Skills are read-only via CLI.
- Display name, category, and icon-only changes do not create a content version and do not require `--version`.

## Next Steps on Failure

- `404` / not found: re-run `+list-skills` to verify the Skill ID and scope.
- `409` / name conflict: use `--name` with a different name, or consider `+upload-skill` with `--auto-rename`.
- `SKILL_VERSION_CONFLICT`: read `meta.currentVersion`, choose a strictly higher `major.minor` value, and retry the same command with `--version`.
- `SKILL_HISTORY_CONFLICT`: stop retrying and tell the user, "The Skill cannot be safely updated right now. Please contact your administrator."
- Do not recommend internal maintenance commands or expose diagnostic payloads in a customer-facing response.

## Recommended Chaining

- `+list-skills` → confirm `id` → `+edit-skill` → `+get-skill-content` (verify)
