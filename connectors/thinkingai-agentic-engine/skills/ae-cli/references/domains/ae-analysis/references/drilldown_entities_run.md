# analysis drilldown-entities run

Preview users or custom entities behind one selected synchronous-preview cell.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md) first. Call this only when the selected metric/action advertises `drilldown_entities`. Event metrics require `analysis_angle=USER_LIST|ENTITY_LIST`; retention, funnel, distribution, interval, property, path, and attribution results expose their analysis subject in `source.drilldown.subject`.

## Command

```bash
ae-cli analysis drilldown-entities run \
  --project-id <project_id> \
  --query-context-id <sync_preview_query_context_id> \
  [--source '{"report_id":1001}'] \
  --coordinate '<merged returned row/column/metric coordinate>' \
  [--properties '[{...}]'] \
  [--preview-rows 100] \
  [--timeout-seconds 120]
```

`--project-id` must be the project used by the synchronous preview and must match the stored query context. The context, source, and coordinate must all come from that same preview. First call `analysis query-context get`; select a visible row from its `row_options`, a drillable column from `column_options`, and the relevant metric option, then shallow-merge their coordinate fragments. Never send `row_index`, `column_index`, `values`, `label`, `target_id`, raw QP, or a coordinate derived from an export file.

Property support depends on the returned subject:

- `subject.type=user` (`column_name=#user_id`): `--properties` may select additional user properties with `[{"columnName":"<property_name>","tableType":"user"}]`. The named value `user` is required; do not send numeric enum codes. Every row still contains `#user_id`, `#account_id`, and `#distinct_id`.
- `subject.type=entity`: do not pass `--properties`. A custom entity returns only its entity value. Supplying properties is invalid and must return `CUSTOM_ENTITY_PROPERTIES_UNSUPPORTED`; it is never silently ignored.

## Output and next intent

The response contains `subject`, `items`, exact `total` when available, `returned_rows`, and `has_more`.

- `subject.type=user`: items include canonical `user_id`; `attributes` always includes `#user_id`, `#account_id`, and `#distinct_id`, followed by requested user properties. `#user_id` is an internal association key that customers normally do not care about. In user-facing tables or summaries, show account ID and visitor ID by default and keep `#user_id` only for machine linkage or explicit troubleshooting. If `drilldown_context_id` and the user-event follow-up are present, the Agent may ask for one returned user's event sequence with `analysis drilldown-user-events run|export`.
- `subject.type=entity`: items contain `entity_value`; do not call user-event commands because non-user entities have no event sequence.
- When `has_more=true` or complete membership is requested, repeat the same context/source/coordinate with `analysis drilldown-entities export`. Do not page this command.
- Creating a result cluster is a sibling action from the original analysis cell, not from an entity row. Use the original `query_context_id`, source, and coordinate with `analysis query create-result-cluster` only if that action was advertised.
