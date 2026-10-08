# team +delete (Delete Team)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team management / write**

## Use Cases
- Permanently delete a team by ID.
- Returns `{ "ok": true }` on success.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real team ID via `+list` — do not guess.
- If the team has running tasks, the server returns **409**. Cancel or wait for active runs before retrying.
- This is an irreversible operation — confirm with the user before executing.

## Command
```bash
ae-cli team +delete --id <team_id> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli team +delete --id <team_id> --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Team ID |

## Decision Rules
- Always call `+list` first to confirm the `id` and that the user is targeting the correct team.
- If the server returns 409, call `+run-result` on active runs to check their status, then use `+run-cancel` to cancel any `running` or `waiting_user` runs.
- Do not retry delete until all active runs have reached a terminal status.

## Next Steps on Failure
- `409 Conflict`: cancel active runs first (`+run-cancel --id <run_id>`), then retry.
- `404`: team already deleted or wrong ID — re-run `+list` to verify.

## Recommended Chaining
- `+list` → confirm target → `+delete`
- `+run-cancel` (clear active runs) → `+delete`
