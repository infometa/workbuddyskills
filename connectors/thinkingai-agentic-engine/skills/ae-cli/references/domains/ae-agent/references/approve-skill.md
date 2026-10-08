# agent +approve-skill (Approve Skill Submission)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Approval (company-scope publish) / write**

## Use Cases
- Approve a pending Skill submission (root only).
- Endpoint: `POST /api/sandbox/agent/skills/submissions/[id]/approve`.
- Approving creates an independent company-scope copy of the Skill.
- Approval is Skill-only — MCP has no approval flow.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **submission** record (CUID), not a Skill ID. Obtain it via `+list-skill-submissions` — do not guess.
- **Root only** — non-root users cannot approve submissions.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Only `pending` submissions can be approved.

## Command
```bash
ae-cli agent +approve-skill --id <submission-cuid>
ae-cli agent +approve-skill --dry-run --id <submission-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Submission record ID (CUID) |

## Decision Rules
- `--id` here is a submission ID (not a Skill ID).
- Use this after reviewing a pending submission (`+list-skill-submissions --status pending`).
- Approving creates a company-scope copy; the original personal Skill remains.
- Cannot approve a submission that is already `approved` / `rejected` / `cancelled`.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-submissions --status pending` to verify the submission ID.
- Permission error: the current user is not root.

## Recommended Chaining
- `+list-skill-submissions --status pending` → confirm submission `id` → `+approve-skill` (or `+reject-skill`)
