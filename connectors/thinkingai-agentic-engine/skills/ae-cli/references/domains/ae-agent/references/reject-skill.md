# agent +reject-skill (Reject Skill Submission)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Approval (company-scope publish) / write**

## Use Cases
- Reject a pending Skill submission with a reason (root only).
- Endpoint: `POST /api/sandbox/agent/skills/submissions/[id]/reject`.
- Approval is Skill-only — MCP has no approval flow.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **submission** record (CUID), not a Skill ID. Obtain it via `+list-skill-submissions` — do not guess.
- `--reason` is required (1–80 chars) — the rejection reason.
- **Root only** — non-root users cannot reject submissions.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Only `pending` submissions can be rejected.

## Command
```bash
ae-cli agent +reject-skill --id <submission-cuid> --reason "Needs more detail"
ae-cli agent +reject-skill --dry-run --id <submission-cuid> --reason "Needs more detail"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Submission record ID (CUID) |
| `--reason` | Yes | Rejection reason (1–80 chars) |

## Decision Rules
- `--id` here is a submission ID (not a Skill ID).
- Use this after reviewing a pending submission (`+list-skill-submissions --status pending`) when the submission should not be published.
- Cannot reject a submission that is already `approved` / `rejected` / `cancelled`.

## Next Steps on Failure
- `--reason length must be between 1 and 80`: adjust the reason length.
- `404` / not found: re-run `+list-skill-submissions --status pending` to verify the submission ID.
- Permission error: the current user is not root.

## Recommended Chaining
- `+list-skill-submissions --status pending` → confirm submission `id` → `+reject-skill` (or `+approve-skill`)
