# UE mapping contract

The mapping version is `ae-data-integration-mapping/v1`.

Required structure:

```json
{
  "version": "ae-data-integration-mapping/v1",
  "source": {
    "sha256": "<source-sha256>",
    "format": "csv",
    "data_set": "$"
  },
  "mode": "track",
  "confidence": "high",
  "account_id_field": "user_id",
  "time": {
    "field": "event_time",
    "format": "auto",
    "source_timezone": "Asia/Shanghai"
  },
  "event_name_field": "event_name",
  "properties": [
    { "source": "amount", "target": "amount", "type": "number" }
  ]
}
```

Use `distinct_id_field` when no account field exists. `mixed` requires `record_type_field`. Track requires `event_name_field` or a reviewed `default_event_name`. `source.format` is one of `csv`, `tsv`, `json`, `jsonl`, `xls`, `xlsx`. For a multi-file template mapping, `source.sha256` may be the wildcard `*`.

## Record types

Every record carries a `#type`. `mode: 'mixed'` resolves the type per row via `record_type_field`; otherwise the mode fixes it (`track` or `user_set`). The `record_type_field` values are normalized case- and underscore-insensitively, with `event`→`track` and `user`/`userset`→`user_set` aliases.

| `#type` | Meaning | Requires `#event_name` |
| --- | --- | :---: |
| `track` | Report an event into the event table | Yes |
| `user_set` | Overwrite user properties (create if missing) | No |
| `user_setOnce` | Initialize a property only when empty | No |
| `user_add` | Increment numeric user properties | No |
| `user_unset` | Clear user property values | No |
| `user_del` | Delete the user from the user table | No |
| `user_append` | Append elements to list properties | No |
| `user_uniq_append` | Append elements with deduplication | No |

## System fields

Top-level `#` fields map from named source columns. The user confirms each mapping; never infer it from a column name alone — a `user_id` column can be either an anonymous or a login ID, and only the user knows which.

| Field | Plain-language meaning | Required |
| --- | --- | :---: |
| `#distinct_id` | Anonymous visitor ID (device/cookie/visitor) — identifies unauthenticated traffic | At least one of `#distinct_id` / `#account_id` |
| `#account_id` | Login/account ID (database `user_id`, phone, member ID) — identifies authenticated users | At least one of `#distinct_id` / `#account_id` |
| `#time` | Event/profile occurrence time; AE bins data by it | Yes |
| `#event_name` | What the user did (`purchase`, `login`) | Only for `track` |
| `#ip` | Client IP; AE resolves geo from it. Event data only | No |
| `#uuid` | Standard 36-character UUID uniquely identifying the record (dedup). Both event and user data | No |

`#zone_offset` is a preset property that tells AE the data's UTC offset (whole hours, -12..14) so `#time` is interpreted correctly. Unlike the fields above it lives **inside `properties`**, not at the top level. Provide it via `zone_offset_value` (a whole-hour integer such as `8` for UTC+8; an IANA name is also accepted and resolved to its offset at conversion time — sub-hour zones round to the nearest whole hour and DST zones reflect the offset then in effect, so historical data crossing a DST boundary should use `zone_offset_field`) or `zone_offset_field` (a source column carrying the offset per row); the two are mutually exclusive. Rows whose `zone_offset_field` value is missing or not an integer in -12..14 are quarantined. `#zone_offset` is event data only — user profile records never carry it.

## Value specifications

Each mapped system field carries a value spec, enforced at both inspect (warnings) and convert (row handling). A row error quarantines the whole row; a field skip drops only that field and keeps the row.

| Field | Value spec | On violation (convert) |
| --- | --- | --- |
| `#account_id` / `#distinct_id` | Non-empty string, at most 128 characters | Row error `MISSING_USER_ID` (absent) / `USER_ID_TOO_LONG` (>128) |
| `#event_name` | `^[A-Za-z][A-Za-z0-9_]{0,49}$` (letter-leading letters/digits/underscore, ≤50 chars; lowercase by default, uppercase kept only on user request) | Row error `INVALID_EVENT_NAME` |
| `#time` | One of the supported formats, within 3 years back / 3 days forward | Row error `INVALID_TIME` / `TIME_OUT_OF_RANGE` |
| `#ip` | Valid IPv4 or IPv6. Event data only | Field skip `INVALID_IP`; a private/LAN IP is kept and reported — AE cannot geolocate it |
| `#zone_offset` | Integer -12..14 (or an IANA name for `zone_offset_value`). Event data only | Row error `INVALID_ZONE_OFFSET` |
| `#uuid` | Standard 36-character UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). Both data kinds | Field skip `INVALID_UUID` |

Event-name case is decided entirely by the mapping, never by the CLI — the CLI performs no case conversion and has no flag for it. The name AE receives is the source `event_name_field` value (or `default_event_name` when there is no event column), optionally replaced by a `value_mapping.event_name` target; `data-integration plan --event-name` passes each name through unchanged. Lowercase is the default: lowercase the name when writing the mapping (a `value_mapping.event_name` entry such as `Purchase` → `purchase`, or a lowercase `default_event_name`). To keep uppercase, skip that lowercasing: leave a legal uppercase source value unmapped so it passes through, write an uppercase `value_mapping.event_name` target only when the source value is not itself a legal name (e.g. `购买` → `Purchase`), or write an uppercase `default_event_name` / `--event-name`.

A field skip is not a row failure: the row is kept with its other fields, and the count is reported in `manifest.output.skipped_fields` so the agent tells the user at the end. `#uuid` is never auto-generated — it comes only from a mapped source column.

Mapping keys: `account_id_field`, `distinct_id_field`, `time.field`, `event_name_field` (or a reviewed `default_event_name`), `ip_field`, `uuid_field`. Inspect surfaces every identity-shaped column in `identity_candidates` (name, `account`/`distinct` kind, unique and missing ratios) so the agent can present all candidates for confirmation. When the required identity column is absent, use an explicit `account_id_value`/`distinct_id_value` placeholder or `random_pool` — a user decision, never invented.

## Output record shape

System fields sit at the top level; every mapped property is nested under `properties`.

```json
{ "#type": "track", "#time": "2026-08-10 10:00:00.000", "#account_id": "u-1", "#event_name": "purchase", "properties": { "amount": 99.9, "channel": "app" } }
```

```json
{ "#type": "user_set", "#time": "2026-08-10 10:00:00.000", "#distinct_id": "d-1", "properties": { "user_level": 5, "user_tag": "vip" } }
```

`track` requires `#event_name`; user-profile types (`user_set`, `user_add`, …) do not.

## Optional overlay fields

All fields below are optional and are explicit user decisions — never invent them.

| Field | Shape | Effect |
| --- | --- | --- |
| `time_format` | `string` (strptime pattern) | Overrides auto-detection for `time.field`; used for ambiguous US/EU dates |
| `value_mapping` | `{ account_id? / distinct_id? / event_name? / record_type?: {original: replacement} }` | Exact-key replacement per system field (business-data keys map to AE-name values). A value with no matching key keeps its original text and fails validation, so confirm every distinct value is covered or excluded |
| `account_id_value` / `distinct_id_value` | `string` | Fixed placeholder identity (≤128 chars). Applies to every row when the corresponding `*_field` is absent; when the field exists, fills only the rows whose column is empty |
| `random_pool` | `{ account_ids?: string[], distinct_ids?: string[] }` | Synthesizes a random identity when the source field is absent |
| `exclude_columns` | `string[]` | Source columns skipped when building properties |
| `flatten_rules` | `{ outColumn: 'dot.path' }` | Nested flatten map. NDJSON/JSON paths are from the record root (`user_info.name`); CSV/TSV/Excel paths are `<column>.<cell-relative path>` into a JSON-encoded object cell (`user_profile.name`) — add the source column to `exclude_columns` when flattening it. `flatten_rules` only materializes the out column in the row; it does **not** emit it — add a `properties` entry with `source` = the out column to actually produce the property. An out column that fails to materialize for some rows (missing path, non-JSON cell, or a path without a `<column>.` prefix) is counted per out-column in `manifest.output.flatten_misses` and named in a convert stderr warning — fix the path or confirm the column is legitimately optional |
| `headers` | `string[]` | User-confirmed column names for a headerless file; presence means the first row is data. Never use inspect's `col_1..col_N` placeholders — infer names from each column's values, confirm them with the user, then write them here |
| `missing_time` | `'now'` | Fill a missing/empty `#time` with the current time, for user-profile rows only (explicit user decision; track rows are never filled) |
| `ip_field` | `string` | Source column emitted as the top-level `#ip` system field (client IP; AE resolves geo). Event data only; a value that is not valid IPv4/IPv6 is dropped from that row, and a private/LAN IP is kept but reported |
| `uuid_field` | `string` | Source column emitted as the top-level `#uuid` system field (standard 36-character UUID, both data kinds). A non-UUID value is dropped from that row |
| `zone_offset_value` | `number` (integer -12..14) or IANA `string` | Emits the fixed `#zone_offset` preset property inside `properties`. An IANA name resolves to its integer UTC offset |
| `zone_offset_field` | `string` | Source column whose per-row integer value (-12..14) is emitted as `#zone_offset`; missing/non-integer rows are quarantined. Mutually exclusive with `zone_offset_value` |
| `event_meta` | `{ <event-name>: { desc?: string, tag?: string } }` | Per-event business description and `event_tag` for the tracking plan, keyed by AE event name. Inferred from the data and user context; the user supplies anything not inferable — never leave them empty |

Each `properties` entry may also carry `value_mapping` (per-property exact-key replacement), `transform` (one of `stringify`, `number`, `boolean`, `json`), `time_format` (only meaningful for `type: 'datetime'`), and `desc` (business description for the tracking plan; inferred, or user-provided when not inferable). Container columns (`object`/`array_row`/`list`) whose values arrive as JSON text — JSON-encoded CSV/TSV/Excel cells, or flattened NDJSON leaves — must set `transform: 'json'` so conversion parses the text back into a native object/array; it is a safe no-op when the value already arrived native.

A `properties` entry whose `target` is dotted (`parent.child`) is a plan-only sub-property declaration: `parent` must name an `object`/`array_row` entry in the same mapping, the child must be scalar or `list`, and the child's `source` must equal the parent's `source` — the nested value lives inside the parent, which conversion emits once and never reads the child's column. A kept whole `object`/`array_row` therefore carries one dotted entry per child alongside the parent entry.

Property types are `string`, `number`, `boolean`, `datetime`, `list`, `object`, and `array_row`. `list` is a scalar array (`["a","b"]`, → AE `array_string`); `object` is a one-to-one object (`{...}`); `array_row` is an object array (`[{...}]`, one-to-many). A mapping expresses an object's/object array's sub-properties as dotted `target`s (`user_info.name`, `orders.sku`); `data-integration plan` maps them one-to-one to `parent.child` plan properties (each child's `display_name`/`desc` default to its leaf segment). In the tracking plan, `object` and `array_row` properties must each have at least one `parent.child` sub-property, and every sub-property must itself be scalar or `array_string` — a nested object/object-array cannot stay nested and must be flattened further to scalar leaves. `list` (→ `array_string`) is a leaf and takes no children. `ae-cli data-integration plan` enforces this locally: a composite property with no children, or a child that is `object`/`array_row`, fails fast with `LOCAL_DATA_PLAN_INVALID_DRAFT` before any upload.

## Time formats

Values with an explicit offset or `Z` are parsed by the JavaScript `Date` constructor (authoritative). Other values are matched against 21 formats; a `time_format` field overrides the match.

| Category | Example | Auto-detected |
| --- | --- | :---: |
| Standard AE | `2024-01-15 10:30:00.123` / `2024-01-15 10:30:00` | Yes |
| ISO 8601 | `2024-01-15T10:30:00` / with `.SSS` / with offset | Yes |
| Unix epoch | `1705314600` (seconds) / `1705314600000` (milliseconds) | Yes |
| Slash-separated | `2024/01/15 10:30:00` / `2024/01/15` | Yes |
| Dot-separated | `2024.01.15 10:30:00` / `2024.01.15` | Yes |
| Compact digits | `20240115103000` / `202401151030` / `20240115` | Yes |
| English month names | `15 Jan 2024 10:30:00` / `January 15 2024 10:30:00` / `Jan 15 2024 10:30:00` | Yes |
| Chinese date | `2024年1月15日` / `2024年1月15日 10:30:00` / `2024年1月15日 10时30分00秒` | Yes |
| US format | `01/15/2024 10:30:00` (MM/DD/YYYY) | No — use `time_format` |
| EU format | `15/01/2024 10:30:00` (DD/MM/YYYY) | No — use `time_format` |

## Data rules

- **Ingestion time window.** The receiver accepts event/profile times from 3 years before to 3 days after the server time; the CLI enforces this range. Client-side reporting has a tighter window (10 days before to 3 days after); historical data beyond the window needs AE support to extend it.
- **Property type locking.** A property's type is locked on first receipt, and properties sharing a name across events are one property — later reports must use the same type. Values whose type mismatches the locked type are dropped silently, so review an inferred type before committing it.
- **Quote stripping.** Paired single or double quotes around a cell value are stripped (`'user_001'` → `user_001`); a single-sided quote is kept as data (SQL exports often quote every value).
- **Column name sanitization.** Recommended mapping auto-names properties: accents are stripped, camelCase is split to snake_case, everything is lowercased, and illegal characters become `_`; a digit-leading name is prefixed `field_`, and a name with nothing recognizable falls back to `field_N`. Review these targets — especially the `field_N` fallbacks — and rename before converting.
- **Object sub-property keys.** Object and list-of-object keys follow the same naming rules as property names (lowercase snake_case, letter-leading, at most 50 chars, no `#`). A key that does not — for example a Chinese key inside a JSON cell such as `{"等级":"金牌"}` — quarantines the whole row, so confirm object keys before converting.

## Review checklist

- Source SHA-256 and data-set ID match the inspection result (or the mapping uses the `*` wildcard for multi-file).
- Identity values remain strings and are at most 128 characters.
- Source timezone is an IANA name derived from user/project context.
- `#zone_offset`, when set, is a whole-hour integer in -12..14 (or an IANA name/column that resolves to one) and is emitted inside `properties`, never at the top level.
- Event names begin with a letter and are at most 50 characters; lowercase is the default, uppercase is kept only when the user asks to preserve it.
- Property names are lowercase snake_case (letter-leading, at most 50 characters).
- Target property names are unique and do not collide with UE system fields.
- Types are one of `string`, `number`, `boolean`, `datetime`, `list`, `object`, or `array_row`.
- Text is at most 2 KB; numbers stay within -9E15..9E15.
- Lists contain at most 500 strings (255 bytes each) or 500 objects.
- Objects contain at most 100 legal sub-properties; nested values follow the same type limits.
- No `object`/`array_row` survives into the tracking plan: AE requires each to have a `parent.child` sub-property (scalar or `array_string` only), and a mapping cannot express one, so nested objects/object-arrays are flattened to scalar leaves first (a kept-whole container fails `data-integration plan` fast).
- A conversion rule does not hide a real type conflict.
- Event/profile times fall within the receiver window: previous 3 years through next 3 days.
- Do not fabricate UUIDs, identities, times, or events; `#ip`/`#uuid` map from named source columns only (`ip_field`/`uuid_field`). `#uuid` is never auto-generated.
- `#uuid` values are standard 36-character UUIDs and `#ip` values are valid IPv4/IPv6; invalid ones are dropped from the row only (`skipped_fields`), never quarantined.
- `#ip` and `#zone_offset` appear on `track` records only; user data carries neither.
- `value_mapping`, `random_pool`, and fixed `account_id_value`/`distinct_id_value` came from an explicit user decision and match the actual distinct values/columns.

`user_set` output for the same identity is ordered by time so receiver application order is deterministic. Conversion applies whole-row quarantine: any error on a row — identity, time, event, record type, or a single property (type coercion, size/limit) — drops the entire row. The row is written to `invalid.rows.jsonl` with its error codes, counted in `manifest.output.invalid_records`, and the manifest is blocked until reviewed. The failed rows are re-reportable without re-sending valid rows: fix the mapping, then run `convert --input-file <same-source> --mapping <fixed-mapping> --salvage-from <invalid.rows.jsonl>`. The salvage run re-processes only the listed row numbers against the same source, emits a `valid.ue.jsonl` containing only the newly fixed rows, and writes a new `invalid.rows.jsonl` with whatever still fails — so the loop repeats (feeding each round's `invalid.rows.jsonl` into the next `--salvage-from`) until no rows fail or the user stops.
