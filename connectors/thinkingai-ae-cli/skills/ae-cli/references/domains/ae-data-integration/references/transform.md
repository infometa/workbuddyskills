# Transform — column → UE mapping

Precondition: the tracking plan ([tracking-plan.md](tracking-plan.md)) has been generated and confirmed. A field mapping is not a tracking plan; if the plan is missing, return to tracking-plan.md first. The key system fields (steps 1–5 below) were already confirmed during the tracking-plan step (tracking-plan.md step 2); if nothing changed, state the confirmed values once and move to the property set — never skip a confirmation the user has not actually given.

Read [UE mapping](ue-mapping.md) and apply these gates:

- At least one real account/distinct ID source exists, or an explicitly user-approved fixed placeholder (`account_id_value`/`distinct_id_value`) or `random_pool`.
- A real event/profile time source exists and is within the supported window.
- Track data has a verified event column or user-approved default event name.
- Low-confidence or mixed mappings are explicitly reviewed.

Confirm the system fields with the user before touching properties. These are the top-level `#` fields, and users may not understand them, so explain each in plain language before asking; never infer a decision from a column name alone.

1. **`#type` / mode.** Confirm the recommendation's `mode` (`track` / `user_set` / `mixed`). If `record_type_field` is set, confirm each distinct value normalizes to one of the eight record types. Ask whether the data reports events (→ `track`) or modifies user profiles (→ `user_set` or another profile type).
2. **`#account_id` and `#distinct_id` — ask together; at least one is required.** Explain both: `#account_id` identifies logged-in users (database `user_id`, phone, member ID); `#distinct_id` identifies anonymous visitors (device/cookie/visitor ID). Present every `identity_candidates` entry from the inspect result alongside the recommendation's `account_id_field`/`distinct_id_field` picks, and ask which column maps to `#account_id`, which to `#distinct_id`, and whether both apply. A column named `user_id` can be either an anonymous or a login ID — only the user knows. If a required identity column is missing, offer an explicit `account_id_value`/`distinct_id_value` placeholder or `random_pool`; never invent one. `identity_candidates` is name-matched only, so it misses identity columns with arbitrary names (`玩家ID`, `用户账号`, `player_name`); surface any column whose shape is identifier-like (high `unique_ratio`, low `missing_ratio`, a string or numeric key, not a time column) and ask the user what it is. When one file has multiple sheets/data-sets, cross-check identity columns across them before finalizing: a column that appears (or near-matches, e.g. `设备ID` vs `主设备ID`) in more than one sheet likely has the same business meaning, so present a per-sheet `#account_id`/`#distinct_id` view and ask whether the same column maps to the same system field everywhere — a device ID used as `#distinct_id` in the event sheet but left as a differently-named plain property in the profile sheet silently breaks anonymous-user linkage, so surface the mismatch and let the user decide rather than letting it pass silently.
3. **`#time`.** Confirm the time column and the source timezone (an IANA name from the user/project context). Leave `time_format` unset unless auto-detection failed (US/EU ambiguous dates). Also confirm the data's `#zone_offset` — the whole-hour UTC offset AE applies to those times, emitted inside `properties` (not top-level). The property's value is a number, so ask the user in numeric terms ("is the offset 8, i.e. UTC+8?") and set `zone_offset_value` to that integer; when a column carries the offset per row, set `zone_offset_field` instead. The two are mutually exclusive.
4. **`#event_name` (track only).** Confirm the event-name column, or a reviewed `default_event_name` when no column exists.
5. **`#ip` / `#uuid` (optional).** Ask only when the data has an IP- or UUID-like column; map it via `ip_field`/`uuid_field`, otherwise skip. `#ip` is event data only and must be a valid IPv4/IPv6 address (a private/LAN IP is kept but reported — AE cannot geolocate it); `#uuid` must be a standard 36-character UUID. A value that violates the spec is dropped from that row only (`INVALID_IP` / `INVALID_UUID`) — the row itself is kept. The program never auto-generates a `#uuid`.

When an `#event_name`, `#account_id`, or `#distinct_id` column's values do not satisfy AE naming rules (pure Chinese, spaces), do not stop — scan the distinct values, list them to the user, and ask for one AE-name replacement each; record the pairs in `value_mapping` (see [UE mapping](ue-mapping.md)). Event names are lowercased by default; keep an uppercase event name only when the user asks to preserve it — leave a legal uppercase value unmapped so it passes through, or map an illegal value to an uppercase target (e.g. `购买` → `Purchase`); see the casing rules in [UE mapping](ue-mapping.md). A value with no matching key keeps its original text and fails validation, so confirm every distinct value is covered or excluded. The same mechanism applies to a property column via that entry's own `value_mapping` — property names stay lowercase-only, so uppercase property values still need `value_mapping`.

Then confirm the property set with the user before saving the mapping. Present every property as a readable table — one row per property with source column, target AE name, and type — never dump the raw mapping JSON at the user. Whether the rows are event or user properties follows `mode`: `track` → **event properties**, `user_set` (or another profile mode) → **user properties**, `mixed` → the same set applies to both event and user rows.

Walk the table item by item:

1. **Auto-renamed targets.** Recommendation sanitizes column names (camelCase split, illegal chars → `_`, digit-leading → `field_`, nothing recognizable → `field_N`). Show each source → target; ask for a manual name for every `field_N` fallback and rewrite the `target`.
2. **Types.** Confirm each inferred type (`number`/`string`/`boolean`/`datetime`/`list`/`object`/`array_row`). ID-like columns stay `string` even when numeric; `object`/`array_row`/`list` columns carry `transform: 'json'`. A scalar array is `list` (→ AE `array_string`); an object array is `array_row` (→ AE `array_row`). A type is locked on first receipt, so review it before committing. If the user changes a type, warn how many rows would fail coercion — `convert` reports each failing row with its error code, so run it with the tentative mapping and confirm the quarantined count before finalizing.
3. **Exclusions.** Ask which columns to drop and record them as `exclude_columns`.

Before saving, present the complete mapping for a final sign-off on one grouped page — system fields (`#type`/mode, `#account_id`, `#distinct_id`, `#time` + source timezone, `#zone_offset`, `#event_name`, `#ip`/`#uuid`), then the property table (source column → target AE name → type), then excluded columns — and wait for an explicit yes. Never dump the raw mapping JSON at the user.

Save the reviewed `ae-data-integration-mapping/v1` JSON to `.ae-cli/data-integration/mapping.json` (project workspace). Convert into a new output directory:

```bash
ae-cli data-integration convert \
  --input-file '<path>' \
  --mapping '.ae-cli/data-integration/mapping.json' \
  --output-dir '.ae-cli/data-integration/runs/<run-id>'
```

For multiple files, repeat `--input-file` and pass a wildcard mapping plus `--type-resolutions` when inspect reported conflicts:

```bash
ae-cli data-integration convert \
  --input-file '<a.csv>' --input-file '<b.csv>' \
  --mapping '<wildcard-mapping.json>' \
  --type-resolutions '<resolutions.json>' \
  --output-dir '.ae-cli/data-integration/runs/<run-id>'
```

Merging several sources into one run assumes they are mutually exclusive partitions of the same data set. Confirm that with the user before converting — matching headers do not rule out a detail/summary pair or an original/revised pair — and present each source's row count and time coverage range so an overlap is visible. The same applies to `--merge-sheets` (see [source-inspect.md](source-inspect.md)).

The command never modifies the source. Inspect `manifest.json`; summarize valid and quarantined counts and the block reason, and check the conservation equation first: `manifest.output.source_rows` must equal `valid_records + invalid_records` — a mismatch means rows were dropped or duplicated between the source and the output, so report the three numbers to the user and do not upload until it is explained. A salvage run's `source_rows` is only the rows it re-processed, not the whole file. If `manifest.output.skipped_fields` is present, tell the user how many `#ip`/`#uuid` values were invalid and dropped (the rows were otherwise kept); if `manifest.output.lan_ip_records` is present, tell the user that many `#ip` values are private/LAN addresses that AE cannot geolocate. Neither blocks the manifest. If `manifest.output.flatten_misses` is present — or a stderr `Warning: flatten rule "X" did not materialize for N row(s).` fires — a `flatten_rules` path missed some rows: re-check the dot path against the source shape (or confirm the column is legitimately optional); the rows are otherwise kept. A stderr `Warning: … column count different from the header row …` means ragged CSV/TSV rows were tolerated (extra fields dropped, missing fields treated as empty) — surface it as a data-quality note. A blocked manifest whose reason is `The source contained no data rows.` means the file had zero data rows; do not re-run the same command on it. Do not expose rows from `invalid.rows.jsonl` unless the user specifically asks to inspect the local quarantine. For the full failure taxonomy and how to respond, see [error handling](error-handling.md).

## Re-report only the failed rows (salvage loop)

Re-uploading the whole `valid.ue.jsonl` would re-send rows that already succeeded (track events would duplicate, `user_add` would double-count). Instead, re-process only the quarantined rows against the fixed mapping, anchored to the same source:

```bash
ae-cli data-integration convert \
  --input-file '<same-source>' \
  --mapping '<fixed-mapping.json>' \
  --salvage-from '<run-dir>/invalid.rows.jsonl' \
  --output-dir '.ae-cli/data-integration/runs/<run-id>-salvage'
```

This emits a `valid.ue.jsonl` containing only the rows that now pass, plus a new `invalid.rows.jsonl` with whatever still fails. Fixes are rarely one-shot, so repeat: feed each round's `invalid.rows.jsonl` into the next `--salvage-from` until no rows fail or the user stops. Each round's `valid.ue.jsonl` is disjoint from earlier rounds', so upload each round independently (same confirmation and `--allow-clean-subset` gates as a normal upload). `--salvage-from` is single-file only and the source must be the same file that produced the quarantine.
