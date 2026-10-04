# agent +submit-skill (Submit Skill for Approval)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Approval (company-scope publish) / write**

## Use Cases
- Submit a personal Skill for company-scope review.
- Endpoint: `POST /api/sandbox/agent/skills/[id]/submit`.
- Submitting writes a `SkillSubmit` row; the original personal Skill is untouched.
- Approval is Skill-only — MCP has no approval flow.
- Optional `--category` / `--icon-emoji` / `--icon-color` set the market meta proposed for the company copy.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **personal-scope** Skill (CUID). Obtain it via `+list-skills` — do not guess.
- `--description` is required (1–80 chars) — the submission reason.
- `--category` must be one of the market category keys (see below) when provided.
- This is an ordinary `write` operation and does not require CLI confirmation.
- After submission, the Skill enters `pending` status until a root user approves or rejects it.

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command
```bash
ae-cli agent +submit-skill --id <skill-cuid> --description "Code reviewer for the team"
ae-cli agent +submit-skill --id <skill-cuid> --description "Data query helper" --category data_query --icon-emoji robot
ae-cli agent +submit-skill --dry-run --id <skill-cuid> --description "Test submit"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID, personal scope) |
| `--description` | Yes | Submission reason / description (1–80 chars) |
| `--category` | No | Market category key (see above) |
| `--icon-emoji` | No | Market icon emoji (e.g. `robot`) |
| `--icon-color` | No | Market icon color (e.g. `#1E76F0`) |

## Decision Rules
- If the user wants to publish a personal Skill to the company, use `+submit-skill`.
- `--id` here is a Skill ID (not a submission ID) — `+cancel-skill-submission` / `+approve-skill` / `+reject-skill` take a submission ID instead.
- Only personal-scope Skills can be submitted; company/system Skills are not submittable.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `--description length must be between 1 and 80`: shorten the description.
- `404` / not found: re-run `+list-skills --scope personal` to verify the Skill ID.

## Recommended Chaining
- `+list-skills` (personal) → `+submit-skill` → `+list-skill-submissions` (track) → root: `+approve-skill` / `+reject-skill`
