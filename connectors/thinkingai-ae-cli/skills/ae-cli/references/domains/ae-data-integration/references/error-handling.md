# Error handling

Failures in the data-integration pipeline split into three classes. Each class has a distinct
response; an agent that mixes them up wastes retries and misleads the user.

| Class | What it is | Response |
| --- | --- | --- |
| Abnormal data | Rows or fields that do not meet UE rules | Quarantine the row or skip the field, report counts, salvage |
| File parsing exception | The source cannot be read as its detected format | Surface the parse error, do not retry by guessing; fix the file or format |
| Program execution exception | The program itself failed (disk, permissions, output dir, mapping mismatch) | Surface the exact error, fix the environment/inputs, re-run |

Every error leaves the CLI as the standard envelope `{ ok, data, error: { type, code, message, hint } }`
(JSON on stdout; progress and warnings on stderr). The `code` is the stable identifier an agent
branches on; `hint` is human-readable guidance.

## Class 1 — Abnormal data

Happens inside `convert`. Two severities:

- **Whole-row quarantine.** Any error on a row — identity, time, event name, record type, or a
  single property (type coercion, size/limit) — drops the entire row. The row is written to
  `invalid.rows.jsonl` with its error codes and counted in `manifest.output.invalid_records`; the
  manifest becomes `blocked`. Row-level codes: `MISSING_USER_ID`, `USER_ID_TOO_LONG`,
  `INVALID_RECORD_TYPE`, `INVALID_TIME`, `TIME_OUT_OF_RANGE`, `INVALID_EVENT_NAME`,
  `INVALID_ZONE_OFFSET`, `PROPERTY_TYPE_CONFLICT`, `PROPERTY_LIMIT_EXCEEDED`.
- **Field skip.** A `#ip` or `#uuid` value that violates its spec drops only that field and keeps
  the row. Counts land in `manifest.output.skipped_fields`; private/LAN IPs are kept but counted in
  `manifest.output.lan_ip_records`. Field-skip codes: `INVALID_IP`, `INVALID_UUID`. Never quarantined.

Responses:

- A blocked manifest is not a failure to retry blindly. Fix the mapping, then re-run `convert
  --salvage-from <invalid.rows.jsonl>` to re-process only the quarantined rows (never re-send the
  rows that already passed). Repeat the salvage loop until no rows fail or the user stops.
- An empty source (zero data rows) blocks with the reason `The source contained no data rows.` —
  a distinct, clearer message than a failed validation run. Do not re-run the same command on the
  same empty file expecting a different result.
- Ragged delimited rows (a CSV/TSV row whose column count differs from the header) are tolerated:
  extra fields are dropped and missing fields are treated as empty, and a stderr warning reports
  how many rows were ragged. A row that becomes missing its identity/time because a field was
  absent is then quarantined normally. Treat the warning as a data-quality signal for the user.

## Class 2 — File parsing exceptions

The source cannot be parsed as its detected format. The agent's job is to report precisely and let
the user decide — never to guess an encoding or structure and retry silently.

| Code | Meaning | What to do |
| --- | --- | --- |
| `LOCAL_DATA_INPUT_NOT_FOUND` | Path is not a readable file | Ask for the correct path |
| `LOCAL_DATA_FILE_TOO_LARGE` | XLS over 1 GB | Convert to XLSX or split the workbook |
| `LOCAL_DATA_INPUT_INVALID` | Generic parse failure (malformed CSV/TSV/JSON/XLS) | Verify encoding and structure, then retry without changing the source |
| `LOCAL_DATA_JSONL_INVALID` | A JSONL line is not valid JSON (`location.record` names the line) | Point at the offending record |
| `LOCAL_DATA_JSON_ROOT_INVALID` | JSON root is not an object or array | Check the file's top-level shape |
| `LOCAL_DATA_XLSX_INVALID` | Workbook metadata missing / no readable sheets / worksheet entry missing | Re-export the workbook (sheet recognition accepts `<sheet>` and namespaced `<x:sheet>` alike, so this is a real metadata gap) |
| `LOCAL_DATA_SET_NOT_FOUND` / `LOCAL_DATA_SET_REQUIRED` | Sheet or JSON Path not found / ambiguous | Ask which `--data-set` to use |

A parse error is never a reason to change the mapping or the tracking plan. Report the code and
hint verbatim, and ask the user to fix the file (re-export, re-encode, or split).

## Class 3 — Program execution exceptions

The program itself failed; the source data is usually fine. These must never be mislabeled as
parse errors: a per-row callback failure (for example a disk that filled up mid-convert) propagates
as itself, not as `LOCAL_DATA_INPUT_INVALID`.

| Code | Meaning | What to do |
| --- | --- | --- |
| `LOCAL_DATA_OUTPUT_NOT_EMPTY` | The output directory must be new or empty | Point convert at a fresh `<run-id>` directory |
| `LOCAL_DATA_SOURCE_CHANGED` / `LOCAL_DATA_SOURCE_FORMAT_CHANGED` | The source no longer matches the mapping fingerprint/format | Re-run inspect and review a new mapping |
| `LOCAL_DATA_MAPPING_INVALID` / `LOCAL_DATA_MAPPING_INVALID_JSON` / `LOCAL_DATA_MAPPING_NOT_FOUND` | The mapping cannot be read or validated | Re-read the mapping reference, fix the mapping file |
| `LOCAL_DATA_SALVAGE_INVALID` / `LOCAL_DATA_SALVAGE_EMPTY` / `LOCAL_DATA_SALVAGE_NO_MATCH` | The salvage file is not a valid quarantine file, is empty, or lists no rows from this source | Point at the correct `invalid.rows.jsonl` from the same source |
| `LOCAL_DATA_TYPE_CONFLICTS_UNRESOLVED` / `LOCAL_DATA_TYPE_RESOLUTIONS_INVALID` | Cross-file column type conflicts need explicit resolutions | Build `--type-resolutions` |
| `LOCAL_DATA_PLAN_INVALID_EVENT_NAME` / `LOCAL_DATA_PLAN_EVENT_NAMES_REQUIRED` / `LOCAL_DATA_PLAN_INVALID_LANG` | Tracking-plan draft inputs are invalid | Fix the event name(s) or `--lang` |
| `LOCAL_DATA_HANDOFF_INDEX_INVALID` / `LOCAL_DATA_HANDOFF_PLAN_NOT_FOUND` / `LOCAL_DATA_HANDOFF_PLAN_INVALID` | Handoff index/plan cannot be read | Point at a valid handoff directory/plan file |
| `LOCAL_DATA_ENDPOINT_INVALID` / `LOCAL_DATA_APPID_INVALID` / `LOCAL_DATA_BATCH_SIZE_INVALID` / `LOCAL_DATA_COMPRESS_INVALID` / `LOCAL_DATA_RESUME_INVALID` / `LOCAL_DATA_RESUME_OUT_OF_RANGE` | Upload arguments are invalid | Fix the flag before uploading |
| `LOCAL_DATA_MANIFEST_INVALID` / `LOCAL_DATA_UE_FILE_INVALID` / `LOCAL_DATA_UE_FILE_NOT_FOUND` / `LOCAL_DATA_UE_FILE_CHANGED` / `LOCAL_DATA_UE_COUNT_MISMATCH` / `LOCAL_DATA_MANIFEST_FILE_MISMATCH` | Upload preconditions fail | Re-check the manifest and UE file pairing |
| `LOCAL_DATA_CLEAN_SUBSET_CONFIRMATION_REQUIRED` | Uploading from a blocked manifest needs a separate clean-subset decision | Confirm the subset explicitly before `--allow-clean-subset` |

Write failures (disk full `ENOSPC`, permission denied `EACCES`) do not hang the command: the
output streams fail with a clear `Failed to write "<path>"` message telling the user to check disk
space and directory permissions. Fix the environment, then re-run into a fresh output directory.

## File-level data-quality severity

The classes above are per row or per field. The user also needs one verdict for the file as a whole,
and its signals arrive scattered across the manifest and stderr. Grade them before reporting so the
same file gets the same verdict no matter who reports it.

| Severity | Signal | Handling |
| --- | --- | --- |
| Critical | Established with the user to be a cumulative snapshot or an aggregate report (see [ue-routing.md](ue-routing.md)); a required identity or time column empty for the whole file | Do not upload. Resolve with the user first |
| High | `manifest.output.invalid_records` is a large share of the row count; inspect reported `leading_title_rows` or `header_signal` and the user has not yet said whether those rows are a title/banner; inspect reported `xlsx_structure.merged_covered_cells` and the user has not yet said whether the merged label belongs on the rows the block covers; `summary_rows` was reported and the user has not yet said whether those rows are totals or real records; `duplicate_keys` was reported and the user has not yet said whether the repeated rows are separate observations | Upload is allowed, but name the item explicitly in the confirmation gate and in the completion response |
| Medium | `manifest.output.skipped_fields`; ragged delimited rows; `manifest.output.flatten_misses`; `manifest.output.unreadable_cells`; `xlsx_structure.hidden_rows` or `hidden_columns` read as data | Report the counts; the gate is unchanged |
| Low | `manifest.output.lan_ip_records` | Report once |

Rules:

- Severity is reported, never silently applied. A Critical finding stops the pipeline and is stated
  as a data finding, not as a program error.
- Grade only what the run actually emitted. Every signal that belongs at High or Critical above now
  has a detector, so grade it from what the run reported — never tell the user the tool checked
  something it did not.
- `unreadable_cells` counts XLSX cells that carried no value the tool may use, grouped by cause:
  `formula_no_cached_value` (the file stores a formula but not the result Excel last computed),
  `error_value` (`#N/A`, `#DIV/0!`, …), `unreadable_object` (an unrecognized cell shape). The cells
  read as missing and their rows are kept, so the record count says nothing about them — a column
  that is empty in AE while the spreadsheet looks full is this. The tool never evaluates a formula
  and never guesses a result; the fix is to recalculate and re-export in Excel, or to export values
  instead of formulas. `inspect` reports the same counts before conversion.
- `xlsx_structure` records worksheet layout the rows themselves cannot carry: `merged_covered_cells`
  counts cells that are empty only because a merged block covers them (Excel shows the value on the
  block's first row), `hidden_rows` and `hidden_columns` name what the worksheet hides. The default
  read changes none of it, so these counts describe what was uploaded: a column mostly missing in AE
  while the spreadsheet looks full is the first of them. `merged_cells_filled` and
  `excluded_hidden_rows` say what the run did about it, which is only ever what the user asked for
  via `--fill-merged-cells` / `--exclude-hidden-rows` (mapping: `fill_merged_cells` /
  `exclude_hidden_rows`). XLSX only — a legacy `.xls` workbook is not scanned.
- `summary_rows` names rows that read as a summary line rather than an observation, by `row` (the
  data-row ordinal) and `signals`: `total_label` (a cell reads as `合计` / `总计` / `小计` / `汇总` / `Total` /
  `Subtotal`) and `column_total` (a number equal to the total of its column's other rows). The rows
  were converted like any other, so this is a finding about what was uploaded: one fabricated event
  whose amount is the whole group's, and a column whose reported `sum` is twice its real total. There
  is no flag that drops a data row, because a row labelled `合计` is sometimes a real record; the fix
  is to remove it from the source file or re-export without it. Any format, `.xls` included.
- `duplicate_keys` names rows the source repeated under the same business key, by `key_columns` (the
  columns compared), `duplicate_groups`, `extra_rows` (surplus records an upload would carry), and
  `groups` with `count`, the data-row `rows`, and a `key_hash` prefix — never the key's own values.
  Nothing was removed: a repeat is sometimes a real pair of records, two order lines in the same
  checkout second, and AE appends accepted events with no way to un-send one, so ask the user whether
  the rows are separate observations; if not, have them remove the rows from the source file. Values
  are compared as written, so a repeat spelled two ways is missed, and `tracking_truncated` means
  distinct keys outran the scan's budget and there may be more. Any format, `.xls` included.
- A large quarantine share has no fixed threshold. State the ratio and the dominant error `code`,
  and let the user judge.

## Cross-cutting rules

- Classify first, act second. Match on `code`, not on message text.
- A parse error is not a data problem; a program error is not a parse error. Do not conflate them
  when reporting back to the user.
- Never retry a parse failure by guessing the encoding, delimiter, or header layout. Show the
  error and ask.
- After any fix, re-run from the start of the step that failed; do not resume a half-written run
  or reuse a partially populated output directory.
