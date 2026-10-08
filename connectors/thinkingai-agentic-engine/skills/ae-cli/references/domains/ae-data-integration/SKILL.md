---
name: ae-data-integration
description: "Bring local CSV, TSV, TXT, JSON, JSONL (NDJSON), XLS, and XLSX files into AE end-to-end: identify the source's business meaning, generate and confirm a tracking plan, transform rows into UE records, and upload. Also supports privacy-preserving local analysis and handing a small file to AE Agent. Use whenever a user wants to import offline/local data into AE or analyze a file without uploading it. Trigger words: 本地数据导入 / 离线数据 / 数据文件 / 文件导入 / 文件上报 / CSV 导入 / Excel 导入 / TSV 导入 / JSON 导入 / 导入到 AE / 导入到 ThinkingData / local data import / import local file."
---

# AE Data Integration

Turn local/offline files into AE data through one fixed pipeline of four submodules: **Source → Tracking plan → Transform → Sink**. A file is never uploaded merely because it is present: its business meaning is understood, confirmed once by a human, and only then ingested. The tracking plan is generated and confirmed **before** ingestion (data governance shift-left) — see [references/tracking-plan.md](references/tracking-plan.md).

Two entrances lead here: the AE Agent dialog (attach / plus-button upload) and `ae-cli`. Two sink paths exist: RESTful API for one-time/small loads (current phase), and LogBus / DataX for recurring/high-volume loads (next phase). Source and Sink are pluggable — adding one does not change the main pipeline.

## Mandatory safety rules

- Treat file paths, receiver endpoints, APPIDs, mappings, generated artifacts, and raw rows as sensitive.
- Do not print source values while inspecting. Summarize types, ratios, counts, warnings, and fingerprints only.
- Inspect samples are bounded but still sensitive. Summarize them; never paste raw sample values into a chat summary.
- Do not invent account IDs, distinct IDs, event times, event names, projects, APPIDs, receivers, or timezones.
- `value_mapping` and `random_pool` are explicit user decisions. Never invent them.
- Never auto-fill a missing time for `track`/`track_*` rows. A missing time on user-profile rows may be filled with the current time only by setting `missing_time: 'now'` and only after the user explicitly confirms it.
- The mapping's fill-in options (`missing_time: 'now'`, `account_id_value`/`distinct_id_value`, `random_pool`, `exclude_columns`, `value_mapping`) record a decision the user has already made; they are never to make a validation failure disappear. When `convert` quarantines rows, present the failure first — the error `code`, the row count, its share of the total, and which events or time ranges are affected — and state the consequence in the user's terms ("3,000 events would carry a time that is not when they happened"). Only after the user has seen that may one of these options be set. When the evidence is insufficient, report the batch as not passed and pending customer data; never shrink the upload scope to manufacture a pass.
- Do not read or send an AE access token or CLI token to `/sync_json`. The receiver request uses only APPID and UE data.
- Never execute `data-integration upload` until the user has seen the target, mapping, valid/quarantined counts, batches, and dry-run and has explicitly confirmed that upload.
- A blocked manifest requires a second, explicit clean-subset decision. Never add `--allow-clean-subset` implicitly.
- If a batch times out or loses the network, treat that batch as unknown. Stop. Ask the user to verify receiver/AE data before the user chooses `--resume-from`; never resume automatically.
- Local analysis stays local. AE Agent attachment is a separate, confirmed branch with a 50 MB per-file limit.

## When to use / When NOT to use

Use this skill when the user wants to bring a **local data file** (CSV/TSV/TXT/JSON/JSONL/XLS/XLSX) into AE, or analyze such a file locally without uploading.

| User intent | Use this instead |
| --- | --- |
| How to integrate the SDK / tracking code / LogBus2 config / reporting-error triage (usage Q&A, no local file) | ae-data-integration-helper |
| Database / datasource direct sync (MySQL, DataX, data warehouse, data-dev platform) | ae-dataops |
| Community content (posts / comments / chat / WeCom groups) insight or submission | ae-community |
| Generate / upload a project-level tracking plan (source material is PRD / chat / template / code; deliverable is a real platform tracking plan) | ae-generate-tracking-plan |
| Upload documents / URLs to a knowledge base | ae-kb |
| Reports / dashboards / queries / governance on data already in AE | ae-analysis |
| Dimension / dictionary data (a stable-entity lookup — city / product / device) to load as a dimension table bound to a property | ae-metadata |

This skill also produces a tracking-plan draft (`source_type: data`) as a governance prerequisite; that draft is an input to ae-generate-tracking-plan, not a substitute for its five-phase platform plan.

## Workflow

Walk the four submodules in order. Each submodule is its own reference; follow it and come back here for the next step.

1. **Source — business identification.** Read [references/source-inspect.md](references/source-inspect.md). Profile every file fully, infer its business meaning using business-doc / user-prompt priors, then pick a branch via [references/ue-routing.md](references/ue-routing.md): UE ingestion, dimension routing ([references/dimension-routing.md](references/dimension-routing.md)), or local analysis.
2. **Reuse check.** If the profile is `ue_eligible`, read [references/reuse.md](references/reuse.md) and match the recommended mapping against the handoff index. `reuse` searches the current directory's `.ae-cli/data-integration/` upward, then `~/.ae-cli/data-integration/`, so a package written elsewhere is still found. A match proposes a frozen package; after one explicit confirmation, run the returned `transform.mjs` command and jump to Sink (step 5). No match → continue.
3. **Tracking plan.** Read [references/tracking-plan.md](references/tracking-plan.md). The plan is generated from the mapping (`plan --mapping`), so confirm the recommended mapping's key system fields with the user first — `mode`, `#account_id`/`#distinct_id`, `#time` + timezone, `#event_name`, `#ip`/`#uuid` (see [references/transform.md](references/transform.md) steps 1–5) — then generate the event/property plan and get a single explicit confirmation from the user before touching data. The plan is a separate, required deliverable from the transform mapping: a user who supplies a column→field mapping directly has **not** completed this step, so build the plan from the confirmed mapping anyway. `user_set` still requires a plan (no events; every property becomes a user property). This step runs for **every** file: a second or later file merges its new events and properties into the existing project plan (tracking-plan.md step 4) — an existing plan is never a reason to skip it.
4. **Transform.** Read [references/transform.md](references/transform.md). Map columns to AE system fields and properties, convert, and quarantine dirty rows per [references/ue-mapping.md](references/ue-mapping.md).
5. **Sink — upload.** Read [references/sink-upload.md](references/sink-upload.md). Resolve the destination, dry-run, confirm, then upload per [references/sync-json-upload.md](references/sync-json-upload.md). `receiver_accepted` is not persistence: after a ~1-minute ingestion delay, verify the data landed with ae-cli (`tracking live-data list` / `tracking ingest summary` / `tracking ingest-error list`) rather than telling the user to check the console.
6. **Handoff.** Read [references/handoff.md](references/handoff.md). Export the reusable package (pipeline descriptor + frozen mappings + stage executors + docs) and a shareable zip; in the completion response, state the absolute zip path, the package directory, and the one-line way to run the next same-shape file.

## Error handling

When a step fails, classify the failure before acting — see [references/error-handling.md](references/error-handling.md). A quarantined row, a ragged line, and a disk-full are three different problems with three different responses: match on the error `code`, never retry a parse failure by guessing the encoding, and never report a program failure as a data problem.

## Local analysis branch

When UE prerequisites fail, the file is an aggregate/analytical table, or the user wants analysis rather than ingestion, use [references/local-analysis.md](references/local-analysis.md) instead of the ingest pipeline.

## Optional AE Agent attachment handoff

Offer this only when the user asks to continue in AE Agent. Explain that the file leaves the local machine and ask for explicit privacy confirmation.

- Reject files over 50 MB; suggest local analysis or user-controlled splitting.
- Read the `ae-agent` `+add-attachment` reference before calling it.
- Dry-run first, show file name/type/size, and wait for confirmation.
- Then run `ae-cli agent +add-attachment --file '<path>'`.
- Return the attachment result, a copyable analysis prompt, and directions to open AE Agent.
- Do not create or execute an Agent conversation.

## Completion response

State which submodules ran, source fingerprint and selected data set, the tracking plan status, generated artifact paths, mapping confidence, valid/quarantined counts, and upload/attachment status. Keep facts separate from recommendations and clearly state whether persistence was verified.
