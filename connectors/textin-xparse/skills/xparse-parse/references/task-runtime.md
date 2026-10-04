# Durable Task Runtime

Use this workflow for two or more local documents, or whenever the user asks
for a persistent Task that can be inspected or resumed later. Its control-plane
routes and OAuth authentication are available in domestic and overseas
environments. URLs remain on the single-document `parse` path.

## Start one Task

Use explicit file arguments or a quoted glob. The CLI expands globs
deterministically, removes duplicates, uploads the files, creates one Task and
one Run, and returns JSON containing the `task_id`, `run_id`, and initial status
without waiting for document processing to finish.

```bash
xparse-cli task run a.pdf b.pdf --api auto
xparse-cli task run --files 'contracts/*.pdf' --api auto
```

With structured progress enabled, stderr contains line-delimited
`xparse_event.v1` progress events and stdout contains one final
`xparse_task_submission.v1` JSON object. The
`run_accepted` event exposes `task_id`, `run_id`, initial status, and next action
as soon as the server accepts the Run. During explicit waiting, `run_status` is
emitted only when status changes. Upload progress is intentionally coarse
(`completed_files` / `total_files`) and does not report byte-level percentages.

Rules:

- Preserve `operation_id`, `task_id`, and `run_id` as soon as they appear.
- Treat accepted Task identity as irreversible. An `operation_id` alone permits
  only the documented idempotent submission retry: an explicit
  `PASSWORD_INPUT_REQUIRED` correction or one ambiguous submission replay.
  After `task_id` or `run_id` is observed, do not issue `task run` again for
  that submission.
- Keep workflow and billing decisions separate. A waiting or rejected billing
  route never changes a multi-document Task into individual `parse` calls.
- Use `--api auto` unless the user explicitly requires the free endpoint or has
  approved paid execution.
- `auto` and `free` use the Agent free-first Task endpoint and fail closed. An
  overseas environment may explicitly return `TASK_FREE_MODE_UNAVAILABLE` when
  no equivalent free billing source exists. Never retry as `paid` without
  approval and never replace the batch with serial `parse` commands.
- One `operation_id` identifies one logical submission. The CLI namespaces it
  into upload, Task, and Run idempotency keys. For
  `PASSWORD_INPUT_REQUIRED`, ask for the listed passwords and retry the same
  command once with the returned selectors and `--operation-id
  <OPERATION_ID>`. The CLI reuses ready uploads and sends only missing files;
  the Agent must not track File Asset IDs. If a transient failure, timeout, or
  lost response makes the outcome ambiguous, replay the unchanged command once
  with the same ID. The same ID with changed files, mode, or config returns
  `IDEMPOTENCY_CONFLICT`; use a new ID only for a genuinely new operation.
- Check the exact returned Run with `task status <TASK_ID> --run-id <RUN_ID>`
  rather than starting the Task again. Do not infer the target from “latest”.
- In Agent workflows, keep the default submit-and-return behavior. Do not
  generate `--wait` or a short fixed `--timeout` automatically. A standalone
  user can explicitly add `--wait` to keep the command in the foreground.
- Use `task export --output <DIR>` after completion. `task run --output` only
  exports when combined with explicit `--wait` and the Run reaches a terminal
  state.
- Task inputs must be non-empty local files. Use `parse` for URLs.

Task-level parse defaults can be provided as a JSON file:

```bash
xparse-cli task run --files 'docs/*.pdf' --config ./parse-config.json --api auto
```

The CLI defaults `capabilities.pages` to `true` so newly parsed files include
page metadata and preview images. A custom config inherits this default when
the key is absent; explicit `"pages": false` is preserved. Existing Tasks retain
their stored config, and previously parsed files do not gain page images retroactively.

Do not put `document.password` in that file. Passwords are resource-specific.

## Create another Run under the same Task

Use `task rerun` when the Task identity must stay the same but a new Run is
needed. Choose exactly one mode from the requested change:

```bash
# Reprocess every Resource already bound to the Task.
xparse-cli task rerun <TASK_ID> --mode all

# Bind new local files to the existing Task, then process those new Resources.
xparse-cli task rerun <TASK_ID> --mode new-files --files 'new-docs/*.pdf'

# Reprocess only explicitly selected existing Resources.
xparse-cli task rerun <TASK_ID> --mode selected-files \
  --resource-id <RESOURCE_ID> --resource-id <RESOURCE_ID>
```

- `all` accepts neither local files nor `--resource-id`.
- `new-files` accepts positional files or repeated `--files`. It uploads missing
  files, binds them to the existing Task, and creates the new Run under that
  Task; it does not create a replacement Task.
- `selected-files` requires one or more repeated `--resource-id` values obtained
  from the Task view. It accepts no local files.
- For protected new files, repeat `--password`. With one input,
  `--password <PASSWORD>` is sufficient; with multiple inputs, use repeated
  `--password <SELECTOR>=<PASSWORD>` bindings.
- If their upload returns `PASSWORD_INPUT_REQUIRED`, ask for the listed
  passwords and replay this same `task rerun --mode new-files` command once with
  the same `operation_id` and returned selectors. The error includes the
  existing `task_id`, but an upload that has not succeeded is not yet a Task
  Resource and cannot be recovered with `task continue`.
- Preserve the new `operation_id` and `run_id`. Use `--operation-id` only to
  correct `PASSWORD_INPUT_REQUIRED` or replay the same ambiguous rerun operation
  with unchanged mode, files, and selectors.
- `task rerun --output <DIR>` is valid only with explicit `--wait`; otherwise
  export the completed Run separately with `task export --output <DIR>`.

## Inspect and consume results

```bash
xparse-cli task status <TASK_ID> --run-id <RUN_ID>
xparse-cli task read <TASK_ID> contract-a.pdf --run-id <RUN_ID>
xparse-cli task read <TASK_ID> <RESOURCE_ID> --run-id <RUN_ID>
xparse-cli task export <TASK_ID> --run-id <RUN_ID> --output ./task-output
xparse-cli task debug <TASK_ID> --run-id <RUN_ID>
```

- Prefer `read` when the user's question needs one or a few named documents;
  do not load every result into context. The CLI requests only the selected
  Resource body.
- Use `export` when the user requests all outputs or local files for downstream
  processing. It pages result metadata and fetches completed bodies one at a
  time. Read `task-manifest.json` to distinguish completed and failed resources,
  including colliding basenames.
- Use `debug` only for compact per-file errors and recovery evidence.
- Pass the preserved `--run-id` to `status`, `read`, `export`, and `debug` when
  continuing an Agent workflow. Omitting it selects the latest Run and is only
  appropriate for an interactive user who explicitly wants the latest state.

If `read` or `export` emits `xparse_error.v1`, apply the main Skill's structured
error gate before any other command. A non-retryable result-access failure does
not authorize another selector, omitting `--run-id`, switching between read and
export, running debug on a completed Run, creating another Task, serial parsing,
or substituting cached content. Report the exact Task/Run/Resource/request IDs
and stop. Only a user-confirmed external remediation or explicit new request
can reopen the action, and it must reuse the preserved Task and Run IDs.

For Agent polling, issue one-shot status checks with bounded backoff: 2, 5, 10,
20, then 30 seconds. Stop after roughly two minutes in one turn if the Run is
still `scheduled` or `running`; report the IDs and current status so a later
turn can continue. Do not hold `task run` open or duplicate the submission.

## State decisions

| Run state | Next action |
|-----------|-------------|
| `scheduled`, `running` | Keep both IDs and check later with `task status <TASK_ID> --run-id <RUN_ID>`; do not create another Task. |
| `completed` | Read selected results or export all results. A non-retryable result-access error is terminal for the current request; do not regress to submission. |
| `partial_failed`, `failed` | Run `task debug`, preserve successful results, and handle each failed resource. |
| `waiting_paid_authorization` | Stop and ask the user to approve paid execution. Do not infer approval from login state. |
| `waiting_funds` | Stop and ask the user to add sufficient funds before retrying settlement. |
| `cancelled` | Report cancellation; do not recreate work without a new request. |

Waiting states are successful Task state projections with an actionable
`next_action`; they are not completed user work. After observing either waiting
state, run no additional xParse diagnostics or alternate workflow. Wait for the
human action, then resume the exact identifiers below.

`--wait` is client-side polling of the already accepted Run, not a synchronous
Task API. If it reaches `--timeout`, the CLI exits successfully with the current
status, the original Task/Run IDs, `wait_timed_out: true`, and
`next_action: POLL_STATUS`. The server-side Run continues; the CLI neither
cancels nor recreates it. Use `task status` for those exact IDs. Do not start an
identical Task merely because the local process stopped waiting.

If Run creation returns `TASK_RUN_ALREADY_ACTIVE`, preserve the returned
`task_id` and active `run_id`. With `retryable=false` and
`next_action=POLL_STATUS`, inspect that Run using `task status <TASK_ID>
--run-id <RUN_ID>`. Do not retry Run creation or create a replacement Task.

After the required human action, resume the exact waiting Run:

```bash
xparse-cli task resume <TASK_ID> --run-id <RUN_ID> --approve-paid
xparse-cli task resume <TASK_ID> --run-id <RUN_ID> --after-funding
```

Use `--approve-paid` only after explicit paid authorization. Use
`--after-funding` only after the user confirms funds were added. The commands
are mutually exclusive and resume submission returns without waiting by
default; poll the same Run ID afterward. Never recreate the Task as paid, split
the files into another Task, or process them with serial/parallel `parse` calls.

## Continue password-protected files

After an accepted Run reaches `partial_failed` or `failed`, use `task debug`.
Only an existing Resource whose RunItem has raw Parse error code `40423` belongs
on this recovery path. This RunItem field is distinct from the stable
`xparse_error.v1.error_code` emitted when a CLI command itself fails. Obtain the
passwords from the user. Selectors can be a Resource ID, File ID, relative path,
file name, or basename. Use the bare password only when exactly one Task Resource
exists; otherwise bind every password to an unambiguous selector.

```bash
# One Task Resource.
xparse-cli task continue <TASK_ID> --password <PASSWORD>

# Multiple Task Resources; repeat the flag once per protected Resource.
xparse-cli task continue <TASK_ID> \
  --password <SELECTOR>=<PASSWORD> \
  --password <SELECTOR>=<PASSWORD>
```

`continue` updates access only for matched resources and reruns those resources.
It submits the selected rerun and returns by default. Preserve the new Run ID,
poll it separately, then call `task export --run-id <RUN_ID> --output
./task-output` after completion. `continue --output` is valid only together
with explicit `--wait`. It does not reparse already successful files. Never
put passwords in `--config`, telemetry, logs, command examples with real values,
or the final answer.

Do not use `continue` for `PASSWORD_INPUT_REQUIRED` emitted while `task run` or
`task rerun --mode new-files` is still uploading. Replay that originating
command with the same `operation_id` instead.

## Task context

The private `xparse_task_context.v1` file described in the main Skill applies to
Task Runtime too. Add `--task-context <FILE>` only to the first xParse invocation
for the user request, including when that first invocation is `task run`, and
delete the file immediately after the command consumes it.
