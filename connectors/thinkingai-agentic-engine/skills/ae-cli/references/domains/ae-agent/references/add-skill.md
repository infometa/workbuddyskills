# agent +add-skill (Create Custom Skill)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases

- Create a custom Skill in the personal or company scope.
- Returns the newly created Skill object including its `id`.
- `--scope personal` (default) creates a personal Skill; `--scope company` creates a company Skill (requires root/agent_admin). Company scope bypasses the submit-approve flow — the Skill is directly created as a company asset (consistent with `+upload-skill --scope company`).
- Optional market meta (`--category` / `--icon-emoji` / `--icon-color`) is applied via a follow-up PATCH to `/api/sandbox/agent/skills/[id]/meta`.

## Mandatory Rules (MUST)

- `--name`, `--description`, and `--instructions` are required.
- `--name` must be 1–80 chars.
- `--instructions` supports `@-` to read from stdin (useful for piping long instruction text).
- `--category` must be one of the market category keys (see below) when provided.
- `--scope` controls target scope: `personal` (default) or `company`. Company scope requires root/agent_admin and bypasses the submit-approve flow (directly creates a company Skill, consistent with `+upload-skill --scope company`).
- This is an ordinary `write` operation and does not require CLI confirmation.

## Market Category Keys

`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command

```bash
# Inline instructions
ae-cli agent +add-skill \
  --name code-reviewer \
  --description "Reviews code for best practices" \
  --instructions "You are a code reviewer. Analyze the code for..."

# Instructions from stdin (useful for long text)
echo "You are a helpful assistant that..." | \
  ae-cli agent +add-skill --name helper --description "Helper skill" --instructions @-

# With market category and icon
ae-cli agent +add-skill \
  --name code-reviewer \
  --description "Reviews code for best practices" \
  --instructions "You are a code reviewer..." \
  --category dev_tool \
  --icon-emoji robot

# Dry-run to inspect the request before executing
ae-cli agent +add-skill --dry-run --name helper --description "Helper" --instructions "x"

# Create with an explicit initial content version
ae-cli agent +add-skill --name helper --description "Helper" --instructions "x" --version 1.0
```

## Parameters

| Parameter        | Required | Description                                                                                               |
| ---------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `--name`         | Yes      | Skill name (1–80 chars)                                                                                   |
| `--description`  | Yes      | Skill description                                                                                         |
| `--instructions` | Yes      | Skill instructions (use `@-` to read from stdin)                                                          |
| `--version`      | No       | Initial content version in `major.minor` format; defaults to `1.0`                                        |
| `--display-name` | No       | Display name (max 100)                                                                                    |
| `--category`     | No       | Market category key (see above)                                                                           |
| `--icon-emoji`   | No       | Market icon emoji (e.g. `robot`)                                                                          |
| `--icon-color`   | No       | Market icon color (e.g. `#1E76F0`)                                                                        |
| `--scope`        | No       | Target scope: `personal` (default) or `company` (requires root/agent_admin; bypasses submit-approve flow) |

## Decision Rules

- If the user provides long instruction text, pipe it via stdin with `--instructions @-` instead of an oversized inline string.
- `--category` / `--icon-emoji` / `--icon-color` are optional market meta; they are applied via a follow-up PATCH after creation. If the meta update fails, the Skill is still created and a warning is printed to stderr.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure

- `stdin is empty; cannot read instructions`: ensure stdin has content when using `@-`.
- Warning `Skill created but meta update failed`: the Skill exists; retry the meta with `+set-skill-meta`.

## Recommended Chaining

- `+add-skill` → `+list-skills` (verify) → `+set-skill-meta` (adjust meta) → `+submit-skill` (publish) or `+share-skill` (peer share)
