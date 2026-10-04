# analysis drilldown-user-events run

Query event sequence details for one user after a user-subject `analysis drilldown-entities run`.

Use this only when `analysis drilldown-entities run` returns `subject.type=user`, a `drilldown_context_id`, and the user-event follow-up action. Custom entities do not have event sequences.

Do not pass raw QP.

## Command

```bash
ae-cli analysis drilldown-user-events run \
  --project-id <project_id> \
  --drilldown-context-id <drilldown_context_id> \
  --user-id <user_id> \
  [--sort-order desc] \
  [--preview-rows 100] \
  [--timeout-seconds 120]
```

## Input

- `--drilldown-context-id`: returned by the same user-subject `analysis drilldown-entities run`.
- `--project-id`: the project used by that drilldown; it must match the project stored by `drilldown_context_id`.
- `--user-id`: canonical `user_id` from one item in that same response. Never substitute `entity_value`, `#distinct_id`, account ID, or another identity field.
- `--properties`: optional exact event-property projection. Omit it to use the default event columns. If present, each item uses backend keys `columnName` and `tableType`, for example `[{"columnName":"<event_property_name>","tableType":"event"}]`. `#user_id`, account ID, visitor ID, event name, and event time remain present; unrelated event properties must not be returned. `#user_id` is an internal association key, so Agents should normally display account ID and visitor ID to customers. Do not pass numeric table-type codes, string-name arrays, or snake_case nested keys.
- `--sort-order`: `asc` or `desc`.
- `--event-name-filter`, `--time-filter`, `--time-filter-before-nums`, `--time-filter-after-nums`: optional event sequence filters.

Do not use raw QP, `query_context_id`, or guessed user IDs for this command.

For a `scope=total` source coordinate, there is no single selected date. Common
preserves the machine date coordinates returned by the source query together
with that query's time granularity, such as daily, weekly, or monthly. Do not
invent `target_dates`, force a daily granularity, or replace the returned
`drilldown_context_id`.

Do not call this command merely because an entity row looks like a user. The explicit subject and follow-up context are the authority.

## Output

The response contains at most `preview_rows` event rows. When `has_more=true`, use `analysis drilldown-user-events export`; do not attempt to fetch another page.
