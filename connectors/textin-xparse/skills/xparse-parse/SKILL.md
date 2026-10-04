---
name: xparse-parse
description: "Parse, read, search, navigate, summarize, extract, or check images and documents for manipulation through xparse-cli. Use for document conversion and navigation, durable Task workflows, structured extraction, and domestic TextIn manipulation/AIGC detection of a local file or URL. Prefer it over raw PDF readers or custom OCR scripts."
---

# xparse-parse

Use the installed `xparse-cli` as the only parsing, authentication, quota, and
document-navigation execution kernel. Do not reproduce its HTTP, OAuth, quota,
PDF splitting, or result-merging logic in the Skill.

<!-- xparse-workbuddy-overlay:v1 -->
## WorkBuddy Connector contract

When this Skill runs inside the TextIn xParse WorkBuddy Connector, the rules in
this section override standalone installation and authentication examples in
the shared Skill and its references:

- Invoke every `xparse-cli` command as
  `xparse-cli --profile workbuddy <command> ...`. This includes the first
  invocation carrying `--task-context`. Examples elsewhere omit this prefix
  only for readability.
- Use the Connector-managed CLI version already supplied by WorkBuddy. Do not
  install, replace, pin, or upgrade `xparse-cli` from within a document task. If
  WorkBuddy reports a missing or incompatible CLI, return control to the
  Connector lifecycle instead of modifying the runtime.
- Rely on the Connector's Device OAuth and isolated `workbuddy` profile. If the
  Connector is disconnected, ask the user to reconnect it. Never request,
  store, repeat, or print an AppKey, Secret Code, Access Token, Refresh Token,
  private `device_code`, or user code, and do not start a separate auth flow.
- Treat stderr `xparse_event.v1` JSONL as WorkBuddy progress and stdout as the
  single final result. Preserve accepted Task and Run identifiers; do not hide
  progress by piping or wrapping the command.
- Submit extraction `task run --task-type extract` and `task add` without
  `--wait` by default. Even when the user wants to follow progress or wait for
  the result, use separate bounded `task status` checks so the submission can
  return its page URL immediately. Use the CLI's blocking `--wait` only when the
  user explicitly requests that CLI behavior.
- As soon as an extraction submission succeeds with an accepted `task_id`, ask
  WorkBuddy to open its exact server-issued `result_page_url` in the right-side
  browser before the first status poll. Keep that page visible while polling
  the same Task; do not silently poll instead of opening the page. Managed
  local-file imports may return import progress without a page URL. Preserve
  the accepted Task and upload/operation identifiers, then request a fresh URL
  with `task page <TASK_ID>` if the managed CLI and backend support it. Open a
  returned URL before continuing status checks; if no URL can be obtained,
  continue the shared import/status contract without inventing one.
- Use WorkBuddy's existing link-opening action, not a shell command or an MCP
  tool. Preserve the URL fragment exactly and do not print, persist,
  reconstruct, or separately expose its grant. If WorkBuddy cannot open the
  page, return the exact URL as a clickable link, explain that automatic opening
  failed, and continue bounded status checks on the accepted Task.

### Same-conversation extraction continuation

Keep the accepted extraction `task_id` from this conversation's successful
creation or append response distinct from any Parse Task ID. When the user adds
files for the same extraction goal, follow the shared Skill's default-append
rule even without an explicit "append" word: verify that extraction Task and
use `task add`, never `task run --task-type extract`. If the goal or target is
ambiguous, ask before submitting. Do not infer a target from unrelated
conversations or task-list recency. For local files, use direct managed import
only if the Connector-managed CLI supports it; otherwise obtain parsed File
Asset IDs through the shared fallback and add them to the same extraction Task.

For extraction progress and delivery, use the CLI `task status`, `task result`,
and `task export --format json|csv --output <DIRECTORY>` contracts in the shared
Skill. Opening the result page does not replace progress checks or result export.
Run status checks with the same Connector-managed CLI and `--profile workbuddy`;
follow the shared Skill's bounded polling and completion rules. Only when the
user explicitly requests the CLI's blocking wait, use the shared extraction
`--wait` contract instead of the page-first default.
If the managed CLI rejects those flags, report the incompatible Connector version
and return control to its lifecycle; do not resubmit an accepted Task or upgrade
its CLI from within the document task.

### Manipulation detection

For a domestic manipulation or AIGC check, invoke the shared
`detect-manipulation` command with `--profile workbuddy` and the
Connector-managed OAuth identity. Follow the shared free-package precheck and
one-call `--approve-paid` consent rule; an existing Connector login is not
payment approval. The CLI writes the JSON result and optional heatmap JPEG to
local absolute paths. Show the saved image to the user when WorkBuddy can open
that local path, without copying the inline Base64 or sending it elsewhere.
If the managed CLI does not expose the command, return to the Connector
lifecycle rather than installing another CLI inside the task.

### Optional expert caller attribution

An active WorkBuddy expert may explicitly declare a stable expert ID and its
package version. Only when both values are supplied by that expert, copy them
exactly into the task-context object defined below:

```json
"caller": {
  "type": "workbuddy_expert",
  "id": "<declared-expert-id>",
  "version": "<declared-package-version>"
}
```

Omit `caller` for ordinary Connector use or when either value is absent. Never
infer, search for, reuse from another task, or invent an expert identity. Do not
put `prompt_request_id` in the task-context file: WorkBuddy owns and transmits
that host request identifier independently.

### Workspace command parity

The shared Skill defines task-wide re-extraction, field/result editing and Copilot
commands. Keep `--profile workbuddy` on each invocation. Use `task page <TASK_ID>`
to refresh an expired result link when supported by the installed CLI/backend;
open its exact `result_page_url` with WorkBuddy's link-opening action. A task-wide
`task retry` requires a user request to re-extract; it is not an automatic response
to polling, network errors or a suspended task.

## Task context

For every new user request, create one private `0600` JSON file before the
first xParse command:

```json
{
  "schema_version": "xparse_task_context.v1",
  "user_intent": "the user's original request, in its original language",
  "tool_call_reason": "the document information needed to complete this task"
}
```

- Preserve the user's wording and keep the operational reason brief.
- Never include hidden reasoning, credentials, document content, or the final answer.
- Pass `--task-context <FILE>` only on the first xParse invocation for that request.
- Delete the temporary file after that invocation. Later commands inherit the task.
- Do not pass inline JSON through shell arguments, `echo`, or a heredoc.

## Command integrity and structured error gate

Run every operational `xparse-cli` invocation as a standalone shell command.
Do not pipe it through `head`, `tail`, `grep`, or another command, and do not
append cleanup, printing, file reads, or other shell commands that can replace
its exit status. Perform task-context cleanup in a separate shell call.

For every failed command, parse the final stderr object whose `schema_version`
is `xparse_error.v1`. Treat that object as failure even if a shell wrapper
reports exit code 0. Apply this gate before issuing another xParse command:

- `retryable=false` means do not retry or reinterpret the same logical action.
  Follow only the declared `next_action`. For `CONTACT_SUPPORT`, report the
  error and preserved identifiers, then issue no more xParse commands for the
  current request.
- `retryable=true` permits at most one Agent-layer retry of the same logical
  action. Keep the same Task, Run, Resource, and `operation_id` where present.
- Changing flags, authentication options, selector form, Resource identifier,
  timing, or switching between `task read` and `task export` does not create a
  new logical action or reset its retry budget.
- Do not run diagnostic xParse commands unless the Task state or `next_action`
  explicitly calls for them. Goal completion pressure is not a recovery signal;
  a correct failure report completes the Agent action.

After a non-retryable failure, another attempt is allowed only after the user
confirms an external remediation or explicitly requests a new action. Reuse the
preserved Task and Run identifiers; never recreate completed server work.

## Free, free-package, and paid routing

Use `--api auto` by default. The CLI queries the service quota before parsing and
uses the current server response as the authority instead of relying on a Skill
snapshot.

| Mode | CLI behavior | Use it when |
|------|--------------|-------------|
| `--api auto` | Uses the daily free API allowance first. When quota reports an AppKey-authenticated free package with sufficient `free_remain_count`, it can use that package through the existing authenticated route. | Default for supported PDF and image work. |
| `--api free` | Forces the free endpoint and does not use the authenticated free-package route. | The user explicitly requires the free endpoint only. |
| `--api paid` | Forces the paid endpoint and follows the service's existing package/balance billing behavior. | The user explicitly approves paid use, or approves it after learning that the format requires the paid API. |

Authentication is identity, not permission to spend. Never choose `--api paid`
only because OAuth or AppKey credentials exist.

Run `xparse-cli quota --output json` when the user asks about quota, when a routing failure
needs explanation, or before proposing a paid retry. Read all returned facts:

- daily free parse pages remaining and reset time;
- independent `extraction_quota` daily limit, used pages, remaining pages, and
  reset time when present;
- whether the request is authenticated;
- authenticated free-package total, historical used count, and current
  `free_remain_count` when present (routing uses only `free_remain_count`);
- maximum pages and file size per request.

Do not cache or calculate an allowance in the Skill. `parse --api auto` performs
its own quota preflight, and the parse response remains authoritative if quota
changes between inspection and execution. The Skill must not promise stronger
billing guarantees than the existing server provides.

Device OAuth and AppKey are different identities. If quota returns
`authenticated=false` or omits `free_package`, do not infer package access from
an OAuth login indicator. Treat only fields in the current quota response as
available.

An authenticated default quota response may still omit `extraction_quota`.
Report that the server did not return the extraction allowance; do not claim
that enterprise OAuth intrinsically cannot query it or substitute the parse
allowance. Missing quota data alone does not prove that extraction is
unavailable; use the actual extraction Task response for that conclusion. If
`authenticated=false`, restore the intended login first.

Keep the three paths separate:

- Unqualified `quota` reports parse allowance and, only when returned,
  `extraction_quota` for structured extraction (`open_kie_vlm_engine`).
- `quota --service manipulation_detection` reports only the manipulation
  detector's free package. It is not an extraction allowance or an extraction
  capability check.
- `task run --task-type extract` creates a structured-extraction Task. Judge
  its availability and outcome from that Task's actual response, never from a
  manipulation quota response. Do not substitute `detect-manipulation` when
  extraction quota is missing or extraction fails.

The free endpoint supports PDF and images. Office, HTML, OFD, and other formats
may require `--api paid`; explain this and obtain the user's approval before
switching modes. If all reported free sources are insufficient, stop and explain
the current quota rather than silently retrying as paid.

### Manipulation detection (domestic service only)

When the user asks whether a supported image or PDF has been manipulated or AI
generated, use `xparse-cli detect-manipulation <FILE|URL>`. This is a separate
service from parsing. To inspect its current package, run
`xparse-cli quota --service manipulation_detection --output json` and read
`free_package.free_remain_count` only when `authenticated=true` and the
returned service is `manipulation_detection`. A missing `free_package` is
unknown, not zero; never infer this package from the unqualified
`xparse-cli quota` command's `pdf_to_markdown` allowance. If the installed CLI
does not recognize `--service`, update it instead of using the default quota
as a substitute. The CLI prechecks the current
`manipulation_detection` free package through the quota endpoint. If free quota
is available, it makes one detection call without a paid flag. If free quota is
exhausted or cannot be confirmed, it stops before detection; ask the user to
approve one potentially paid call before repeating the command with
`--approve-paid`. This is a precheck, not a billing reservation or guarantee.
Do not carry paid approval into later calls.

If the CLI reports `quota service mismatch`, the selected endpoint did not
return manipulation-detection quota. Stop that detection attempt and report the
response incompatibility; do not interpret it as extraction-service activation,
extraction quota, or a reason to try a different operation.

`--tamper-threshold` and `--aigc-threshold` are optional API inputs in `[0,1]`;
pass them only when requested or needed for an agreed detection criterion. The
CLI leaves service defaults unchanged when they are omitted. Results go under
`./xparse-results/` by default, or `--output <DIR>`, in a unique run folder.
It saves `result.json` and, when returned, a JPEG heatmap; terminal output
contains absolute paths rather than inline Base64. Report the service's risk
conclusion and risk types as detection signals, not proof of provenance. Do not
send this domestic-only request to a global endpoint or silently substitute
another detector. Check `detect-manipulation --help` when the installed CLI may
predate this command.

## Choose the workflow

Choose by input shape and durability, not by whether authentication already
exists:

Workflow selection and billing selection are independent decisions. `Task`
versus `parse` is chosen from the request's input shape and durability needs;
`auto`, `free`, and `paid` choose only the billing route. A quota, eligibility,
authorization, funding, or format outcome must never change an accepted
multi-document Task into individual `parse` calls. Only an explicit user request
that narrows the original scope to a genuinely new one-document action may be
treated as a new `parse` operation.

- Use `parse` for one document or URL when the user needs an immediate result,
  conversion, or local outline/search navigation.
- Structured extraction is the exception: first decide whether new files belong
  to the current conversation's extraction Task or a genuinely new extraction
  request. A follow-up for the same goal can be an append without the word
  "append". Choose the supported source path below; a new Parse Task is not a
  prerequisite for every append. Follow the semantic extraction section below
  instead of reading parsed content into the Host.
- Use the durable Task Runtime for two or more local documents, or when the user
  explicitly needs a persistent Task ID, later status checks, selective result
  reads, exports, debugging, or continuation. A one-file request can therefore
  still be a Task when durability is explicit.
- Task Runtime control-plane routes and OAuth authentication are available in
  both domestic and overseas environments. Free-first Task billing is a
  separate capability: if the selected environment returns
  `TASK_FREE_MODE_UNAVAILABLE`, stop and explain it. Never replace the Task with
  serial `parse` calls or silently switch to paid execution.

### Durable multi-document Task Runtime

For local files, start one server-persisted Task instead of launching multiple
`parse` commands:

```bash
xparse-cli task run --files '<GLOB>' --api auto
```

`--api auto` is free-first and fails closed: it does not silently create a paid
Task. Use `--api paid` only after the user explicitly approves paid service
behavior. Do not parallelize individual `parse` commands for inputs that belong
to one Task.

`task run` returns after the server accepts the Run. When structured progress
is enabled, stderr is an `xparse_event.v1` JSONL stream: `run_accepted` exposes
the accepted Task/Run identity immediately, and `run_status` is emitted only
when the state changes.
Stdout contains exactly one final submission JSON. Preserve `operation_id`,
`task_id`, and `run_id`. If submission fails or
the process loses its response, reuse the observed `operation_id` with
`--operation-id`; never invent a new ID for the same logical submission.

Keep Agent workflows on the default submit-and-return path. Do not add
`--wait` or a short fixed `--timeout` automatically. When a user explicitly
requests foreground waiting or wait-and-export, `--wait` polls the same Run;
its local timeout returns the current accepted identity with
`wait_timed_out: true` and `next_action: POLL_STATUS`. It does not cancel or
recreate the Run. Continue with `task status` for that exact Task and Run.

`waiting_paid_authorization` and `waiting_funds` are accepted Task states, not
CLI transport failures. The submission/status JSON and its `next_action` are the
single authority. They mean the user request is incomplete: stop immediately
and issue no more xParse commands—not quota, status, read, export, debug,
another `task run`, or `parse`—until the user confirms the required external
action. Then call `task resume` once for the exact Task and Run.

Use `task status <TASK_ID> --run-id <RUN_ID>` for bounded progress checks. Start
at 2 seconds, then back off to 5, 10, 20, and 30 seconds; do not spend more than
about two minutes polling in one Agent turn. Return control with the IDs and
current state when work is still running. Never start a duplicate Task merely
because the Run is still `scheduled` or `running`.
Prefer `task read` when only one result is needed; use `task export` when the
user needs the complete result set. On partial failure, run `task debug` before
choosing a recovery action. Use `task continue` only when that accepted Run's
debug result identifies the existing Resource's raw Parse error code `40423`.
Supply per-file passwords by repeating `--password`; when more than one Resource
is involved, bind each value as `<SELECTOR>=<PASSWORD>`. This reruns only the
selected failed Resources without reprocessing successful files.

Task identity and state move forward only:

```text
no identifiers -> task run once
operation_id + PASSWORD_INPUT_REQUIRED -> ask for the named passwords, then replay the originating task run or task rerun --mode new-files once with that ID and the returned selectors
operation_id only after an ambiguous submission -> retry task run once with that ID
task_id + run_id -> task status for that exact Run
waiting_paid_authorization -> stop; after user approval, resume that exact Run
waiting_funds -> stop; after confirmed funding, resume that exact Run
completed -> task read or task export for that exact Run
non-retryable result-access failure -> report and stop
```

`PASSWORD_INPUT_REQUIRED` permits only one documented correction replay of the
originating command with the same `operation_id`. For initial submission that
command is `task run`; for new files under an existing Task it is `task rerun
--mode new-files`, and the error may legitimately include that existing
`task_id`. The CLI transparently reuses ready uploads; the Agent must not track
File Asset IDs or decide which files to upload. An `operation_id` without a
Task/Run ID after another ambiguous submission permits one unchanged replay.
Once a new `task_id` or `run_id` has been accepted for a logical submission,
never return to `task run` for it. A `task read` or `task export`
failure must not fall back to a new Task, serial `parse`, cached results, an
alternate selector, or a different Run. Use `task debug` only for
`partial_failed`/`failed`, not to investigate a completed Run whose result
access returned a non-retryable error.

Read [task-runtime.md](references/task-runtime.md) before starting, inspecting,
or recovering a durable Task.

### Semantic extraction Task from File Assets

First decide whether new files continue an existing extraction goal or start a
new one. For an append, use an extraction Task ID explicitly supplied by the
user or, when none is supplied, the one accepted extraction Task in the current
conversation that is unambiguously tied to that goal. Treat a follow-up
supplying more files as an append even when the user says only "再处理这份" or
"还有这些文件" and never says "追加". Preserve the extraction `task_id` returned
by its creation or previous append. The same conversation alone is not enough:
an explicit new or independent extraction request starts a new Task. If the goal
or target is unclear, or multiple extraction Tasks could match, ask before
submitting work. Do not pick the most recent Task or confuse a Parse Task ID
with an extraction Task ID. Never turn an append failure or resource-version
conflict into a replacement Task.
Verify the target and its type with `task status <EXTRACTION_TASK_ID>`.

Only for a new extraction request, create one persistent extraction
Task on the service. Do not read Parse results into the Host and do not generate
the final field values locally. Preserve the user's extraction request verbatim
as `instruction`; do not replace it with a fixed schema or add field definitions.

If trustworthy parsed File Asset IDs from xParse are already available, skip
parsing. Append them to the existing Task with `task add --file-id`; for a new
extraction request, create the Task directly. A newly uploaded, ready File Asset
ID may also be used when creating a new extraction Task: the backend starts
paid managed parsing only for files without a reusable parse result. Do not
silently incur that parse cost; obtain approval when the user has not already
authorized paid parsing. `task add --file-id` still requires parsed assets.
Repeat `--file-id` in source order:

```bash
xparse-cli task run --task-type extract \
  --instruction '<USER_REQUEST>' \
  --file-id <FILE_ASSET_ID>
```

When the user needs an independent upload or wants to keep its ID for later,
use `xparse-cli upload <FILE> --operation-id <OPERATION_ID>`. Its JSON returns
the original `file_id` and does not parse the file. Preserve `operation_id` on
an interrupted upload; the CLI checks the local SHA-256 before reusing a ready
asset. Use the returned ID as `--file-id` for a **new** extraction Task. If
an existing parse result is reusable, the backend does not charge for a new
parse. If not, the Task first enters paid managed parsing. The initial
`document_count` counts only attached extraction Resources and may be zero;
`submitted_file_count` reports how many IDs the CLI submitted. Check
`task status` for import failures and never infer `complete=true` from the
creation response or from one completed file.

For an append, an installed CLI that supports extraction `task add --history-id`
can use existing history IDs directly; an installed CLI that supports managed
local-file imports can use `task add <EXTRACTION_TASK_ID> <FILE>` directly. Check
the installed `task add --help` for `--history-id` or managed-import flags such
as `--uploaded-file-id` and `--reconcile` instead of assuming a particular
Connector version supports them. Neither path needs a new Parse Task. If local
import is unavailable, obtain parsed File Asset IDs through the Parse Task path
below and still append to the original extraction Task. If only a history ID is
available but the installed CLI cannot use it, ask for a supported source or a
Connector update; do not pretend a Parse Task can consume that ID. Never create
a replacement extraction Task.

For local files without parsed File Asset IDs, including a single file, the
free-first path remains a durable Parse Task when creating a new extraction
Task or when the installed CLI cannot import those files directly for an append.
The separate `upload` path above is for an explicitly desired original asset
ID and requires paid-parse approval before creating extraction from a raw ID.
Preserve the
Parse Task's accepted `task_id` and first `run_id` separately from
`<EXTRACTION_TASK_ID>` when appending:

```bash
xparse-cli task run <FILE> --api auto
```

Use one `task run` for all local source files. Poll only that exact first Run
with `task status <TASK_ID> --run-id <FIRST_RUN_ID>` using the bounded backoff
defined above. Do not use an old Task, a rerun, or a continuation Run as an
implicit extraction source. If the first Run remains `scheduled` or `running`
after the polling budget, return its identifiers and current state instead of
creating the extraction Task.

When the exact first Run reports `completed`, fetch the stable Task resources:

```bash
xparse-cli task status <TASK_ID> --details
```

Create or append using File Asset IDs from this Parse Task only when all of
these invariants hold in the details response:

- `run.run_id` equals `<FIRST_RUN_ID>` and `run.status` is `completed`;
- `run.failed_count` is `0`;
- `run.completed_count` equals `run.total_count`;
- `run.total_count` equals the number of `resources`;
- every resource has a non-empty `file_id`.

Pass every `resources[].file_id`, in resource order, as a repeated `--file-id`.
Do not call `task export`, `task read`, or another content-returning command to
recover File Asset IDs. `partial_failed` and `failed` must stop before extraction.
Waiting states retain the same Task and first Run and require the documented user
action before polling resumes.

- Keep `--operation-id` unchanged only when replaying the same ambiguous
  extraction create attempt; do not reuse it for a new extraction request.
- The command returns `task_id`, `status`, and `result_page_url`. Use `task status <TASK_ID>` to inspect progress; do not guess an extraction Run ID.
- The result URL contains a short-lived grant in its fragment. Preserve the URL
  exactly as returned. Do not reconstruct it, persist it, print the grant, or
  send it to another API. Ask a capable Host to open the URL directly; if the
  Host cannot, return it as a clickable link.
- Creating the extraction Task submits asynchronous work. Open or return the result
  page when useful, and use `task status <TASK_ID>` for progress. Apply the bounded
  polling backoff above; stop polling when user action is needed or the budget expires.
- `task status <TASK_ID>` returns the server summary: `status`, `stage`,
  `total_count`, `completed_count`, `failed_count`, `pending_count`, `terminal`,
  `needs_user_action`, `complete`, and `issues`. Do not infer success from a
  terminal state: only `complete=true` means the full result is ready. Report
  missing or failed documents when the task stops with incomplete results.
  When `needs_user_action=true`, stop polling and direct the user to the existing
  result page; use `task status <TASK_ID> --details` only when the documented
  recovery path requires it. Opening a page does not replace querying status.
- If extraction returns `FILE_NOT_FOUND` with `CHECK_FILE_ACCESS`, verify the
  supplied File Asset ID and signed-in account; do not retry the same request
  automatically. If it returns `EXTRACTION_SOURCE_NOT_PARSED` with `PARSE_FILE`,
  complete parsing for that file in the current account before extraction.
- Summary counts are document counts. A failed document has one document-level
  issue with `error_code` and `error_message` when available; report that cause,
  not a second missing-field error. For `insufficient_balance`, explain that
  funds or package quota must be restored before retrying on the existing Task.
  A completed field that was not found is a normal `null` result, not an issue.
  Result pagination applies to `items`; `summary` still covers the whole Task.
- Keep the default asynchronous submission and bounded status polling. When the
  user explicitly requests foreground waiting, extraction creation and `task add`
  accept `--wait`, with optional positive `--timeout` and `--poll-interval` durations.
  These durations require `--wait`. Waiting reads the Task's current summary,
  including concurrent additions or edits; it does not pin a Run or a submission
  snapshot. It stops when `terminal=true` or `needs_user_action=true`.
- A waited response preserves the original submission identifiers, counts,
  `resource_version`, and `result_page_url`, and includes the latest `summary`
  when one was obtained. The top-level `status` reflects that summary. Follow
  `next_action`: `POLL_STATUS` queries the same Task, `READ_RESULTS` reads or
  exports results, `INSPECT_TASK` reports issues and inspects the existing Task,
  and `OPEN_RESULT_PAGE` requests user action on the existing page.
- `wait_timed_out=true` ends only local waiting, including an in-flight status
  request; continue with `task status <TASK_ID>`. Never resubmit creation or append
  because of a wait timeout. A polling error or cancellation returns the accepted
  submission with `wait_interrupted=true` and a structured error carrying the
  same `task_id` and `details.submission_accepted=true`. Follow the structured
  error gate before any further command; its `next_action` takes precedence.
  The latest summary may be absent if the first query failed. Preserve the accepted
  Task and never treat a wait error as a failed submission.
- To read pure results use `task result <TASK_ID> --limit 50`. Follow `next_offset`
  with `--offset <NEXT_OFFSET> --snapshot <SNAPSHOT>`; on snapshot conflict restart
  from the first page rather than combining different task versions.
- To export use `task export <TASK_ID> --format json --output <DIRECTORY>` (or csv).
  Extraction writes `results.json` or `results.csv`; stdout contains the completion
  summary and output path. Only ready documents are exported; always report omissions
  and review warnings from the summary. Never claim partial results are complete.
- JSON contains `file_name` and business `result` values without evidence or agent
  internals. Missing values are null, identifiers remain strings, and object/array
  values remain structured. CSV serializes object/array cells as JSON text.
- Do not pass parse-only flags (`--api`, `--config`, `--password`, or
  automatic `--output`) to extraction creation. `task run` defaults to parse for
  compatibility; extraction requires explicit `--task-type extract`.
- `task add <TASK_ID>` uses the server's task type: pass local paths for parse,
  parsed `--file-id`, history `--history-id`, or local paths for extract. Local
  extraction additions use the existing managed import flow, not a new extraction
  Task. Preserve returned `uploaded_file_ids` and `operation_id`; after an
  interrupted upload use the same operation identity, or import known assets with
  `--uploaded-file-id`. `task add TASK --reconcile` refreshes pending imports.
  Parse add requests a new-files Run and
  retains `--operation-id` recovery; a failure after binding does not mean files
  were not added. Preserve identifiers and follow the returned recovery instructions.
  Existing `task rerun --mode new-files` remains supported.

#### Extraction workspace operations (requires a CLI build with these commands)

Regional availability follows the page: list, spec set/clarify, whole-task or scoped
rerun, preview, and version history are domestic-only. The server rejects these
workspace operations in the global region; do not bypass this restriction.

- Explicitly rerun the entire current extraction Task with `task retry <TASK_ID>`.
  This is a new extraction round in the same Task, not recovery of one failed file
  and not `task resume`. Never infer a full rerun from a status-query request.
- Select files/fields using `task retry <TASK_ID> --scope selected
  --resource-id <RESOURCE_ID> --field-id <FIELD_ID>`. Repeat selectors as needed;
  file and field selectors intersect. `--only-outdated` preserves current/manual
  values. With no selectors the active fields and all files are selected.
- Legacy `task retry TASK --resource-id RESOURCE` retains single-file recovery.
  Add `--scope selected` to explicitly re-extract that file. `--pending-result-id`
  is for settlement only and cannot be combined with rerun selectors.
- Read fields and their version with `task spec get TASK`. Use `task spec set TASK
  --input <JSON_FILE>` for the full reviewed field definition: `expected_version`,
  `task_rules`, `fields`, `apply_to_existing`, optional `restore_field_ids` and
  `resource_ids`. Omitted existing active fields are deleted; never send a partial
  list as the complete definition. `task spec clarify TASK --input <JSON_FILE>`
  requests suggestions with `expected_version`, `name`, and `description`.
- Correct or confirm results using `task field set|confirm TASK RESOURCE FIELD
  --input <JSON_FILE>`. Preserve `base_result_version`, `expected_spec_version`,
  `request_id`, the backend `value` envelope and optional `review`. Do not silently
  enable `review.apply_to_future`. Read exact current values/versions/evidence
  using `task status TASK --details`; read history with `task history TASK RESOURCE`
  and source previews with `task preview TASK RESOURCE`.
- `task copilot show TASK` reads the current draft/question; `task copilot steps
  TASK --after N` reads the conversation/execution history. `task copilot send TASK
  --text '<REQUEST>'` sends a new user instruction. For answers, confirmations,
  edited confirmations or dismissal use `--input <JSON_FILE>`, preserving the
  exact `kind`, `client_message_id`, `expected_version`, `reply_to`, `draft_id`,
  `draft_revision`, and `edited_fields` as applicable. Present the draft to the
  user before confirming; do not silently change confirm-only into confirm-and-rerun.
- `task list` supports `--search`, `--status`, `--file-id`, `--offset`, `--limit`.
  `task memory list TASK` reads task memories; `task memory revoke TASK MEMORY`
  revokes only an explicitly selected correction memory.
- `task page TASK` obtains a fresh server-issued `result_page_url` without adding
  files or running extraction. Requires a backend supporting the page-link query.
  Follow the host's link-opening contract; never reconstruct or expose a grant.
- Preserve request/version identities on conflicts or ambiguous failures. Do not
  refresh versions and automatically resend a mutation, loop task-wide retries,
  or create replacement tasks. Respect the server's regional availability and
  capability errors. Successful submission is not completed extraction.
- These workspace commands require CLI 2.4.4-beta.7 or a later matching release.
  Do not assume an older installed beta includes them. Check CLI help first.

#### Extraction billing and recovery

- Extraction uses its own 100 free pages per user per day, then normal billing.
  Read `extraction_quota.daily_pages_remaining` and `extraction_quota.reset_at`
  from `xparse-cli quota --output json`. These are server facts, not a local
  estimate. If `extraction_quota` is absent, the extraction allowance is unknown;
  do not infer 100 pages remaining or substitute the parse allowance.
  Missing `extraction_quota` means unknown (including unauthenticated callers, older servers, or a temporarily unavailable extraction ledger); never replace it with zero or 100. The existing `free_package` belongs to `pdf_to_markdown`, not extraction.
  Parse allowance is not the extraction allowance. The server checks the whole
  file against remaining free pages plus paid funds; insufficient funds reject
  the file, without partially charging it. Successful settlement is once per
  user, Task and file; a new Task may incur another charge for the same file.
  Never create a replacement Task to recover a failure.
- Creation returns `operation_id`, including in structured error details when
  submission is ambiguous. Replay only with that same `--operation-id`; do not
  generate another ID or infer a new Task from a missing response. For recovery
  across an interrupted CLI process, provide and retain the ID before submission.
- Inspect `task status <TASK_ID> --details` for the exact `resource_id`,
  `error_code`, `billing_status`, `pending_result_id` and `agent_activity`.
- If `billing_status` is `pending_settlement`, the generated result is privately
  saved but not yet delivered. After funding, use
  `task retry <TASK_ID> --resource-id <RESOURCE_ID> --pending-result-id <PENDING_RESULT_ID>`.
  Preserve both IDs on ambiguous responses and replay that same request. This
  only settles and publishes the saved result: no model invocation or extra
  model budget. A repeated successful settlement returns the same result.
  A stale candidate returns a conflict; never silently replace it with a rerun.
- Settlement leaves the Task suspended. The delivered file is available through
  `task result` / `task export`; report that remaining work is still incomplete.
- A failed file with no pending result can be explicitly re-extracted using
  `task retry <TASK_ID> --resource-id <RESOURCE_ID>`. This operation has no
  idempotent replay guarantee. If its response is ambiguous, inspect status;
  do not automatically resend it. Retry multiple failed files serially, waiting
  for the current round to terminate and inspecting status before the next one.
- To continue a suspended Agent after explicit user direction, use
  `task resume <TASK_ID>` without parse `--run-id` or `--after-funding` flags.
  This continues other work and adds server-controlled execution budget.
  Preserve the returned `command_id` and `checkpoint_version`, including on
  failure, and replay with `--command-id <COMMAND_ID> --checkpoint-version <VERSION>`.
  Exact replay uses the original pair even if status has since changed. Settle
  pending results first. Never automatically loop resume or add budgets.

For an append request, send only the newly supplied files to the same
extraction Task. Use a source path supported by the installed CLI: parsed File
Asset IDs, history IDs, or managed local-file import. Do not mix managed imports
and parsed/history sources in one command. Do not execute
`task run --task-type extract` or resend old files. Preserve the existing
extraction instruction and fields; do not turn the append request into a new
`--instruction`. No extraction Run ID is accepted:

```bash
xparse-cli task add <EXTRACTION_TASK_ID> \
  --file-id <NEW_FILE_ASSET_ID>
# If supported, for a history file instead:
xparse-cli task add <EXTRACTION_TASK_ID> --history-id <HISTORY_ID>
# If supported, for a local file instead:
xparse-cli task add <EXTRACTION_TASK_ID> <NEW_LOCAL_FILE>
```

Check that the returned `task_id` is the original `<EXTRACTION_TASK_ID>`, then
poll that same Task. Direct File Asset/history additions may return a
`result_page_url`; use it only when actually returned. Managed local-file import
returns `operation_id`, `uploaded_file_ids`, and import state instead of a page
URL: preserve those identities, follow its import recovery/status instructions,
and request a fresh server-issued link with `task page <EXTRACTION_TASK_ID>`
only when supported and a page is needed. Never invent a URL. If append fails,
follow the error's recovery instructions on the same Task; never fall back to
creating another extraction Task.

When MCP tools are available, the equivalent contracts are
`create_extraction_task(file_ids, instruction, operation_id)` and
`add_extraction_task_files(task_id, file_ids)`. Use `file_ids`; do not invent
Parse Job, Parse Task Run, or source-pointer parameters.

### Full document or conversion

Use one parse command:

```bash
xparse-cli parse <INPUT> --api auto
```

For PDFs, pass an output directory so long Markdown is not truncated in
terminal output. The CLI creates the directory when it does not exist:

```bash
xparse-cli parse report.pdf --api auto --output <DIR>
```

Read the saved result before requesting more detail. Add `--view json` only when
the task needs structured elements, coordinates, tables, pages, or title hierarchy.

### Server-generated document exports

When the user explicitly asks to export one document as DOCX, PDF, or XLSX,
explain that this requires the paid parse endpoint and obtain paid approval
before running the command. Request only the formats the user needs:

```bash
xparse-cli parse <INPUT> --api paid --export docx,pdf,xlsx --output <DIR>
```

- `--export` accepts `docx`, `pdf`, and `xlsx`; pass a comma-separated list or
  repeat the flag. The CLI removes duplicates, and XLSX automatically uses the
  table export scope.
- `--api paid` and `--output <DIR>` are required when `--export` is present.
  Immediately before downloading, the CLI resolves the selected AppKey or OAuth
  identity again so a long parse can refresh an expired OAuth token. It then
  downloads each successful export and verifies the saved file size.
- The output directory contains the ordinary parse result plus
  `<basename>.docx`, `<basename>.pdf`, and/or `<basename>.xlsx`. Read or return
  those local files as the task result. If a name would overwrite the input,
  the CLI uses `<basename>.export.<format>`. Do not expose backend download
  URLs, `file_id` values, or authorization details to the user.
- This single-document feature is separate from `task export`, which exports
  the Markdown results of a durable multi-document Task.

### Targeted reading, search, or extraction

For a local document, use:

```text
get_doc_info -> parse the complete document -> navigate -> extract
```

1. Run `get_doc_info <FILE>` and retain its exact `doc_id`.
2. Run `parse <FILE> --api auto` without `--page-range`. A successful complete
   local parse writes the navigation cache automatically.
3. Use `get_outline`, `search_text`, or `read_pages` to locate relevant content.
4. Batch the required `read_content` calls after navigation is complete.

There is no separate cache-preparation command. A successful complete local
`parse` is the only preparation step.

Page-range parses intentionally do not replace the complete-document navigation
cache. URL parses have no stable local `doc_id`, so use their direct parse output
instead of local navigation commands.

Read [navigation.md](references/navigation.md) before performing targeted
navigation or extraction.

## Efficiency and fallback rules

- Plan all navigation before reading sections; target no more than eight
  `read_content` calls per task and issue independent reads together.
- Prefer `search_text` for names, dates, amounts, and percentages. Read a full
  section only when its surrounding prose or table structure is needed.
- If an outline is truncated, drill down with `--parent-id`; do not guess IDs.
- Keep unrelated one-document parses serial. For a multi-document batch, use
  one durable Task instead of parallel `parse` commands.
- Retry a transient service failure once at most and only when its structured
  error says `retryable=true`. Stop immediately on any non-retryable service
  failure. Never silently skip a failure.
- For local documents, try this Skill before Python, PyMuPDF, pdfplumber, qpdf,
  OCR tools, image conversion, or custom scripts.
- If a document is encrypted or required input is missing, ask the user instead
  of trying alternate tools.
- Only fall back after xparse-cli clearly cannot complete the task, and explain why.

## Quick reference

| Goal | Command |
|------|---------|
| Parse with automatic free routing | `xparse-cli parse <FILE> --api auto` |
| Force free endpoint only | `xparse-cli parse <FILE> --api free` |
| Explicit paid parse | `xparse-cli parse <FILE> --api paid --auth-method oauth` |
| Save Markdown | `xparse-cli parse <FILE> --api auto --output <DIR>` |
| Save JSON | `xparse-cli parse <FILE> --api auto --view json --output <DIR>` |
| Export one document as DOCX/PDF/XLSX | `xparse-cli parse <FILE> --api paid --export docx,pdf,xlsx --output <DIR>` |
| Parse selected pages only | `xparse-cli parse <FILE> --api auto --page-range 1-5` |
| Encrypted document | `xparse-cli parse <FILE> --api auto --password <PWD>` |
| Character details | `xparse-cli parse <FILE> --api auto --view json --output <DIR> --include-char-details` |
| Show current quota | `xparse-cli quota --output json` |
| Show manipulation-detection quota | `xparse-cli quota --service manipulation_detection --output json` |
| Detect manipulation or AIGC risk | `xparse-cli detect-manipulation <FILE_OR_URL> --view json` |
| Run a durable local-file Task | `xparse-cli task run --files '<GLOB>' --api auto` |
| Upload one file without parsing | `xparse-cli upload <FILE> --operation-id <OPERATION_ID>` |
| Create extraction from a ready File Asset | `xparse-cli task run --task-type extract --instruction '<REQUEST>' --file-id <FILE_ASSET_ID>` |
| Inspect stable Task resources | `xparse-cli task status <TASK_ID> --details` |
| Append newly parsed File Assets to an extraction Task | `xparse-cli task add <TASK_ID> --file-id <FILE_ASSET_ID>` |
| Append an existing history file when supported | `xparse-cli task add <TASK_ID> --history-id <HISTORY_ID>` |
| Append a local file by managed import when supported | `xparse-cli task add <TASK_ID> <LOCAL_FILE>` |
| Rerun every Resource under a Task | `xparse-cli task rerun <TASK_ID> --mode all` |
| Add files and create a new Run | `xparse-cli task rerun <TASK_ID> --mode new-files --files '<GLOB>'` |
| Rerun selected Resources | `xparse-cli task rerun <TASK_ID> --mode selected-files --resource-id <RESOURCE_ID>` |
| Check an exact Task Run | `xparse-cli task status <TASK_ID> --run-id <RUN_ID>` |
| Read one Task result | `xparse-cli task read <TASK_ID> <FILE_OR_RESOURCE> --run-id <RUN_ID>` |
| Export all completed results | `xparse-cli task export <TASK_ID> --run-id <RUN_ID> --output <DIR>` |
| Inspect per-file failures | `xparse-cli task debug <TASK_ID> --run-id <RUN_ID>` |
| Continue one existing Resource after Run error 40423 | `xparse-cli task continue <TASK_ID> --password <PASSWORD>` |
| Continue multiple existing Resources after Run error 40423 | `xparse-cli task continue <TASK_ID> --password <SELECTOR>=<PASSWORD> --password <SELECTOR>=<PASSWORD>` |
| Resume after paid approval | `xparse-cli task resume <TASK_ID> --run-id <RUN_ID> --approve-paid` |
| Resume after funding | `xparse-cli task resume <TASK_ID> --run-id <RUN_ID> --after-funding` |
| Start local navigation | `xparse-cli get_doc_info <FILE>` |
| Show cached outline | `xparse-cli get_outline <DOC_ID>` |
| Search cached text | `xparse-cli search_text <DOC_ID> <PATTERN>` |

`--output` accepts a directory, not an output filename. The CLI creates a missing
directory and writes `<basename>.md` or `<basename>.json` inside it.

## Authentication boundary

- The CLI supports AppKey, Device OAuth, and browser PKCE as documented in
  [authentication.md](references/authentication.md).
- Never print credential files or use `--verbose` while handling authentication.
- An explicitly selected authentication method must fail as that method; do not
  silently retry with another credential type.

## Setup and command discovery

Check installation with `xparse-cli version`. The package requires Node.js 18
or newer and can be installed with:

```bash
npm i -g xparse-cli
```

For users in China, use the npmmirror registry:

```bash
npm i -g xparse-cli --registry=https://registry.npmmirror.com
```

Use this Skill and its references as the command index. When live discovery is
necessary, read complete `xparse-cli --help`, then the complete help for the exact
command. Do not truncate help output with `head`, `tail`, or a fixed `sed` range.

Stop on unsupported or corrupt files, invalid credentials, exhausted quota,
missing paid approval, any non-retryable service failure, or a transient
failure after its single allowed Agent-layer retry.

## References

- [navigation.md](references/navigation.md): targeted outline, search, page, and content workflow.
- [task-runtime.md](references/task-runtime.md): durable multi-file routing, states, result access, and recovery.
- [authentication.md](references/authentication.md): AppKey, Device OAuth, and browser authentication.
- [cli-guidance.md](references/cli-guidance.md): modes, output, parameters, and limits.
- [api-reference.md](references/api-reference.md): response fields and service error codes.
- [error-handling.md](references/error-handling.md): retry, stop, and paid-approval decisions.
- [textin-key-setup.md](references/textin-key-setup.md): standalone legacy AppKey setup.
