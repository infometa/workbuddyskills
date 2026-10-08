# analysis data retrieval routing

This is the single routing policy for analysis data retrieval commands. It is scoped to `ae-cli analysis` data queries only; do not generalize it to other `te-cli` business modules.

## Scope

This policy applies to:

- `analysis adhoc run` / `analysis adhoc export`
- `analysis report-data run` / `analysis report-data export`
- `analysis dashboard-report-data run` / `analysis dashboard-report-data export`
- `analysis bi-panel-page-data run` / `analysis bi-panel-page-data export`
- `analysis event-detail run` / `analysis event-detail export`
- `analysis entity-detail run` / `analysis entity-detail export`
- `analysis drilldown-events run` / `analysis drilldown-events export`
- `analysis drilldown-entities run` / `analysis drilldown-entities export`
- `analysis drilldown-user-events run` / `analysis drilldown-user-events export`
- `analysis user-cluster-member list` / `analysis user-cluster-member export`
- `analysis user-tag-member list` / `analysis user-tag-member export`
- `analysis history-tag-data run` / `analysis history-tag-data export`
- `analysis history-tag-data-drilldown run` / `analysis history-tag-data-drilldown export`

This policy does not apply to:

- `analysis user-cluster list/get`, `analysis user-tag list/get`, create/update/refresh/delete, ID-file operations, and history-tag management commands.
- `analysis-meta`, metadata, DataOps, Community, Engage, or other business modules.
- Report/dashboard/BI asset list commands, catalog exports, definition import/export, or management commands.

## Cache policy for report and ad-hoc data

Apply this cache policy to `analysis adhoc run|export` and
`analysis report-data run|export`:

- For an ordinary query, omit `--use-cache`; its effective default is `true`.
  This allows a cache read but does not prove that the query actually hit a
  cache.
- Pass `--use-cache false` only when the user explicitly asks for fresh data,
  a refresh or recomputation, to bypass/disable cache, or says the underlying
  data was just updated. Words such as "latest" or "current" trigger this only
  when they refer to data freshness, not merely to a selected time window.
- When the user explicitly compares with a freshly refreshed analysis UI,
  pass `--use-cache false`. A request that merely mentions a report or UI does
  not imply this freshness requirement.
- If the user reports that CLI/Agent data differs from the analysis UI, repeat
  the same semantic query exactly once with `--use-cache false`. Preserve the
  project, asset or model definition, filters, time range, timezone, cluster
  route, and other query inputs. Explain that any difference may come from
  cache policy or refresh timing; do not enter a retry loop.

The Agent cannot observe whether another browser session is open, whether a UI
query used cache, or whether the user is demonstrating the product. Never infer
a demo scenario and never change cache policy based only on the audience or
interface. `--use-cache` controls whether cache reads are allowed for this CLI
query; it neither changes the saved asset/UI configuration nor exposes an
actual cache-hit result. Do not claim cache hit or miss unless the response
contains explicit backend evidence.

## Decision rule

Synchronous data commands use `--preview-rows` for the maximum business rows
returned per result. Omit it to use the model's current cluster-configured
synchronous limit; the CLI does not detect an Agent sandbox or inject a smaller
default. Agents should normally pass `--preview-rows 100` to control context and
memory use. Human or script callers may omit it when the native synchronous
result is wanted directly. User tag/cluster member list commands are the
exception: omission returns at most 1000 rows, matching the UI member query.

Use `run` only when all conditions are true:

- The user needs an inline preview or immediate JSON result.
- The expected result fits in the chosen synchronous preview.
- The query is expected to finish within the sync timeout window, normally `<=180` seconds.

The runtime validates an explicit `--preview-rows` against the effective model
or SQL cluster configuration. Do not hard-code one universal maximum. Model
queries reserve their own internal total/summary rows, so the physical query
limit may be `N+M`; these internal rows do not reduce the requested `N` business
rows. SQL/list-shaped queries may fetch one look-ahead row to determine
`has_more`. User tag/cluster member list commands accept explicit values up to
100000; this does not change their omitted default of 1000.

The dashboard report-data sync timeout defaults to 180 seconds because one call may execute multiple reports. Other sync analysis data retrieval commands default to 120 seconds. The maximum remains 180 seconds, and an explicitly supplied lower timeout always wins.

Detail `run` commands (`event-detail run` and `entity-detail run`) support
`--preview-rows`, but not `--limit`, `--offset`, or stable pagination. If
`has_more=true`, switch to the matching `export`.

User member, history-tag drilldown, and result drilldown `list/run` commands are bounded previews. They do not expose pagination. Use the matching `export` command for full or unknown-size data.

Use `export` when any condition is true:

- The user asks for full data, all rows, a downloadable file, or an export.
- The result size is unknown or expected to exceed the chosen preview.
- The query may be long-running or may exceed the sync timeout window.
- A data-query `run` times out.
- The result should be durable and processed from a file instead of printed inline.

Export commands are asynchronous artifact jobs and do not accept
`--preview-rows`. Native full-download paths retain their existing model/SQL total row
ceilings.

`--artifact-format` selects the logical row format, not compression. Read the returned `format`, `compression`, `file_name`, `content_type`, and `content_encoding`; analysis query exports are currently gzip-compressed even when the logical format is `jsonl` or `csv`.

Default and maximum runtime is 21600 seconds (6 hours). Omit `--timeout-seconds` to use that default, or pass a smaller value when the caller explicitly wants an earlier deadline.

Choose one lifecycle form:

```bash
# Submit only. Preserve the returned run_id/artifact_id.
ae-cli analysis adhoc export ...

# Submit, then wait through repeated short inspect requests.
ae-cli analysis adhoc export ... --wait

# Submit, wait, and stream the completed artifact to a local file.
ae-cli analysis adhoc export ... --output <file>

# Resume after interruption, client wait expiry, or a detached shell.
ae-cli analysis run wait --run-id <run_id> [--output <file>]
```

`--output` implies `--wait`. `--wait-timeout-seconds` controls only how long the
current CLI process remains attached; it defaults to 600 seconds and is capped
at 21600 seconds. The server lifecycle descriptor remains a hard upper bound
with a short artifact-materialization grace period. Ctrl-C, client wait expiry,
or a persistent transient network failure stops only local waiting; it never
cancels the remote run. Resume with the returned `resume_command` or printed
`analysis run wait` command.

Waiting succeeds only for `status=SUCCEEDED` plus
`artifact_status=COMPLETED`. Run or artifact `FAILED`/`CANCELED` is terminal and
returns a non-zero error. Unknown states, authorization failures, and 404s fail
immediately instead of being polled indefinitely.

Downloads stream into a temporary file in the destination directory and publish
the complete file atomically. Existing output paths are refused by default; pass
`--force` only when replacement is intentional. The primitive commands remain
available for manual control:

```bash
ae-cli analysis run inspect --run-id <run_id>
ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output <file> [--force]
```

Cancel an async run/export with:

```bash
ae-cli analysis query cancel --run-id <run_id>
```

If `analysis run inspect`, `analysis run wait`, or `analysis artifact download` returns HTTP 404 for a valid `run_id` / `artifact_id` from the same export response, treat it as a backend route/capability deployment issue. Do not keep polling or invent download URLs.

If the current host returns `CAPABILITY_NOT_FOUND` for a documented command, treat it as host/backend capability unavailability. Do not retry with different JSON shapes or flags; choose another supported path only when it satisfies the user's request, otherwise report the backend gap.

Drilldown event/entity/user-event, ad-hoc/report/dashboard model, BI chart,
user tag/cluster member, and history-tag drilldown exports use Common's
full-download streaming paths. They accept no `limit`, `offset`, `page_num`, or
`page_size`, and remain bounded by the existing full-download ceiling. Do not
collect full data by repeated `list/run` calls.

User tag/cluster member and history-tag drilldown exports support both
`jsonl.gz` and `csv.gz`, defaulting to `jsonl.gz`; format selection does not
change the native full-download query or introduce paging.

## Follow-up context

Only synchronous `adhoc run`, `report-data run`, and `dashboard-report-data run`
previews with at least one available follow-up action create `query_context_id`
and compact `sources[]` summaries. SQL, BI SQL, unsupported models, and previews
without a drillable analysis angle do not create a useless context. Exports and
downloaded artifacts never create this context and never expand the selectable
result. The Common/UI synchronous result is the drilldown boundary.

Before composing a follow-up coordinate, call `analysis query-context get` with
the returned `query_context_id` and, for multi-source results, one exact source
selector from the compact summary. The command reads the full row, column, and
metric options already stored for that preview; it does not rerun the query.

Follow-up commands are allowed only when the compact source summary advertises the exact action. Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md), fetch full options with `analysis query-context get`, select only those returned row/column/metric options, and never infer source IDs, dates, groups, model fields, or analysis angles from display text.

Pass the original `--project-id` with every query-context or drilldown-context follow-up. Gateway uses it for project authorization, and Common rejects it if it does not match the project stored by the context ID.

When present, compare `effective_time_range` with `data_time_range`. `effective_time_range` is the resolved query scope, while `data_time_range` is the observed returned-row range. `clipping_reasons=[]` means the gateway applied no silent range cap; a narrower `data_time_range` then reflects available/returned data rather than a gateway range clamp.

Use that synchronous `query_context_id` for the advertised action only:

- `analysis drilldown-events run` or `analysis drilldown-events export`
- `analysis drilldown-entities run` or `analysis drilldown-entities export`
- `analysis query create-result-cluster`

Do not reconstruct or pass raw QP for follow-up drilldown or result-cluster creation.

If the synchronous response does not include `query_context_id` and the required
action, or `analysis query-context get` does not return the required selectable
options, stop before drilldown/result-cluster commands. Report that this preview
does not expose that follow-up.

For sync `run`, trust Common's `has_more`. Common uses model totals or one extra
lookahead business unit at the requested `preview_rows` boundary, or at that
model's configured boundary when `preview_rows` is omitted. The lookahead unit
is never returned, and reaching the boundary alone does not imply
`has_more=true`. Use `export` whenever completeness matters.

## BI page data note

`analysis bi-panel-page-data run --result-type charts` supports
`--preview-rows` per chart and has no row pagination contract. A configured
chart top-N still applies as a semantic chart limit. Summary is rendered
presentation data, is available only from `run`, and rejects `--preview-rows`.

Use `export --result-type charts` for complete, unknown-size, timed-out, or
long-running chart data. Common streams rows directly under
`model_full_download_limit`.

User tag-member, cluster-member, and history-tag drilldown exports call their
native full-download SQL paths and stream CSV rows directly into a gzip artifact.
These exports support `--property-names`, but do not support the preview-only
`--fields`, `--query`, or `--use-cache` options.

BI SQL page/chart data does not support this analysis drilldown contract.
