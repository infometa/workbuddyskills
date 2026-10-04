# analysis drilldown-entities export

Stream the complete users or custom entities behind one selected synchronous-preview coordinate as a `csv.gz` artifact.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md) and first validate the coordinate with the corresponding synchronous preview/`drilldown-entities run` path. The export consumes an existing sync-preview context; it never creates a query context or additional drilldown choices.

```bash
ae-cli analysis drilldown-entities export \
  --project-id <project_id> \
  --query-context-id <sync_preview_query_context_id> \
  [--source '{"report_id":1001}'] \
  --coordinate '<same returned coordinate>' \
  [--properties '[{...}]'] \
  [--artifact-format csv] \
  [--timeout-seconds 21600]
```

`--project-id` must match the project stored by `query_context_id`; a mismatch is rejected before export execution.

Property support matches the synchronous preview exactly:

- For the `#user_id` user subject, `--properties` accepts `[{"columnName":"<property_name>","tableType":"user"}]`. The artifact always retains `#user_id`, `#account_id`, and `#distinct_id` plus the requested user properties.
- For a custom entity subject, omit `--properties`; the artifact contains only the entity value column. Supplying properties returns `CUSTOM_ENTITY_PROPERTIES_UNSUPPORTED` instead of silently ignoring them.

`#user_id` is an internal association key. When presenting downloaded user rows to a customer, Agents should display account ID and visitor ID by default rather than using `#user_id` as the only visible identity.

This command does not accept `--limit`, `--offset`, `--page-num`, or `--page-size`. Common executes one full-download query and streams it directly into the artifact; it does not repeatedly call the synchronous preview. “Complete” follows the platform full-download ceiling (`model_full_download_limit`). Inspect `run_id`, then download only after completion.

The file is durable member data, not a new interactive result. Do not use rows in the downloaded artifact to construct another analysis coordinate. User event continuation requires the `drilldown_context_id` and canonical `user_id` returned by a user-subject `drilldown-entities run`, not this export.
