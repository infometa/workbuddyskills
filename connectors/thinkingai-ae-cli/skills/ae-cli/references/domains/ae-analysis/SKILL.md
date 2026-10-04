---
name: ae-analysis
version: 4.2.5
description: "Use ae-cli for AE/TE analysis-side data questions, asset operations, and asset governance: reports, analysis boards, BI dashboards, ad-hoc models, drilldown, detail data, alerts, clusters, tags, metrics, metadata, project configuration, tracking plans, governance asset lists/rules/lineage/impact/dependency, batch asset operations, projects, and resource links. Use when the user asks to query data, explain a change, export evidence, or inspect/create/update/govern analysis assets."
---

# ae-analysis

This is the single entry skill for analysis intent and command execution.

## Route before reading

1. Map the request to a command family before opening any reference.
   - Known family: open only its dedicated reference. For example, a retention request goes directly to `references/adhoc_run.md` plus the `retention` section of `references/ai_models.md`.
   - Unknown family: search [`references/command_index.md`](references/command_index.md) with `rg` or an equivalent text-search tool and keep only the matching rows. `command_index.md` is a search-only fallback; never open it with a whole-file read or print the entire file.
2. Read the selected command's dedicated reference before composing it:
   - `event list` -> `references/event_list.md`
   - `analysis dashboard list` -> `references/dashboard_list.md`
   - `personal-semantic-preference list` -> `references/personal_semantic_preference_list.md`
   - Asset center cross-source configuration (资产中心 / 跨源资产配置 / Excel 配置表导入): L3 discovery via `capability search "cross_source_config" --domain metadata --project-id <id>`; read [`references/cross_source_config.md`](references/cross_source_config.md) for workbook upload and validation. No dedicated business commands.
   - replace hyphens with underscores in gateway filenames.
3. For an AI-facing ad-hoc definition, also read [`references/ai_models.md`](references/ai_models.md).
4. For cluster/tag `--definition-request`, also read the matching [`references/user_cluster_models.md`](references/user_cluster_models.md) or [`references/user_tag_models.md`](references/user_tag_models.md). Shared primitives live in [`references/audience_models.md`](references/audience_models.md).
   - For tag periodic refresh, read `references/user_tag_create.md` or `references/user_tag_update.md`; they cover the enable switch, frequency/time schedule, cron alternative, and timezone behavior.
5. For analysis data retrieval, choose `run` or `export` using [`references/analysis_data_retrieval.md`](references/analysis_data_retrieval.md).
6. When an AI-QP compile failure contains `slot_kind`, `allowed_resource_types`, `search_targets`, and `next_action`, read and follow [`metadata_resolution.md`](metadata_resolution.md).

Routing is complete when one command family and its dedicated references are selected. The generated command index is exhaustive and must stay out of model context except for matching search rows. This file contains routing and workflow rules only; do not duplicate a hand-maintained command inventory here.

## Boundaries and priority

Use this skill for these CLI services:

- `analysis`: reports, dashboards, BI panels, ad-hoc analysis, drilldown, detail data, alerts, clusters, tags, and async runs/artifacts.
- `analysis-meta`: gateway metadata assets, events, properties, virtual metadata, metrics, data tables, exchange rules, and super metadata. Cross-source asset configuration uses the metadata L3 catalog instead.
- `analysis-governance`: gateway asset governance operations, including governed asset lists/exports, lineage, dependency, impact, query history, rule schema/list/create/update/delete, batch asset actions, and operation records. Use this service for asset governance workflows, not for metadata event/property/metric CRUD.
- `tracking`: gateway tracking plan, checking, ingest, live-data, and event blacklist operations.
- `personal-semantic-preference`: current user's project-scoped personal semantic preferences. Use it as agent context before resolving ambiguous business wording, asset choices, or recurring user preferences.

For metadata gateway detail outside the commands in the generated index, use the metadata skill. For Engage, DataOps, or Community work, use the corresponding skill.

Use `ae-cli` as the only execution path for this skill. If a command is missing, unsupported, not implemented, or a capability gap is confirmed, report the gap and stop or provide framework-level guidance; do not switch to direct MCP execution. Repeated failures are not evidence of a capability gap until parameters, types, time formats, permissions, timeout choice, and payload construction have been checked. A validation error or `need_clarification` is a reason to correct the input, not to switch tools.

For tags and audience clusters, use the native `analysis user-tag ...` and `analysis user-cluster ...` gateway commands.

## Global AE CLI Rules

Command forms:

```bash
ae-cli analysis <resource> <action> [options]
ae-cli analysis-meta <resource> <action> [options]
ae-cli analysis-governance <resource> <action> [options]
ae-cli tracking <resource> <action> [options]
ae-cli capability search|inspect|validate|dry-run|run [options]
```

- Gateway commands use kebab-case flags such as `--project-id`; the CLI sends snake_case JSON.
- JSON values must be JSON string literals.
- Global flags include `--host`, `--format json|table`, `--jq`, `--validate`, `--dry-run`, and `--yes`. Use `--validate` alone to normalize complex capability input; use `--dry-run` alone for execution or risk preview.
- JSON is the default machine-readable output. On failure, preserve the structured error and non-zero exit.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, your reply **MUST open with** a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Never answer with only a project/table summary when a host_compat notice exists. Soft tip; `ok: true` can still carry the notice.
- Never invent command names, flags, payload fields, projects, resource IDs, asset names, event/property names, metric definitions, or dates.
- 中文时间表达必须按固定语义映射：最近7天/近7天 -> `mode=recent` -> QP `recentDay=0-7`，含今天；过去7天/前7天 -> `mode=previous` -> QP `recentDay=1-7`，不含今天。用户明确说明是否包含今天时，以该说明为准。完整映射见 [`references/ai_models.md`](references/ai_models.md)。

`CAPABILITY_NOT_FOUND` means the current host does not expose that gateway capability; changing parameters will not fix it. A permission error stops any dependent chain. A 404 while inspecting an async run is a route/deployment failure; do not poll the same ID forever.

Interpret gateway envelopes by state:

- `ok: true` with empty data is success and means no matching data. Never relabel an empty report/dashboard result as query failure.
- `ok: true` with `meta.partial: true` is partial success. Use the successful data and explicitly report `meta.failures`; do not fail the whole batch or hide failed items.
- `ok: false` is failure. Preserve `error.code`, `error.message`, and `meta.request_id`, `meta.invocation_id`, `meta.stage`, and `meta.failures` when present.
- Do not retry an unchanged failed command or guess alternative payload shapes. Retry only after applying concrete validation/clarification guidance or correcting a verified transient condition.

Failure evidence:

- A process exit code of 0 is not business success when the envelope says `ok: false`. Prefer direct CLI invocation; if a shell pipeline is necessary, preserve the CLI exit status with `set -o pipefail` and retain the complete error envelope rather than truncating it.
- `TE_TOOL_POLICY_DENIED` identifies the runtime authorization stage. Report its exact reason; it does not prove a backend schema check passed or that the user needs to log in again. Do not bypass policy or retry by changing the business scope.
- `INVALID_ANALYSIS_DEFINITION` / `INVALID_CAPABILITY_INPUT` identifies an input failure. Correct all relevant fields together within the allowed retry budget. Say "validation passed" only after an explicit successful validation response for the same complete definition on the same host.
- `QUERY_FAILED` establishes that the query failed; it does not establish the database or engine root cause. Preserve the returned error and correlation IDs, leave unavailable values unknown (not zero), and stop when the user requests no retries. Distinguish observed errors from unverified hypotheses.

For every gateway command that exposes `--request-id`, ae-cli generates a `request_id` and prints it to stderr before dispatch when the caller omits it. Preserve that ID with the final envelope and diagnostics. Pass an explicit `--request-id cli_<32 lowercase hex>` only when a caller-owned correlation ID is required.

### Execution invariants

- Probe the first page exactly once. Verify `ok`, the documented data shape, and the effective `limit` before starting a pagination loop.
- For paginated directory results, continue only with the returned `next_offset` while `has_more` is true. Never calculate a speculative offset, repeat the current page, or declare the list complete before `has_more` is false.
- Track the normalized command, input, and announced `request_id` for every invocation. Never resubmit an identical invocation while it is still in flight; wait for the current process, or inspect its returned `run_id` when it is asynchronous.
- Retry only the items named in `meta.failures`, and only when their `retryable` value and `next_action` permit it. Never retry successful or empty items from the same batch.
- For black-box coverage audits, maintain an explicit module × model × outcome matrix. Mark coverage complete only from observed responses; missing assets, permissions, or fixtures are environment gaps, not passing coverage.

## Mandatory routing

### Product terminology gate

- The Chinese product term `看板` means an analysis board backed by saved reports. Route it to `ae-cli analysis dashboard ...` and capability IDs under `analysis.dashboard.*`.
- The Chinese product terms `仪表盘` and `BI 仪表盘` mean a BI dashboard with worksheets, charts, and pages. Route them to `ae-cli analysis bi-panel ...` and capability IDs under `analysis.bi_panel.*`.
- These assets are not aliases. Never substitute an analysis board for a BI dashboard, or a BI dashboard for an analysis board.
- The standalone English word `dashboard` is ambiguous in this product. Before a write, ask whether the user means an analysis board (`看板`) or a BI dashboard (`仪表盘`) unless the surrounding context already makes the product asset explicit.
- If the requested BI-panel capability is unavailable or unauthorized, report that constraint. Do not fall back to creating an analysis board.

### Project gate

Before a project-scoped command:

1. Reuse a project only when its ID and host/environment were already verified in the same continuous conversation.
2. Otherwise call `project info list` and resolve the supplied ID/name.
3. If there are multiple plausible projects, the host is unclear, or no project matches, show the candidates and ask; never guess.
4. Re-verify after the user changes project, host, or environment.

### Personal Semantic Preferences

Before answering project-scoped analysis or asset-governance requests, call `ae-cli personal-semantic-preference list --project-id <project_id>` once per host, authenticated user, project, and conversation after the project is resolved. Keep that lightweight directory in conversation context; do not page it, search the database, or call list again for each question. The backend returns at most 200 entries using `HOT_160_PLUS_RECENT_40` and may return fewer to keep the payload within its size limit.

Use the returned compact catalog only as context. If one item is actually adopted to interpret the user's wording, asset selection, metric preference, or output style, fetch it with `ae-cli personal-semantic-preference get --project-id <project_id> --id <preference_id> --mark-used`. This also applies when the matched item is being used as the target for an `update`. Do not pass `--mark-used` for items that were only inspected or rejected.

The Agent owns the personal preference capture trigger. Choose `context_type` by meaning:

- `preference`: durable interpretation or output preference without an exact asset binding.
- `asset_context`: durable user wording or intent bound to one or more exact project assets. Send the complete ordered `resource_refs` array; each item has `resource_type`, string `resource_key`, and `display_name`. This identity is generic across reports, dashboards, events, properties, metrics, tags, clusters, data tables, and future asset types.
- `experience`: a confirmed reusable work method without an exact asset binding.
- `background`: stable personal context without an exact asset binding.

Any stable choice of a concrete asset, including an event-selection scenario, must use `asset_context`; do not encode asset IDs only in prose. A current-user working definition remains eligible for personal storage even when it would also benefit other users. Store it only as the current user's preference; do not copy the bound asset definition into its content or imply that it is shared authority. Keep future governance or lifecycle instructions out of the stored content. Do not save transient task details, one-off analysis results, company knowledge, or standalone metadata facts.

An explicit stable statement, correction, or confirmation that passes that evidence gate authorizes `personal-semantic-preference add` or `update` without a second "save" confirmation. Compare against the already loaded catalog first; when one existing preference matches, fetch it with `--mark-used`, update that existing preference, and avoid creating a duplicate. Otherwise add a new one. An explicit instruction not to retain it always wins. Delete remains high risk and requires explicit user confirmation.

After a successful add, update, or delete, merge that response into the conversation's cached directory locally. Do not call list again merely to observe the write.

Stale or expired preferences are automatically hidden by list filtering and backend maintenance. Do not look for or invent a separate command for that behavior.

### C. FUZZY_SEARCH_FALLBACK

For saved-asset operations on reports, dashboards, metrics, clusters, tags, and alerts, use the relevant list/search command first unless an exact ID or canonical asset name was already verified. For saved assets outside the analysis metadata catalog, broaden the keyword batch up to two times, then list all candidates. If no resource exists, stop instead of fabricating one.

For ordinary event, property, metric, cluster, and tag metadata discovery, keep one discovery budget per host, project, authenticated principal, and Agent conversation. Put the user's phrase and its useful synonyms in one `--queries` JSON array; matching is OR across at most 20 keywords. A successful remote search round with no confirmable candidate consumes one miss. A candidate stops discovery and requires user confirmation; it is not a miss. Validation, permission, network, and server errors are failures: they do not consume the budget and must not trigger a full export. After at most two ordinary miss rounds, the third remote discovery round must be one aggregate `analysis-meta catalog list` using the accumulated deduplicated queries and the union of applicable resource types. If that aggregate search is still unresolved, export the complete unified catalog exactly once and reuse it locally as defined in `metadata_resolution.md`. Once a valid complete catalog exists, do not call online resource-specific metadata list/search commands or `analysis-meta catalog list|export` again in that scope.

Only when explicitly complete event, property, metric, cluster, or tag metadata is needed, use that resource's `export --output <temporary_path>/<resource>` command. Event/property/metric exports use `.json`; cluster/tag exports use `.jsonl` and an integrity sidecar. Search the temporary file locally and keep the full rows out of model context. Do not page repeatedly to synthesize a complete catalog.

Do not pre-list events or properties before constructing an AI-facing intent model. Pass the user's wording directly in `definition`; the backend resolves it and returns `resolved` evidence. Call event/property metadata commands only when the user explicitly asks to inspect metadata, a structured compiler error instructs `next_action=search_candidates`, or the compiler reports an explicit metadata-resolution capability gap. When compiler candidates already exist, ask the user to confirm without another metadata call. If the user explicitly rejects every candidate for that path, treat the rejected set as exhausted and continue through the one aggregate-search workflow in `metadata_resolution.md`; do not terminate the original task or repeat the rejected candidates.

The ordinary discovery budget does not replace the entry path for structured AI-QP metadata failures. For those failures, `allowed_resource_types` is authoritative: collect the whole compiler error array and follow the one aggregate online search, optional full-catalog, conversation-reuse workflow in `metadata_resolution.md`. Never use a candidate from either path without user confirmation.

### Existing business asset before ad-hoc

When the request can map to a saved business definition:

1. Extract metric, dimensions, filters, time window, and comparison semantics.
2. Search reports; use dashboard search only to discover candidate embedded reports.
3. Before querying a selected dashboard's report data, call `analysis dashboard get` exactly once with the verified project and dashboard IDs. Inspect `effective_settings` and `filter_config`; dashboard default, dashboard business, and space business filters are already applied and call-time filters add AND conditions. Honor the saved fixed time unless the user explicitly supplies a supported time override. Preserve non-empty `location.folder_name`, `dashboard_name`, `remark`, and `notes[].note_title/description` as authored dashboard context for all results from that dashboard. Do not repeat the detail call per report.
4. Read the candidate definition and verify semantic equality, not merely a similar name.
5. Use report/dashboard data when the definition matches.
6. Use `analysis adhoc run|export` when no definition matches, the user explicitly requests ad-hoc exploration, or custom grouping/filtering is required.

Do not call removed QP builders or schema helpers for ad-hoc analysis. `--definition` is the AI-facing contract from `ai_models.md`, not raw QP or a frontend DTO.

### Result data versus metadata

- Metric value, trend, comparison, or anomaly -> saved report/dashboard first, then ad-hoc data.
- Metric definition search/create/update -> metadata commands.
- Event/entity rows -> `event-detail run|export` or `entity-detail run|export`.
- Events/entities from a query result -> pass the original `--project-id`, follow the returned synchronous `query_context_id` and compact source action summary, then call `analysis query-context get` for full coordinate options; never reconstruct raw QP or use export rows as coordinates.
- Cluster/tag definition -> matching gateway cluster/tag commands and matching model reference.
- Tag/cluster candidate values, including requests phrased as "latest version" or "latest result" -> resolve the exact asset, then use `analysis filter-value list` with `cluster_date_policy=LATEST`. This means the latest computed data snapshot, never a definition or configuration release; do not invent version lists, version IDs, draft states, or publish states.
- Alert/configuration/tracking-plan requests -> the dedicated gateway command reference from the index.

### Run, export, and follow-up

- `run` is a bounded inline preview for work that can complete within the synchronous limits. Agents should normally pass `--preview-rows 100`; omitting it deliberately uses the model's current cluster-configured synchronous limit. User tag/cluster member list commands are the exception: omission defaults to 1000 rows, matching the UI member query.
- `export` is for complete, unknown-size, over-limit, or long-running results. It returns `run_id` and `artifact_id`.
- Drilldown event/entity/user-event exports are `csv.gz` full-download streams bounded by `model_full_download_limit`; never pass or simulate `limit`, `offset`, `page_num`, or `page_size`.
- Plain `export` submits only. Add `--wait` to wait for terminal state, or `--output <file>` to wait and atomically stream the completed artifact; `--output` implies wait. Existing files require explicit `--force`.
- Resume detached or interrupted work with `analysis run wait --run-id <run_id> [--output <file>]`. Local interruption never cancels the remote run; cancel only through the explicit `analysis query cancel` command.
- `analysis run inspect` and `analysis artifact download` remain primitive lifecycle commands. Do not call raw lifecycle URLs. Use `--wait-timeout-seconds` only to bound local waiting; it never changes or cancels the remote runtime.
- Drilldown requires the original `--project-id`, a synchronous preview context, and row/column/metric coordinate options fetched with `analysis query-context get`. Common rejects a project ID that does not match the stored context. If the context/options are absent or the action is not advertised, report that drilldown/result-cluster creation is unavailable.

### Writes and destructive operations

Write only with explicit user intent. Use `--validate` alone while correcting complex input, or `--dry-run` alone to inspect the resolved request and execution impact; do not stack both by default. Execute `read` and ordinary `write` commands without `--yes`. For `high-risk-write`, dry-run first, summarize the target and impact, wait for explicit user confirmation, and only then execute the unchanged command with `--yes`.

Project-space and folder create/delete/share are L3 capabilities rather than curated `analysis` commands. Read the matching command reference, then use `ae-cli capability inspect|dry-run|run`; discover `*.members` through `capability search|inspect|run` and [`references/analysis_gateway_assets.md`](references/analysis_gateway_assets.md). For `risk=high-risk-write`, dry-run first, summarize the impact, and execute with `--yes` only after a later explicit confirmation.

After a successful create/update, if a resource ID and supported resource type are available, call `analysis-meta asset url-get` and return the link. Explicitly state when link generation is skipped because no resource ID exists or when it fails.

## Analysis workflow

For a data question:

1. Clarify only missing facts that change the query: KPI, scope, time window, dimensions, filters, and baseline.
2. Pass the project gate.
3. For AI-facing intent models, let the backend resolve event/property wording and consume `resolved`; discover metadata directly only for explicit metadata inspection, compiler clarification, or a reported resolution capability gap.
4. Check existing reports/dashboards when applicable.
5. Run or export one reproducible query path.
6. For anomalies, compare consistent scopes, rank drivers, then drill down to users/events only when result contexts permit it.
7. Return conclusion, evidence, limitations, and a concrete next action.

For attribution, use the algorithms and self-checks in [`references/analysis_interpretation.md`](references/analysis_interpretation.md). The main driver is determined by absolute contribution, not the largest relative growth rate.

## Output requirements

- Lead with the conclusion.
- Include the metric, time window, dimension/filter scope, value, and baseline needed to reproduce it.
- Separate observed evidence from inferred causes and state uncertainty.
- For attribution, include total absolute/percentage change and dimension contributions sorted by absolute delta; verify the contribution sum.
- For saved dashboard answers, use non-empty `location.folder_name`, `dashboard_name`, `remark`, and `notes[].note_title/description` to establish business scope. Label folder names and notes as authored context, separately from observed query evidence.
- Do not return an unexplained raw table.
- State missing data, definition, permission, or capability constraints explicitly.

## Maintenance

When commands change, update source command metadata and the dedicated reference, then run:

```bash
npm run generate:analysis-skill
npm run verify:analysis-skill
npm run verify:analysis-tools
```

The verification fails for missing command references, retired/orphan command references, or a stale generated index.
