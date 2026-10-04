# Community Data Reporting

Use `ae-cli community data report` to validate, normalize, and submit community records directly to an authorized Iris ingress endpoint. This is an ingestion data-plane command, not an AE analysis-host command.

## Contents

- [Safety and delivery contract](#safety-and-delivery-contract)
- [Endpoint and identifiers](#endpoint-and-identifiers)
- [Input modes](#input-modes)
- [Chat example](#chat-example)
- [Mixed payload example](#mixed-payload-example)
- [Common record rules](#common-record-rules)
- [Schemas](#schemas)
- [Normalization](#normalization)
- [Dry-run and output](#dry-run-and-output)
- [Errors and retry policy](#errors-and-retry-policy)
- [Privacy](#privacy)

## Safety and delivery contract

- The command has `risk: write`. A clear user request to report the data is sufficient; do not add `--yes` or ask for a second confirmation.
- Run a redacted `--dry-run` before the first submission of a dataset.
- A successful response means only that Iris queued the request. It does not prove that every record passed asynchronous processing or reached durable storage.
- Never describe `status: "queued"` as accepted, imported, persisted, or queryable.
- The client makes at most one POST, never follows redirects, and never retries automatically.
- After a timeout, the delivery state is unknown. Check the downstream query or storage side before deciding whether a manual resubmission is safe.

## Endpoint and identifiers

The endpoint precedence is:

1. `--endpoint`
2. `AE_IRIS_SYNC_ENDPOINT`

The endpoint must be a complete `http` or `https` URL whose path ends in `/sync_content`. It must not contain credentials, a query string, or a fragment. Never guess, concatenate, or derive this URL from `--host`; `--host` is unrelated to this command.

Verify all three identifiers with the user or an authoritative system:

| Flag | Iris field | Contract |
|------|------------|----------|
| `--space-id` | `game_id` | Positive signed int64 |
| `--channel-id` | `channel_id` | Positive signed int64 |
| `--source-id` | `source_id` | Positive signed int64 |

The CLI reads these flags as strings to preserve precision, then emits JSON numeric values without quotes. It fixes `source_type` to `#standard` and `version` to `5.0.0`. `--zone-id` defaults to `Asia/Shanghai` and accepts a valid IANA time-zone ID.

The reporting command does not provide a `--game-id` alias. It also does not accept `zone_offset` or top-level `timestamp`/`datetime` request overrides.

## Input modes

Choose exactly one mode:

```text
--data-type <type> --data <inline|path|@path|->
--payload <inline|path|@path|->
```

`--data` accepts one record object or a non-empty record array. `--payload` accepts one segment object or a non-empty segment array. A segment has this shape:

```json
{
  "data_type": "chat",
  "data": [
    { "chat_uuid": "example" }
  ]
}
```

Supported `data_type` values are `post`, `video`, `reply`, `danmu`, `live_room`, `live_interaction`, `chat`, and `interaction`.

Before constructing records, run `ae-cli community data report --help`. The installed command's schema summary is the source of truth for the required fields of every supported `data_type`; use the schema sections below for field limits and normalization behavior.

For either input flag:

- Inline JSON is accepted for non-sensitive examples.
- `@path/to/file.json` is the preferred, unambiguous file form.
- A plain existing path is also accepted.
- `-` reads JSON from stdin.
- JSONL is not supported.

## Chat example

Store records in `chat.json` so message content does not enter shell history:

```json
[
  {
    "chat_uuid": "wecom-chat-0001",
    "user_id": "user-001",
    "user_name": "Example User",
    "chat_room_type": "wecom_group",
    "chat_room_id": "room-001",
    "chat_room": "Example support group",
    "content": "Example redacted message",
    "publish_time": "2026-07-21 09:30:00",
    "extras": {
      "source": "wecom"
    }
  }
]
```

Run the redacted preview, then submit only if the endpoint and IDs are verified:

```bash
ae-cli --dry-run community data report \
  --endpoint https://<iris-ingress>/sync_content \
  --space-id <space-id> \
  --channel-id <channel-id> \
  --source-id <source-id> \
  --data-type chat \
  --data @chat.json

ae-cli community data report \
  --endpoint https://<iris-ingress>/sync_content \
  --space-id <space-id> \
  --channel-id <channel-id> \
  --source-id <source-id> \
  --data-type chat \
  --data @chat.json
```

## Mixed payload example

Use `--payload` when one request contains multiple data types. For example, `mixed.json` can contain a post with a sidecar interaction plus a standalone interaction snapshot:

```json
[
  {
    "data_type": "post",
    "data": [
      {
        "post_uuid": "post-0001",
        "user_id": "author-001",
        "title": "Example post",
        "content": "Example body",
        "publish_time": "2026-07-21 10:00:00",
        "interaction": {
          "collect_time": "2026-07-21 10:05:00",
          "metrics": {
            "views": 100,
            "likes": 8
          }
        }
      }
    ]
  },
  {
    "data_type": "interaction",
    "data": [
      {
        "content_uuid": "post-0001",
        "content_type": 0,
        "collect_time": "2026-07-21 11:00:00",
        "metrics": {
          "views": "125",
          "comments": 3
        }
      }
    ]
  }
]
```

```bash
AE_IRIS_SYNC_ENDPOINT=https://<iris-ingress>/sync_content \
  ae-cli --dry-run community data report \
  --space-id <space-id> --channel-id <channel-id> --source-id <source-id> \
  --payload @mixed.json
```

## Common record rules

- Each record and segment must be a JSON object; arrays must be non-empty.
- Text fields accept only JSON strings. Numbers and booleans are not coerced to text.
- Optional `null` fields are treated as omitted.
- Unknown record fields are preserved.
- Signed int64 inputs may be JSON integer numbers or canonical decimal strings. The wire body contains lossless, unquoted JSON numbers.
- Fields constrained to non-negative int64 reject negative values, fractions, and values above `9223372036854775807`.
- Date/time strings accept only `yyyy-MM-dd HH:mm:ss`, `yyyy-MM-dd HH:mm:ss.SSS`, `yyyy-MM-dd HH:mm`, or `yyyy-MM-dd` where the field permits a date-only value.
- `extras` and `user_extra` accept an object or a JSON-encoded object string. Missing, null, or invalid values normalize to `{}`. Serialized `user_extra` must not exceed 1024 UTF-16 code units.
- `subtitle` accepts an object array or a JSON-encoded object array. Every element must be an object.
- Lengths and truncation use UTF-16 code units, matching Iris/Java string behavior.
- A field with an Iris truncation fallback is truncated and counted in normalization statistics. An overlong field without a fallback is rejected.

## Schemas

Only the key ingestion constraints are listed below. Unknown fields remain on the record after validation.

### `post`

Required: `post_uuid`, a string no longer than 32 UTF-16 code units.

Optional normalized fields include `user_id` (64), `user_name` (80), `title` (200), `content` (65533), `publish_time`, and `extras`. Values in parentheses are truncation limits. An optional `interaction` sidecar requires `collect_time` and a non-empty `metrics` object using the same metric rules as standalone `interaction` with `content_type=0`.

### `video`

Required: `video_uuid`, a string no longer than 32 UTF-16 code units.

Optional normalized fields include `user_id` (64), `user_name` (80), `title` (1000), `description` (65533), `publish_time`, `subtitle`, and `extras`. An optional `interaction` sidecar uses the standalone metric rules with `content_type=1`.

### `reply`

Required: `reply_uuid` (maximum 32), `root_id` (maximum 32), and `root_type`, which must be `post`, `video`, or `live`.

Optional normalized fields include `user_id` (64), `user_name` (80), `content` (65533), `publish_time`, `parent_id` (32), and `extras`.

### `danmu`

Required: `danmu_uuid` (maximum 32), non-negative int64 `timestamp`, `root_id` (maximum 32), and `root_type`, which must be `post`, `video`, or `live`.

Optional normalized fields include `user_id` (64), `user_name` (80), `content` (65533), and `publish_time`.

### `live_room`

Required: non-negative int64 `uuid`, `room_id` (maximum 32), `room_name` (maximum 80), `room_avatar` (maximum 65533), non-negative int64 `fans`, and date/time `timestamp`.

Optional room/stream fields include `room_type` (truncated to 128), `stream_cover` (65533), `stream_title` (80), `stream_status`, `stream_start_time`, `stream_end_time`, and `stream_notice` (maximum 255, rejected if longer). Missing or `2` `stream_status` becomes `0`; only normalized values `0` and `1` are allowed.

The optional metrics `online`, `heat`, `noble_count`, `guardian_count`, `diamond_fan_count`, and `dfans_count` are non-negative int64 values. At most one of the three guardian aliases may be present. If stream details or metrics are present, `stream_start_time` is required and must include a time component; a date-only value is rejected. The derived `stream_id` must not exceed 64 UTF-16 code units, and every derived metric ID (`uuid * 5 + metric_type`) must remain within signed int64 range.

### `live_interaction`

Required: non-negative int64 `uuid`, `activity_type`, `activity_content`, `room_id`, `stream_start_time`, and date/time `timestamp`.

`activity_type` must be `danmu`, `gift`, `superchat`, or `premium`. `activity_content` is truncated to 1024. `room_id` is at most 32. `stream_start_time` must include a time component. Optional normalized fields include `user_id` (80), `user_name` (80), and `user_extra`.

### `chat`

The six required string fields are:

| Field | Limit |
|-------|-------|
| `chat_uuid` | 36 UTF-16 code units; overlong values are truncated |
| `user_id` | 80 |
| `chat_room_type` | 16; no enum restriction |
| `chat_room_id` | 80 |
| `content` | 65533 |
| `publish_time` | One supported date/time format |

Optional normalized fields are `user_name`, `chat_room`, `chat_server`, and `chat_server_id` (each 80), plus `extras`.

`chat_uuid` is a required JSON string. If it exceeds 36 UTF-16 code units, the client keeps the first 36 units and reports the change under `chat.chat_uuid` in the normalization statistics; it does not reject the record for length. Supply source identifiers that already fit the limit to avoid truncation changing record identity or collapsing distinct identifiers to the same normalized value.

### `interaction`

Required: `content_uuid` (maximum 32), integer `content_type` from 0 through 7, `collect_time`, and a non-empty `metrics` object.

Every metric value must be a non-negative int64. A single invalid metric rejects the whole record; it is never silently dropped. Metric names must match `content_type`:

| `content_type` | Meaning | Allowed metric names |
|----------------|---------|----------------------|
| `0`, `1` | post, video | `views`, `likes`, `comments`, `shares`, `favorites`, `coins`, `danmaku`, `dislikes` |
| `2`-`6` | live, chat, comment, reply, danmu | `favorites`, `coins`, `danmaku`, `dislikes` |
| `7` | user | `followers`, `total_views`, `total_likes` |

## Normalization

The CLI normalizes the input before dry-run or submission:

- A single record becomes a one-element `data` array; a single segment becomes a one-element `payload` array.
- Fixed request metadata is `source_type: "#standard"` and `version: "5.0.0"`.
- Integer strings become lossless JSON numeric literals.
- Optional `null` properties are removed.
- Fields with Iris truncation fallbacks are truncated by UTF-16 code units.
- Invalid or missing `extras`/`user_extra` becomes `{}`; encoded objects and `subtitle` arrays become native JSON structures.
- Missing or legacy `stream_status: 2` becomes `0`.

The summary counts truncated, defaulted, and integer-converted fields without exposing their original values.

## Dry-run and output

`--dry-run` performs local parsing, schema validation, and normalization, but sends no network request. Its redacted output contains endpoint, data types, segment/record counts, encoded byte count, and normalization statistics. It never prints the business payload.

A successful live submission has these semantics:

```json
{
  "status": "queued",
  "persistence_verified": false,
  "next_step": "After asynchronous processing, verify the submitted record identifiers through an authorized downstream query or storage path before treating this submission as persisted."
}
```

The complete output also reports submission counts and normalization statistics. Treat them as submitted-to-queue counts, not per-record acceptance counts. Iris does not currently return a query URL or trace ID in this response, so the CLI does not invent one; use the submitted identifiers with an authorized downstream query or storage path.

## Errors and retry policy

- Input, schema, file, identifier, and endpoint failures use a `validation` error envelope. Locations identify segment, record, and field but do not echo the invalid business value.
- Iris HTTP 400 errors expose the safe `return_message` when available.
- HTTP 5xx responses, non-JSON responses, missing `return_code`, non-zero `return_code`, redirects, and buffer-full responses use a standard API error envelope. Server stack traces are not echoed.
- The request timeout is 30 seconds. A timeout does not establish whether Iris queued the request.
- Never automate a retry. For timeout or ambiguous transport failure, check downstream state first and ask the user before any deliberate resubmission.

## Privacy

- Prefer `@file` or stdin for chat text, usernames, identifiers, and other sensitive content. Inline JSON can remain in shell history or process listings.
- The reporting client sends only `Content-Type: application/json` and `Accept: application/json`. It does not send AE access tokens, CLI tokens, or custom authorization headers.
- Request and response bodies are excluded from CLI HTTP logs. Logs contain only endpoint, status, and byte counts.
- Dry-run output is redacted by default. Do not paste raw records into reports or error explanations.
- An endpoint URL must not contain embedded credentials, query parameters, or fragments.
