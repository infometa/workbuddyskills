# agent +list-skill-submissions (List Skill Submissions)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Approval (company-scope publish) / read**

## Use Cases
- List Skill submissions (approvals).
- Endpoint: `GET /api/sandbox/agent/skills/submissions`.
- Root sees all company submissions; non-root users see only their own.
- Use this to find a submission ID before `+cancel-skill-submission` / `+approve-skill` / `+reject-skill`.

## Mandatory Rules (MUST)
- `--status` must be one of the submission statuses (see below) when provided.
- Do not guess submission IDs. Always call `+list-skill-submissions` first when a submission ID is needed.

## Submission Statuses
`pending | approved | rejected | cancelled`

## Command
```bash
ae-cli agent +list-skill-submissions
ae-cli agent +list-skill-submissions --status pending --format table
ae-cli agent +list-skill-submissions --mine
ae-cli agent +list-skill-submissions --dry-run --status pending
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--status` | No | Filter by status (see above) |
| `--mine` | No | Only show submissions created by the current user (root only) |

## Decision Rules
- When the user wants to review pending submissions, use `--status pending`.
- Root users can see all company submissions; non-root users only see their own.
- `--mine` (root only) filters to the current user's own submissions.
- Capture the submission `id` for `+cancel-skill-submission` / `+approve-skill` / `+reject-skill`.

## Next Steps on Failure
- `--status must be one of...`: use one of the submission statuses.
- Empty result: no submissions match the filter.

## Recommended Chaining
- `+list-skill-submissions` → confirm submission `id` → `+cancel-skill-submission` (submitter/root) or `+approve-skill` / `+reject-skill` (root)
