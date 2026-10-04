# analysis drilldown-events export

Stream all raw events behind one selected `EVENT_LIST` coordinate into one `csv.gz` artifact.

Use this only when the selected synchronous preview metric advertises `drilldown_events`. Copy the same `query_context_id`, optional `source`, and semantic `coordinate` used by `analysis drilldown-events run`; never pass raw QP or `target_id`.

```bash
ae-cli analysis drilldown-events export \
  --project-id <project_id> \
  --query-context-id <sync_preview_query_context_id> \
  [--source '{"report_id":1001}'] \
  --coordinate '<same returned coordinate>' \
  [--properties '[{"columnName":"<event_property_name>","tableType":"event"}]'] \
  [--artifact-format csv] \
  [--timeout-seconds 21600]
```

`--project-id` must match the project stored by `query_context_id`; a mismatch is rejected before export execution.

This command does not accept `--limit`, `--offset`, `--page-num`, or `--page-size`. Common executes one full-download query and streams its result directly into the artifact; it does not repeatedly call the synchronous preview. “All” follows the platform full-download ceiling (`model_full_download_limit`), not an unbounded query.

When `--properties` is present, the artifact contains required system event columns plus exactly the requested event properties. The export and synchronous preview use the same projection contract.

Inspect `run_id`, wait for completion, then download the bound artifact. The downloaded rows are durable event detail only; they do not create or enlarge the interactive drilldown coordinate set.
