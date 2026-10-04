# team +run-reply (Reply to Waiting TeamRun)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / write**

## Use Cases
- Provide a user reply to a TeamRun that is paused in `waiting_user` state.
- After reply, the run resumes execution automatically.

## Mandatory Rules (MUST)
- `--id` is required. The run **must be in `waiting_user` state** — sending a reply to a run in any other state will fail.
- `--input` is required (1–50000 chars). Pass the user's reply verbatim.
- This is an ordinary `write` operation and does not require CLI confirmation.
- After replying, poll `+run-result` until the run reaches a terminal status.

## Command
```bash
ae-cli team +run-reply --id <run_id> --input "请继续，使用方案A"
ae-cli team +run-reply --id <run_id> --input "好的，请重点分析周末下降原因"
ae-cli team +run-reply --dry-run --id <run_id> --input "test"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | TeamRun ID (must be in `waiting_user` state) |
| `--input` | Yes | User reply content (1–50000 chars) |

## Decision Rules
- Before calling `+run-reply`, always verify the run is in `waiting_user` state via `+run-result`.
- If the run is in `running` state (not yet paused), wait and poll again — do not send a reply prematurely.
- If the run is in a terminal state, it cannot be replied to — start a new run if needed.

## Next Steps on Failure
- `400` / wrong state: check the run status with `+run-result` first.
- `404`: run ID not found — verify from the original start response.

## Recommended Chaining
- `+run-result` (confirm `waiting_user`) → `+run-reply` → poll `+run-result` → `+run-artifacts`
- In chat mode: `+run-chat` → status `waiting_user` → `+run-reply` → `+run-chat` (next turn)
