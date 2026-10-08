# Handoff (reusable package)

After a successful run, export a **handoff package** so the next file of the same shape skips the full pipeline. The package is a DataX-style pipeline — a declarative `source → transform → sink` descriptor plus generic stage executors that dispatch to `ae-cli data-integration` subcommands. It freezes the transform logic (the confirmed mappings) and the tracking-plan reference, and ships a `bin/` directory that a human or agent can run directly. It never re-freezes raw data or upload secrets.

## When

Run handoff after Transform — or after Sink — once the mappings are confirmed. It is local-only and idempotent: re-running it for the same table refreshes the package in place.

## CLI

```
ae-cli data-integration handoff --mapping <mapping> [--mapping <mapping2> ...] [--plan-file <draft.json>] [--pushurl <url>] [--project-id <id>] [--out-dir .ae-cli/data-integration]
```

- `--mapping` — one or more confirmed `ae-data-integration-mapping/v1` mappings (the frozen transform logic, including `value_mapping` and `flatten_rules`). Repeat it for multi-sheet workbooks: one mapping per sheet.
- `--plan-file` — optional tracking-plan `draft.json` to reference inside each mapping directory (`plan.json`).
- `--pushurl` — optional receiver base URL to record as the reuse upload target (the sink endpoint is `pushurl` + `/sync_json`). Record it when the next same-shape file will most likely land at the same receiver.
- `--project-id` — optional numeric destination project ID to record; `bin/upload.sh` derives the APPID from it via `project info get` at upload time.
- `--out-dir` — handoff root. Default `.ae-cli/data-integration/` (project workspace; travels with the project).
- `--dry-run` previews the fingerprints, target, file list, and zip path without writing.

## Package layout

```
.ae-cli/data-integration/    ← handoff root (= out-dir, project workspace)
  pipeline.json             ← source → transform → sink descriptor (ae-data-integration-pipeline/v1)
  index.json                ← shared structure-fingerprint index (reuse detection)
  shape.json                ← per-mapping column baseline (shape gate)
  <fingerprint[:16]>/       ← one directory per mapping
    mapping.json            ← frozen mapping
    transform.mjs           ← node transform.mjs <new-file> [<output-dir>]
    plan.json               ← optional tracking-plan reference
  bin/                      ← generic stage executors (read pipeline.json)
    run.sh                  ← source → transform → plan (never uploads)
    upload.sh               ← sink (dry-run by default; --confirm uploads; resolves recorded target)
    bind_mapping.py         ← shape check + rebind sha256/data_set to the new file
    summarize.py            ← valid/quarantined counts
    plan_check.py           ← tracking-plan coverage gate (exit 3 on new events/properties)
    verify.py               ← soft persistence check (submit window vs ingest summary)
    resolve_appid.py        ← APPID derivation helper (project info get)
  README.md / RUNBOOK.md    ← how to run, the four gates, persistence verification
  .local/target.env.example ← destination template (no real secrets)
  .gitignore                ← inbox/ runs/ .local/target.env
  inbox/  runs/             ← daily input / per-run outputs
```

A shareable archive is written next to the package root: `<parent>/ae-data-integration-handoff-<fingerprint[:8]>.zip`. The zip carries only this handoff round — the frozen mappings just written, a scoped `index.json` (just this round's entries), and the generic executors/docs — not the accumulated history, which stays in `.ae-cli/data-integration/` for reuse matching.

## Pipeline descriptor

`pipeline.json` declares the three stages and their types. Only `source: local_file` and `sink: restful_sync_json` are implemented today; the `type` fields reserve logbus / datax / mysql for later phases. `bin/run.sh` and `bin/upload.sh` read the descriptor and dispatch each stage by its `type` to `ae-cli data-integration inspect / convert / upload` — they are executors, not a second runtime engine.

## Recorded destination

`pipeline.json` → `sink.params` records `pushurl` and `project_id` when the handoff
was run with those flags. Reuse defaults to that target, but **`bin/upload.sh`
never sends without `--confirm`**, so the operator re-confirms the address and
project on every reuse. Resolution order at upload time:

- endpoint: recorded `pushurl` (+ `/sync_json`), else `AE_ENDPOINT`.
- APPID: `AE_APPID`, else derived via `ae-cli project info get --project-id <id>`
  (see `bin/resolve_appid.py`; set `AE_APPID` when that payload lacks `appid`).
- project id: recorded `project_id`, else `AE_PROJECT_ID`.

`project info get` returns `data.appid` at the top level (verified against the AE
demo host); `bin/resolve_appid.py` reads that exact field and prints it, falling
back to `AE_APPID` when the field is absent or not a non-empty string.

## Project custom layers

For projects that need a hard per-event SQL judge or a multi-round salvage loop
(the reference package's environment-specific workarounds), overlay a custom layer
next to the package instead of editing it — see [custom-layer.md](custom-layer.md).

## Four confirmation gates

The RUNBOOK and the scripts enforce four gates. The first two run automatically; the last two always need human confirmation:

1. **Shape gate** — `bind_mapping.py` compares the new file's column set against `shape.json` and fails fast on a mismatch. A changed shape means the frozen logic was never reviewed for it: re-run the full pipeline.
2. **Transform** — `ae-cli data-integration convert` per mapping; quarantined rows go to `invalid.rows.jsonl`, never silently dropped.
3. **Tracking-plan gate** — `plan_check.py` verifies every produced event/property already exists in `plan.json`; new ones exit 3 and must be merged into the project plan first.
4. **Sink gate** — `upload.sh` is dry-run by default; `--confirm` is the explicit upload decision.

## Structure fingerprint and index

Every handoff records one entry per mapping in `index.json` (`ae-data-integration-index/v1`) keyed by a **structure fingerprint** — a SHA-256 over the table shape: the raw source columns (by name, reconstructed so flatten, exclude, and account-vs-distinct decisions don't move it), the format, and the event model (`mode`). Business logic (`value_mapping`, transforms, `time_format`, `flatten_rules`, `exclude_columns`, the fixed `default_event_name`, and the system-field assignments) is excluded, so re-handing off the same table with new business rules refreshes the existing entry instead of forking a new one.

Reuse matching is its own step — see [references/reuse.md](reuse.md).

## Completion response

After handoff succeeds, state the **absolute zip path**, the package directory, and the one-line way to run the next same-shape file:

```
cd <out-dir> && bin/run.sh <new-file>   # then bin/upload.sh runs/<run-id> --confirm
```

## Safety rules

- Treat the mappings, plans, generated artifacts, the `.ae-cli/data-integration/` directory, and the zip as sensitive.
- Never write APPID, tokens, or raw data values into a handoff package. The package records at most a destination `pushurl` and `project_id`; uploads still require an explicit, confirmed `upload` call, so the operator re-confirms the address and project each time.
- Do not invent a mapping or plan. Handoff only packages what the user already confirmed.
