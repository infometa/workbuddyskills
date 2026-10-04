# team +run-result (Get TeamRun Result)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / read**

## Use Cases
- Retrieve the full result of a TeamRun, including all steps, events, status, and output.
- The primary command for polling run progress after `+run-start` or `+run-chat`.
- Returns the run object with `status`, `output`, `steps`, and `error` (if failed).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real run ID from a previous `+run-start` or `+run-chat` response — do not guess.
- Poll this command repeatedly until `status` reaches a terminal value: `completed`, `failed`, or `cancelled`.
- Do not call `+run-artifacts` until status is `completed`.

## Command
```bash
ae-cli team +run-result --id <run_id>
ae-cli team +run-result --id <run_id> --jq '.status'
ae-cli team +run-result --dry-run --id <run_id>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | TeamRun ID |

## Key Response Fields

| Field | Type | Description |
|---|---|---|
| `status` | string | Current run status |
| `output` | string \| null | Final output (populated when `completed`) |
| `pendingQuestion` | string \| null | The question the team is asking the user; only populated when `status = waiting_user` |
| `error` | object \| null | Error details when `status = failed` |
| `steps` | array | All execution steps and events |

## Status Transitions
```
pending → running → completed
                 → waiting_user → (reply) → running → completed
                 → failed
                 → cancelled
```

Terminal statuses (stop polling): `completed`, `failed`, `cancelled`

Non-terminal statuses (keep polling): `pending`, `running`, `waiting_approval`, `paused`

Interrupt statuses (stop polling, get user input): `waiting_user`

## Decision Rules
- Check `status` field on each poll. Continue until terminal.
- If `status = waiting_user`: read `pendingQuestion`, present it to the user, collect the answer, then call `+run-reply --id <run_id> --input "<user_answer>"`. Resume polling after reply.
- If `status = failed`, inspect the `error` field to diagnose the issue.
- If `status = completed`, proceed to `+run-artifacts` to retrieve produced files/outputs.
- Use `--jq '{status,pendingQuestion}'` when polling to get both status and the pending question in one call.

## Polling Best Practice
```bash
# Lightweight status + pendingQuestion check
ae-cli team +run-result --id <run_id> --jq '{status,pendingQuestion}'

# Full result when completed
ae-cli team +run-result --id <run_id>
```

## Next Steps on Failure
- `404`: run ID not found — verify from the original start response.
- `status = failed`: report the `error.message` to the user and ask whether to retry with `+run-start`.

## Recommended Chaining
- `+run-start` or `+run-chat` → poll `+run-result` → terminal → `+run-artifacts`
- `+run-result` → `waiting_user` → `+run-reply` → continue polling `+run-result`
