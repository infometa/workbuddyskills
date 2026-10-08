# engage-activity.activity-data.detail

Query activity delivery trends through the L3 Capability Gateway.

Mapped command:

```bash
ae-cli capability run engage-activity.activity-data.detail --input '<json>'
```

## Input

Required fields:

- `project_id`: project that owns the activity.
- `activity_id`: activity to query.
- `start_time`: inclusive start date in `yyyy-MM-dd` format.
- `end_time`: inclusive end date in `yyyy-MM-dd` format.

Optional fields:

- `time_particle_size`: `T1` (day), `T2` (week), `T3` (month), or `T5` (total). Defaults to `T1`.
- `source`: `activity` or `topic_and_task`. Defaults to `activity`.
- `topic_id_list`: selected topic IDs.
- `task_id_list`: selected standalone task IDs.
- `request_id`: cancelable query ID. A UUID is generated when omitted.

When `source=topic_and_task` and both ID lists are omitted or empty, the capability selects every topic and standalone task in the activity. When either list is provided, only the explicitly selected resources are queried. Selected resources must belong to the activity and project.

## Recent seven-day topic trend

Use an inclusive seven-day range, `T1`, and `topic_and_task`:

```bash
ae-cli capability run engage-activity.activity-data.detail --input \
  '{"project_id":1,"activity_id":"act-1","start_time":"2026-07-25","end_time":"2026-07-31","time_particle_size":"T1","source":"topic_and_task","request_id":"<uuid>"}'
```

The report exposes the existing activity-page indicators:

- `plan`: planned trigger users.
- `actualTrigger`: actual push users.
- `trigger`: successful push users.

It does not expose `view` (actual arrival) or `click`. Use the returned header values instead of treating `trigger` as an actual-arrival metric.

## Output

Successful output contains:

- `data.request_id`: the request ID used by the query.
- `data.result_generate_time`: ISO-8601 generation time.
- `data.data.x`: summary/date axis.
- `data.data.headers`: indicator keys.
- `data.data.total`: activity totals aligned with `headers`.
- `data.data.values`: topic or standalone-task rows aligned with `x` and `headers`.
- `data.data.topic_list`: selected source IDs and names using `topic_id` and `topic_name`.

The first `x`/`total` row is the overall summary. For non-total time grains, subsequent rows are the requested date buckets.

Use `engage-setting.query.cancel` with the same `request_id` to cancel a running query.
