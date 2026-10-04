# team +run-chat (Chat with Team)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / write**

## Use Cases
- Send a message to a team in a multi-turn conversational session.
- If the current session has a run in `waiting_user` state, the platform automatically resumes it.
- Returns the session object (including `session.id`) and the new run object (including `run.id` and `status`).

## Mandatory Rules (MUST)
- `--team-id` is required. Obtain the real team ID via `+list` — do not guess.
- `--input` is required. Pass the user's message verbatim.
- To continue an existing session, pass `--session-id` with the `session.id` from the previous turn.
- This is an ordinary `write` operation and does not require CLI confirmation.
- After each turn, capture `session.id` and `run.id` for subsequent turns or replies.

## Command
```bash
# First turn (starts a new session)
ae-cli team +run-chat --team-id <team_id> --input "帮我分析最近的DAU趋势"

# Continue the same session
ae-cli team +run-chat --team-id <team_id> --session-id <session_id> --input "继续上次的分析"

ae-cli team +run-chat --dry-run --team-id <team_id> --input "test"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--team-id` | Yes | Team ID |
| `--input` | Yes | User message |
| `--session-id` | No | Existing session ID for multi-turn continuation |

## Decision Rules
- Use `+run-chat` when the task requires interactive back-and-forth (e.g. the team may ask clarifying questions).
- Use `+run-start` instead for fully automated, single-shot tasks.
- Always persist `session.id` from the response and pass it on subsequent turns with `--session-id`.
- If a run enters `waiting_user` state, use `+run-reply` (not another `+run-chat`) to respond.

## Waiting User Flow
```
+run-chat → run.status = waiting_user
→ +run-reply --id <run_id> --input "..."
→ poll +run-result until terminal
→ optionally continue with +run-chat --session-id <session_id>
```

## Next Steps on Failure
- `404` team not found: re-run `+list` to verify the team ID.
- Session state confusion: if unsure of current session state, call `+run-result --id <run_id>` to check status.

## Recommended Chaining
- `+list` → `+run-chat` → `+run-reply` (if waiting_user) → `+run-result` → `+run-artifacts`
- `+run-chat` (turn 1) → capture `session.id` → `+run-chat --session-id ...` (turn 2+)
