# team +run-watch (Stream TeamRun via SSE)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / read**

## Use Cases
- Stream real-time progress of a TeamRun without polling.
- Blocks until the run reaches a terminal state or `waiting_user`.
- Preferred over `+run-result` polling for all automated workflows.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real run ID from a previous `+run-start` or `+run-chat` response.
- Check the **exit code** to determine what happened — do not guess from output alone.
- When exit code is `2` (`waiting_user`): read `pendingQuestion` from stdout, present it to the user, collect their answer, call `+run-reply`, then re-run `+run-watch`.
- Network drops are handled automatically (up to 10 reconnects with 2s delay). Do NOT retry `+run-watch` on exit 1 unless you have confirmed the run itself failed via `+run-result`.

## Command
```bash
ae-cli team +run-watch --id <run_id>

# Suppress stderr log/status noise (stdout JSON is unaffected)
ae-cli team +run-watch --id <run_id> --quiet

# Reconnect after drop, skip logs already seen
ae-cli team +run-watch --id <run_id> --after-log <lastTimestamp>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | TeamRun ID |
| `--after-log` | No | Reconnect: skip log events at or before this timestamp |
| `--quiet` | No | Suppress log and status lines on stderr; stdout JSON is always emitted |

## Exit Codes
| Code | Meaning | Action |
|---|---|---|
| `0` | `completed` or `partial_success` | Proceed to `+run-artifacts` |
| `1` | `failed`, `cancelled`, `stale`, or connection error | Inspect `errorMessage` in stdout JSON; report to user |
| `2` | `waiting_user` | Read `pendingQuestion` from stdout JSON, present to user, then `+run-reply` → re-run `+run-watch` |

## Output
stdout always receives the final `TeamRunEntity` as a standard JSON envelope:
```json
{ "ok": true, "data": { "id": "...", "status": "...", "pendingQuestion": "...", ... } }
```
- Exit 0/1: the entity from the `final` SSE event (terminal state)
- Exit 2: the entity from the `update` SSE event at the moment `waiting_user` was detected

stderr receives real-time log lines and status changes (suppressed with `--quiet`).

## Handling waiting_user
```bash
# 1. Watch the run
ae-cli team +run-watch --id <run_id>
# exit code 2 → waiting_user

# 2. Read pendingQuestion from stdout, present to user, collect answer
# 3. Submit the reply
ae-cli team +run-reply --id <run_id> --input "<user_answer>"

# 4. Resume watching
ae-cli team +run-watch --id <run_id>
```

## SSE Events (reference)
| Event | Frequency | Payload |
|---|---|---|
| `snapshot` | Once on connect | `TeamRunEntity` |
| `update` | Every 500ms when changed | `TeamRunEntity` |
| `final` | On terminal state, then closes | `TeamRunEntity` |
| `log` | Real-time (with history replay) | `{ timestamp, stepId, type, content }` |
| `error` | On auth/read failure | `{ error: string }` |

## Next Steps on Failure
- Exit 1 + `status = failed`: read `errorMessage` in the JSON output; ask user whether to retry with `+run-start`.
- Connection drop before `final`: re-run `+run-watch --id <run_id> --after-log <lastTimestamp>`.

## Recommended Chaining
- `+run-start` → `+run-watch` → exit 0 → `+run-artifacts`
- `+run-watch` → exit 2 → `+run-reply` → `+run-watch`
