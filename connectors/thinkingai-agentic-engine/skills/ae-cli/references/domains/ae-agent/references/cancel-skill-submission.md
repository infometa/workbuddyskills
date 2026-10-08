# agent +cancel-skill-submission (Cancel Skill Submission)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Approval (company-scope publish) / write**

## Use Cases
- Cancel a pending Skill submission.
- Endpoint: `POST /api/sandbox/agent/skills/submissions/[id]/cancel`.
- Only pending submissions can be cancelled; the submitter or root can cancel.
- Approval is Skill-only — MCP has no approval flow.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **submission** record (CUID), not a Skill ID. Obtain it via `+list-skill-submissions` — do not guess.
- Only the submitter or root can cancel a submission.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli agent +cancel-skill-submission --id <submission-cuid>
ae-cli agent +cancel-skill-submission --dry-run --id <submission-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Submission record ID (CUID) |

## Decision Rules
- `--id` here is a submission ID (not a Skill ID) — `+submit-skill` / `+share-skill` / `+copy-skill` take a Skill ID instead.
- Use this when the submitter wants to withdraw a pending submission before review.
- Cannot cancel a submission that is already `approved` / `rejected` / `cancelled`.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-submissions --status pending` to verify the submission ID.
- Permission error: only the submitter or root can cancel.

## Recommended Chaining
- `+list-skill-submissions --status pending` → confirm submission `id` → `+cancel-skill-submission`
