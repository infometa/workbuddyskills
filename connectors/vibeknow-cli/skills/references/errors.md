# vibeknow-create Error Reference

## Exit Codes

| Exit Code | Meaning | Agent Action |
|-----------|---------|--------------|
| 0 | Success | Extract `video_url` from stdout (JSON) or last NDJSON `task.succeeded` event |
| 1 | General error | Read stderr for details |
| 2 | Invalid arguments | Check `--from` is provided, file exists, URL is valid |
| 3 | Auth error | Credential missing, expired, or superseded by another login — every command exits this way, and re-running changes nothing. Only a person can fix it, so say so instead of retrying. Where a host manages the login for you (the WorkBuddy connector does), tell the user to reconnect there; where it is your own install, `vibeknow auth status --output json` names the cause and `vibeknow auth login` repairs it. |
| 4 | Task failed, **retryable** | Safe to re-submit. The `task.failed` event's `retryable` field is `true`. |
| 5 | Task failed, **not retryable** | Do not retry. Report `error_code` and `error_message` to user. |
| 6 | Stream interrupted, **task status unknown** | The task may still be running on the server. Read `error.detail.resend_safe` before doing anything (below). Unless it is `true`, reconnect with `vibeknow video wait` — do **not** re-submit, which would create a duplicate billed task. |
| 7 | Partial success: preview ready, MP4 render failed | Report the `share_url`; retry only the export. |
| 8 | Blocked on a user decision | Show the pending action, wait for the user, run its `resume_command`. |
| 130 | User interrupt (SIGINT) | Task may still be running server-side. |

## Exit 6: `error.detail`

Exit 6 means "not a terminal state". Three things reach it, and they need
different responses, so check `reason` first:

| `reason` | What happened | What to do |
|---|---|---|
| `wait_budget_expired` | `video wait --for` reached its budget. The run is fine and nothing was lost. | Run the `next_actions` command to keep waiting |
| *(absent)* | The stream ended with no terminal event, or the task was paused | Read `delivery` / `resend_safe` below, or `video resume` for a pause |

A spent budget carries the run's position rather than a verdict on resending,
because there is nothing to decide — the run is going:

```json
{ "ok": false,
  "error": {
    "type": "api", "code": 6,
    "message": "still generating (tts / tts_generate) after 1m30s — run again to keep waiting",
    "detail": {
      "status": "running",
      "reason": "wait_budget_expired",
      "task_id": 42, "session_id": "s_x",
      "stage": "tts / tts_generate",
      "waited_ms": 90000,
      "next_actions": [{ "command": "vk video wait 42 --session-id s_x --for 1m30s",
                         "purpose": "Keep waiting; the run is still going and no work is lost" }]
    } } }
```

`stage` is the last position seen on the wire, so it advances between calls.
`past <node>` means that node finished and nothing has been reported since;
on the hand-drawn line it is followed by `drawing (…)`, because that line's
middle emits nothing and that is where most of its time goes. Neither shape
is a fault, and neither says the run is healthy — silence is not evidence
either way. See `commands.md` for what each line reports.

The other two cases carry a machine-readable verdict on the one question that
matters there — whether re-running recovers a lost run or pays for a second
one.

```json
{ "ok": false,
  "error": {
    "type": "api", "code": 6,
    "message": "the generation stream ended before the task reached a terminal state…",
    "hint": "vk video wait 4242 --session-id s_x",
    "detail": {
      "delivery": "submitted",
      "resend_safe": false,
      "task_id": 4242,
      "session_id": "s_x",
      "backend_status": "running",
      "next_actions": [{ "command": "vk video wait 4242 --session-id s_x",
                         "purpose": "Reattach to the run the backend still has; do not start a new one" }]
    } } }
```

| `delivery` | `resend_safe` | Meaning |
|------------|---------------|---------|
| `submitted` | `false` | The backend has a work row for this session. It is likely still running. Reattach. |
| `not_submitted` | `true` | The backend returned not_found. The work row is created at init time, so its absence means nothing was dispatched and nothing was billed. Safe to start over. |
| `indeterminate` | `false` | The probe itself failed (network, auth, 5xx). Unknown is not permission — check with `vibeknow video list` first. |

`backend_status` is present only for `submitted`, and is one of `running`,
`succeeded`, `failed`, `deleted`, `unknown`.

## Exit 8: blocked on a decision

Written to **stdout**, because it is the command's result rather than an
error report:

```json
{ "status": "blocked",
  "pending_actions": [{
    "action_id": "act_9f3c1b…", "type": "export_confirmation", "blocking": true,
    "message": "About to render MP4 (~several minutes, consumes 1 export credit). Continue?",
    "payload": { "session_id": "s_x", "credits": 1, "operation": "render_mp4" },
    "options": [{ "id": "confirm", "effect": "resume", "label": "Proceed and spend the credits" },
                { "id": "cancel",  "effect": "none",   "label": "Do not proceed; run nothing" }],
    "resume_command": "vk video export 42 --session-id s_x --confirm act_9f3c1b…" }] }
```

Rules:

- Present `message` and `payload` to the user. Never default a choice.
- `effect: "resume"` → run `resume_command` **verbatim**.
- `effect: "none"` → run nothing.
- `action_id` is not derivable and is bound to this run and this price. A
  rejected token (exit 2) means the terms changed: re-run without
  `--confirm`, show the new terms, ask again.
- Do not reach for `--yes` to get past a block you just received.

### The two boundaries

| `type` | Raised by | What is being agreed to |
|--------|-----------|-------------------------|
| `export_confirmation` | `video export`, `create --export` | Rendering the MP4: `{session_id, credits, operation}` |
| `scene_edit_confirmation` | `video edit` | Rewriting one shot: `{session_id, scene_index, script_only, from, to}` |

A token verifies only against the boundary it was minted for, so one is
never usable for the other.

`scene_edit_confirmation` carries **both** halves of the change. `from` is
what the shot says now, `to` is what it would say — show the user the diff,
not just the replacement. It also has no `credits` number, and that is not
an omission: what an edit costs depends on how much text the model writes
and how long the resulting speech runs, and the backend does not quote it in
advance. The `message` names the *kinds* of work being billed instead.
Do not invent a figure for the user.

Because `from`, `to` and `script_only` are all part of what was agreed to,
a token is invalidated by editing the proposed text at all, by adding or
dropping `--script-only`, or by the shot changing underneath between the
block and the resume.

## stage.failed Behavior

- `fatal=false`: Progress information only. The pipeline may retry internally or skip the stage. CLI continues streaming. No non-zero exit code is set from this event alone.
- `fatal=true`: The task is about to fail. CLI preserves the error info and exits with code 4 or 5 when `task.failed` arrives.
- If SSE disconnects after `fatal=true` stage.failed but before `task.failed`: CLI exits with code 6.

## Error Object (--output json)

When a command fails before a task is created (auth error, bad args, network error), the output is:

```json
{
  "schema_version": "1",
  "error": {
    "code": "<error_code>",
    "message": "human-readable message",
    "details": {},
    "retryable": false,
    "trace_id": "string (if VIBEKNOW_TRACE=1)"
  }
}
```

This is distinct from task events — it means no task was created at all.

## Error Codes (relevant to create)

| Code | Meaning | Typical Scenario |
|------|---------|-----------------|
| `auth_required` | No credential | Token missing |
| `auth_expired` | Token expired | Re-authenticate |
| `invalid_args` | Bad arguments | Missing `--from`, invalid file path |
| `not_found` | Resource not found | Bad doc_id or task_id |
| `network_error` | Cannot reach endpoint | Check connectivity |
| `stream_interrupted` | SSE connection lost | Maps to exit code 6 |
| `task_failed` | Task terminated with error | Check `retryable` field |
| `rate_limited` | Too many requests | Wait and retry |
| `internal_error` | Server error | Report bug |
| `insufficient_credits` | Not enough credits | Top up, then retry. Exit 5. |
| `concurrent_work_limit` | Too many runs in flight | Wait for one to finish; retryable (exit 4) |
| `script_invalid` | 原稿锁定 preflight rejected the script | Fix the document (length ≤ 8000 chars, usable text); exit 2 |
| `replica_invalid` | PPT-mode preflight rejected the source | Needs a PPT-style PDF/PPT within page/content limits; exit 2 |
| `knowledge_unsupported` | Document parsed to empty content | Use a document with extractable text; exit 2 |
| `image_invalid` | Image-mode preflight rejected the page count | Lower `--pages`, pick fewer `--images`, or use a longer document; exit 2 |
| `work_edit_busy` | The work is being edited right now | Transient; retry after the edit ends (exit 4) |
| `project_quota_exceeded` | Account is at its project cap | Delete a project or upgrade the plan; retrying cannot help (exit 5) |
| `project_works_full` | This project holds its maximum works | Use another project or remove works from it (exit 5) |
| `tts_preview_quota_exceeded` | Rolling voice-preview budget for this work is spent | Stop previewing and proceed, or come back later (exit 5) |

Any command run without a usable credential exits **3** and says
``no credential found; run `vibeknow auth login` `` before it opens a
connection. It is never reported as `network_error` — a missing login is not
a transport problem, and retrying cannot fix it.

The three quota codes exit 5 for the same reason `insufficient_credits` does:
nothing about the request is wrong, so retrying it unchanged can only fail
again. Report what ran out and let the user decide.
