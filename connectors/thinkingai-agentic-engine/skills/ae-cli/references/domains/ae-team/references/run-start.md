# team +run-start (Start TeamRun)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / write**

## Use Cases
- Start a new TeamRun for a given team with a task input.
- Returns the newly created run object including its `id` and initial `status`.
- Used for one-shot task execution. For multi-turn interactive sessions, use `+run-chat` instead.

## Mandatory Rules (MUST)
- `--team-id` is required. Obtain the real team ID via `+list` — do not guess.
- `--input` is required (1–50000 chars). Pass the user's task description verbatim; do not truncate.
- JSON array flags (`--project-ids`, `--project-names`, `--space-ids`, etc.) must be valid JSON arrays, e.g. `'["id1","id2"]'`.
- `--notification` must be valid JSON if provided, e.g. `'{"channels":["feishu"],"feishuChatId":"..."}'`.
- This is an ordinary `write` operation and does not require CLI confirmation.
- After starting, capture the returned `id` (run ID) and use it to poll `+run-result`.

## Command
```bash
ae-cli team +run-start --team-id <team_id> --input "分析上周用户留存情况，生成报告"

ae-cli team +run-start \
  --team-id <team_id> \
  --input "分析本月DAU趋势" \
  --notification '{"channels":["feishu"],"feishuChatId":"oc_xxx"}' \
  --save-to-kb-id <kb_id>

ae-cli team +run-start --dry-run --team-id <team_id> --input "test"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--team-id` | Yes | Team ID |
| `--input` | Yes | Task input text (1–50000 chars) |
| `--conversation-id` | No | Associated conversation ID |
| `--notification` | No | Notification config JSON `{"channels":["feishu"\|"lark"\|"slack"],...}` |
| `--save-to-kb-id` | No | Knowledge base ID to save result to on completion |
| `--project-ids` | No | Associated project ID list JSON, e.g. `["id1"]` |
| `--project-names` | No | Associated project name list JSON |
| `--space-ids` | No | Associated space ID list JSON |
| `--space-names` | No | Associated space name list JSON |
| `--dw-space-codes` | No | Associated DW space code list JSON |
| `--dw-space-names` | No | Associated DW space name list JSON |

## Decision Rules
- Use `+run-start` for single-shot automation tasks where no interactive back-and-forth is needed.
- Use `+run-chat` instead when the user wants multi-turn conversation with the team.
- After receiving the run `id`, immediately start polling `+run-result` until status is `completed`, `failed`, or `cancelled`.
- If the run reaches `waiting_user`, use `+run-reply` to continue.

## Watching for Completion
```bash
# Preferred: stream via SSE (blocks until done, no polling needed)
ae-cli team +run-watch --id <run_id>
# exit 0 → completed/partial_success
# exit 1 → failed/cancelled/stale
# exit 2 → waiting_user: read pendingQuestion from stdout, reply, re-watch
ae-cli team +run-reply --id <run_id> --input "<user_answer>"
ae-cli team +run-watch --id <run_id>
```

## Next Steps on Failure
- `404` team not found: re-run `+list` to verify the team ID.
- `400` validation: check `--input` length and JSON flag formats.
- Run reaches `failed` status: inspect the `error` field in `+run-result` output.

## Recommended Chaining
- `+list` → `+run-start` → poll `+run-result` → `+run-artifacts`
- `+run-start` → status `waiting_user` → `+run-reply` → poll `+run-result`
