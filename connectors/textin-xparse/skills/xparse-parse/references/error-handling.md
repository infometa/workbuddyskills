# Structured Error Handling

Every failed CLI command writes exactly one final `xparse_error.v1` JSON object
to stderr. Task commands may write preceding `xparse_event.v1` JSONL progress
lines to the same stream; parse each line by `schema_version` and use the final
error object for the decision. Failed commands do not write a success object to
stdout. Read `error_code`, `retryable`, and `next_action`; do not branch on
translated message text or an old numeric API code.

```json
{
  "schema_version": "xparse_error.v1",
  "error_code": "FILE_TOO_LARGE",
  "message": "file exceeds the current service limit",
  "actual_value": {"size_bytes": 12582912},
  "limit": {"source": "service", "max_file_size_bytes": 10485760},
  "retryable": false,
  "next_action": "REDUCE_FILE",
  "request_id": "optional-request-id",
  "task_id": "optional-task-id",
  "run_id": "optional-run-id"
}
```

## Field contract

| Field | Agent rule |
|-------|------------|
| `error_code` | Stable decision key. Prefer it over `message` or `details.api_code`. |
| `message` | Direct user-facing explanation. Show it to the user, but never parse it for branching because it can be localized. |
| `actual_value` | Current file size, page count, required pages, attempts, or another observed value. It is `null` when unavailable. |
| `limit` | Current service/account capability. Only use a value with `source: service`; never replace it with a remembered constant. It is `null` when the service did not report a limit. |
| `retryable` | `true` means the same logical action can be retried safely once at the Agent layer. `false` means do not retry or try a command variant; follow only `next_action`. |
| `next_action` | Stable action enum such as `FIX_INPUT`, `REDUCE_FILE`, `REDUCE_PAGES`, `POLL_STATUS`, `WAIT_AND_RETRY`, `AUTHENTICATE`, `UPGRADE_OR_USE_PAID`, or `CONTACT_SUPPORT`. |
| `upgrade_url` | Optional purchase/upgrade URL. Showing it does not authorize a paid retry. |
| `request_id`, `task_id`, `run_id` | Preserve when reporting or escalating a failure. After Run acceptance, retry status access against this exact identity. |
| `details` | Additional diagnostics, including `operation_id`, an upstream numeric `api_code`, or batch `failures`. Preserve `operation_id` for an idempotent retry; do not use details to override base fields. |

## Stable codes and decisions

This table applies to the final `xparse_error.v1` object for a failed CLI
command. A successful `task debug` response is not that error envelope: each
failed RunItem currently retains the Parse service's raw `error_code`, including
`40423` for a password failure. Use that raw code only after an accepted Run has
failed and only to select the existing-Resource `task continue` recovery path.

| `error_code` | Decision |
|--------------|----------|
| `FILE_NOT_FOUND` | Stop and obtain the correct accessible path. |
| `EMPTY_FILE` | Stop and obtain a non-empty file. |
| `UNSUPPORTED_FILE_TYPE` | Stop or convert to a supported type. Never silently switch to a paid route. |
| `FILE_TOO_LARGE` | Read `actual_value` and the service-sourced `limit`; reduce/split the physical file or ask before an explicit paid retry. `--page-range` does not reduce upload bytes. |
| `PAGE_LIMIT_EXCEEDED` | Reduce the page selection using the reported limit. |
| `PAID_QUOTA_REQUIRED` | Stop. Explain current daily/package values and reset time, then wait for explicit paid approval. |
| `TASK_FREE_MODE_UNAVAILABLE` | Stop. The selected environment has no supported free-first Task billing capability. Do not fall back to serial parse or paid execution. |
| `TASK_RUN_ALREADY_ACTIVE` | Keep the returned `task_id` and `run_id`. With `retryable=false` and `next_action=POLL_STATUS`, inspect the existing Run using `task status <TASK_ID> --run-id <RUN_ID>`; do not create a replacement Task or Run. |
| `IDEMPOTENCY_CONFLICT` | Stop. The operation ID was reused with different inputs or semantics. Keep the original operation intact and use a new ID only for a genuinely new request. |
| `CAPABILITY_QUERY_FAILED` | Do not invent quota or limits. Retry only when `retryable=true`; otherwise report `request_id`. |
| `OUTPUT_FAILED` | Inspect `details.failure_stage` and `details.reason_code`, then fix the output path or permissions before retrying. |
| `SPLIT_FAILED` | Stop; do not parse an incomplete segment set. Preserve the original file. |
| `MERGE_FAILED` | Stop; do not present partial output as a complete document. Surface `failure_stage`, `reason_code`, segment index/field, and request/task identifiers when present. |
| `RETRY_EXHAUSTED` | The CLI already used its bounded retry budget. Do not immediately repeat the same command. Inspect `details.last_error`, follow `next_action`, and preserve `request_id`. |
| `RATE_LIMITED` / `NETWORK_ERROR` | Retry only when `retryable=true`; respect `WAIT_AND_RETRY`. |
| `SERVICE_ERROR` | Show the original `message`, then follow `retryable` and `next_action`. When `details.api_code=40422`, keep `SERVICE_ERROR`, preserve `request_id`, and follow `PROVIDE_FILE`; do not infer or rename a subtype from message text. |
| `AUTHENTICATION_FAILED` | Ask the user to restore the configured authentication method. Never request or print tokens. |
| `INVALID_ARGUMENT`, `INVALID_PAGE_RANGE`, `INVALID_PASSWORD` | Correct the input, then run once with the corrected arguments. |
| `BATCH_PARTIAL_FAILURE` | Inspect every `details.failures[]` item. Never hide failed inputs or claim the batch fully succeeded. |

## Durable Task states

Task commands return a persistent `task_id` and the latest Run state. Branch on
the state rather than repeating `task run`:

When structured progress is enabled, `run_accepted` is a success event that
exposes the durable identity before foreground polling finishes. An explicit `--wait`
timeout is also a successful submission projection (`wait_timed_out: true`,
`next_action: POLL_STATUS`), not `SERVICE_ERROR`; poll the same Run. A genuine
polling API failure remains `xparse_error.v1` and includes the accepted
`task_id` / `run_id` when known.

| State | Agent decision |
|-------|----------------|
| `scheduled`, `running` | Keep Task and Run IDs and use `task status <TASK_ID> --run-id <RUN_ID>` later. Do not recreate the Task or take over the Runtime's internal retries. |
| `completed` | Use `task read` for selected evidence or `task export` for the full set. If result access returns a non-retryable error, report it and stop; never return to `task run`. |
| `partial_failed`, `failed` | Run `task debug`; report successful and failed files separately. Do not recreate the whole Task. |
| `waiting_paid_authorization` | Stop and obtain explicit user approval. Authentication alone is not approval to spend. After approval, resume the exact Run with `task resume ... --approve-paid`. |
| `waiting_funds` | Stop and ask the user to add funds. After confirmation, resume the exact Run with `task resume ... --after-funding`. |
| `cancelled` | Report cancellation. Start a new Task only if the user asks. |

`waiting_paid_authorization` and `waiting_funds` are action-required state
projections, not `xparse_error.v1` failures. A successful CLI exit does not mean
the user request is complete. Follow only `next_action`, make no other xParse
call before the required human confirmation, and preserve the exact Task/Run
identity for resume.

An upload-time `PASSWORD_INPUT_REQUIRED` includes an `operation_id` and stable
input selectors. Ask for the named passwords, then replay the unchanged
originating command once with the same `--operation-id` and repeated `--password
<SELECTOR>=<PASSWORD>` bindings. Replay `task run` for an initial submission and
replay `task rerun --mode new-files` when adding files to an existing Task. The
latter error includes the existing `task_id`, but the failed uploads are not yet
Resources and cannot be recovered with `task continue`. The CLI transparently
reuses already-ready uploads; do not track File Asset IDs or replace the
operation.

After an accepted Run fails, only an existing Resource whose `task debug`
RunItem has raw Parse error code `40423` uses `task continue`. Ask for the
password and repeat `--password`; a single-Resource Task can use `--password
<PASSWORD>`, while multiple Resources require repeated
`--password <SELECTOR>=<PASSWORD>` bindings. Never put passwords in a Task
config file, telemetry, logs, or the response. See
[task-runtime.md](task-runtime.md) for the recovery sequence.

## Quota and paid boundary

Run `quota --output json` when explaining `PAID_QUOTA_REQUIRED`. Routing uses
the server's current `daily_pages_remaining` and, only when returned for an
authenticated request, `free_package.free_remain_count`. The historical
`free_count` field is display-only and must not be used as remaining quota.

Authentication is not approval to spend. Never turn `--api auto` or `--api
free` into `--api paid` after an error. Wait for the user's explicit approval,
even when `upgrade_url` is present.

When the user explicitly chooses to purchase credits, use the `upgrade_url`
returned by the current service. If it is absent, direct the user to the account's
regional support or portal; never invent or substitute another region's URL.

## Retry boundary

The CLI automatically retries recognized transient parse failures with a
bounded backoff. Therefore:

- when `retryable=true`, follow `next_action` and retry at most once at the Agent
  layer; for ambiguous Task submission, reuse the emitted `operation_id` with
  `--operation-id`;
- when `error_code=RETRY_EXHAUSTED`, do not immediately retry again;
- when `retryable=false`, stop the logical action and follow only
  `next_action`; for `CONTACT_SUPPORT`, report the failure and identifiers and
  execute no further xParse commands for the current request;
- changing timing, flags, authentication options, selector form, Resource ID,
  or switching between `task read` and `task export` does not reset the retry
  budget;
- after any Task/Run identifier has been observed, result-access failure must
  not fall back to `task run`, serial `parse`, cached output, or another Run;
- run each xParse command independently. A pipeline or compound shell command
  can hide the CLI exit status; the final `xparse_error.v1` still makes the
  operation a failure even when the wrapper reports exit code 0;
- never silently skip a failed parse or failed batch item.

## Reporting template

Tell the user what failed, the real observed value, the current service limit,
and the required next action. Include `request_id`/`task_id` when present. Do
not paste credentials, verbose HTTP headers, or a stale limit from this Skill.
