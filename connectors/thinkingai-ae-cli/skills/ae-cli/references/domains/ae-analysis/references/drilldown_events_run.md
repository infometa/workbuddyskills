# analysis drilldown-events run

Preview raw event rows behind one event-analysis metric cell.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md) first. Call this command only when the selected event `metric_option` has `analysis_angle=EVENT_LIST` and includes `drilldown_events` in `actions`. Event totals commonly have this angle; triggered-user/entity counts do not.

## Command

```bash
ae-cli analysis drilldown-events run \
  --project-id <project_id> \
  --query-context-id <sync_preview_query_context_id> \
  [--source '{"report_id":1001}'] \
  --coordinate '{"group_values":["Beijing"],"date":"2026-07-16","metric_index":0}' \
  [--properties '[{...}]'] \
  [--preview-rows 100] \
  [--timeout-seconds 120]
```

`--project-id` must be the project used by that synchronous preview; Common rejects it if it does not match the stored query context. `--query-context-id` must come from the same synchronous preview that returned the selected source and options. `--source` is required only to disambiguate multiple returned sources. Assemble `--coordinate` only by merging the selected returned option fragments. Do not pass `target_id`, raw QP, display-only dates, or values from an export/download.

`--properties` is an optional exact event-property projection. Omit it for default columns; string arrays such as `["#event_time"]` are invalid. Each item uses the backend field names `columnName` and `tableType`, for example `[{"columnName":"<event_property_name>","tableType":"event"}]`. `tableType` uses the documented name `event`, not a numeric enum code. Required system event columns remain present, but unrelated event properties must not be returned.

The response contains at most `preview_rows` event rows from that selected preview cell. `total` is the exact number of matching events, `returned_rows` is the number included in this response, and `has_more=true` means more matching events exist. This command has no paging offset. When complete event detail is required, call `analysis drilldown-events export` once with the same returned context/source/coordinate; that sibling capability uses the backend full-download stream and does not page or enlarge the synchronous selection boundary.
