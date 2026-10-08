# analysis drilldown-user-events export

Export the complete event sequence for one user from a drilldown context. Do not pass raw QP.

## Command

```bash
ae-cli analysis drilldown-user-events export \
  --project-id <project_id> \
  --drilldown-context-id <drilldown_context_id> \
  --user-id <user_id> \
  [--properties '[{"columnName":"<event_property_name>","tableType":"event"}]'] \
  [--sort-order desc] \
  [--artifact-format csv] \
  [--timeout-seconds 21600]
```

`--project-id` must match the project stored by `drilldown_context_id`; a mismatch is rejected before export execution.

The nested backend keys are exactly `columnName` and `tableType`, and the table type is the named value `event`. String-name arrays, numeric enum codes, and snake_case rewrites are invalid. With an explicit projection, the artifact retains `#user_id`, account ID, visitor ID, event name, and event time and appends exactly the requested event properties. `#user_id` is internal; Agents should normally present account ID and visitor ID to customers.

Use the exact `drilldown_context_id` and canonical `user_id` returned by a user-subject `analysis drilldown-entities run`. Do not use a custom entity, an entity export artifact, or a guessed identity. Export does not accept `--limit`, `--offset`, `--page-num`, or `--page-size`; Common builds the same authorized event-sequence query without the synchronous preview boundary and streams one `csv.gz` artifact. The platform full-download ceiling (`model_full_download_limit`) still applies.

For a `scope=total` source coordinate, there is no single selected date. Common
preserves the machine date coordinates returned by the source query together
with that query's time granularity, such as daily, weekly, or monthly. Do not
construct dates outside that context or force a daily granularity.

Inspect the returned `run_id` with `analysis run inspect`, then download the completed artifact with `analysis artifact download`.

Output is an async run/artifact descriptor. The complete event rows exist only in the downloaded artifact; they cannot be used as new analysis coordinates.
