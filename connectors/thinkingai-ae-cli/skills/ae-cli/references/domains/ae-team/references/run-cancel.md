# team +run-cancel (Cancel TeamRun)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / write**

## Use Cases
- Cancel a TeamRun that is in `pending`, `running`, or `waiting_user` state.
- After cancellation, the run transitions to `cancelled` (a terminal status).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real run ID from a previous `+run-start` or `+run-chat` response — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Cancellation is irreversible. To re-run the same task, call `+run-start` again.

## Command
```bash
ae-cli team +run-cancel --id <run_id>
ae-cli team +run-cancel --id <run_id>
ae-cli team +run-cancel --dry-run --id <run_id>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | TeamRun ID |

## Decision Rules
- Before cancelling, verify the run status with `+run-result` to confirm it is not already in a terminal state (`completed`, `failed`, `cancelled`).
- If the user wants to delete a team that has active runs, cancel all active runs first, then call `+delete`.

## Next Steps on Failure
- `404`: run ID not found — verify the run ID from the original start response.
- Already terminal: the run has already completed, failed, or been cancelled — no action needed.

## Recommended Chaining
- `+run-result` (verify status) → `+run-cancel`
- `+run-cancel` (clear active runs) → `+delete` (team)
