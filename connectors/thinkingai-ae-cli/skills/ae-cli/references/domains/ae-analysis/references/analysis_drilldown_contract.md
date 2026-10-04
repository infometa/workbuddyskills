# analysis drilldown contract

This contract controls every follow-up from an analysis result. Read it before composing `drilldown-events`, `drilldown-entities`, or `query create-result-cluster`.

## Hard boundary

Only a synchronous `adhoc run`, `report-data run`, or `dashboard-report-data run` preview can create `query_context_id` and selectable drilldown coordinates. The selectable population is exactly the returned preview, after its `--preview-rows` boundary is applied. If `--preview-rows 10` returns ten rows, only coordinates represented by those ten rows may be selected.

Every query-context or drilldown-context follow-up must also pass the original `--project-id`. Gateway uses it for project authorization, then Common verifies that it matches the project stored by the context ID. Never substitute a different project ID.

Exports never create a query context. A downloaded file, export submit response, or export artifact must never be used to invent or extend drilldown coordinates. To drill into a large result, first run a bounded synchronous preview containing the desired row; do not raise the limit merely to manufacture a complete target catalog.

SQL, `heat_map`, `rank_list`, `revenue`, and scenario models do not support this analysis drilldown contract and therefore do not create a query context. Stop when the primary response has no `query_context_id` or advertised action.

## Select a cell without `target_id`

The primary response contains compact `sources[]`. Select the source that owns the visible result. When more than one source exists, pass the source selector returned there, normally `{"report_id":...}` or `{"chart_id":...}`, to `analysis query-context get`. Never put source IDs inside `coordinate`.

The query-context response contains the selected full `source`. Its `drilldown` object is the only coordinate option catalog for follow-up commands:

- `selection_boundary` must be `synchronous_preview_only`.
- `row_options[]` contains only rows from this preview. Match the user's row by `values`, then copy that option's `coordinate` fragment.
- `column_options[]` contains only drillable result columns. Match the requested visible column by `label`/`column_index`, then copy its `coordinate` fragment.
- `metric_options[]` describes the analysis angle and allowed `actions`. For event analysis, select the metric by `metric_index`; different metrics in one result may allow different actions.
- `coordinate_fields` is the allowlist for the final coordinate.

Build one coordinate by shallow-merging the selected row, column, and metric coordinate fragments. Identical keys must have identical values. Use the returned snake_case keys and values exactly. Do not send `row_index`, `column_index`, `values`, `label`, `target_id`, display-only dates, raw QP, or any inferred value.

An event-analysis phase-summary row is metric-dependent. The same visible row may therefore appear more than once in `row_options`, with a different `metric_index` in each coordinate fragment. Select the option whose `metric_index` matches the chosen metric column; never remove or replace that field. The backend advertises only these valid combinations:

| Phase calculation | Drillable metric angle |
|---|---|
| `sum` (`PERIOD_TOTAL`) | `EVENT_LIST` only |
| `dist` (`PERIOD_DISTINCT`) | `EVENT_LIST`, `USER_LIST`, or `ENTITY_LIST` |
| averages, integer averages, min/max, weighted averages, and every `intact_*` calculation | none |

This distinction is mathematical: event counts are additive across date buckets, while bucket-level distinct subject counts are not. A `dist` value is recomputed for the complete phase and can therefore identify one event/entity population. `intact_*` values exclude incomplete periods, but the current total drilldown query does not carry that reduced time range.

`time_granularity=T5` is not a phase-summary calculation. Its single returned row is the native full-range metric and remains selectable when the metric advertises `EVENT_LIST`, `USER_LIST`, or `ENTITY_LIST`.

Example:

```json
{
  "source": {"report_id": 1001},
  "coordinate": {
    "group_values": ["Beijing"],
    "date": "2026-07-16",
    "metric_index": 1
  }
}
```

This represents one visible cell: the returned Beijing/date row plus metric column 1. It is not a server-generated ID for every possible cell.

## Choose the action from the analysis angle

Never infer an action from the model name or the numeric cell value. Use the selected `metric_options[].actions` for event analysis and `source.drilldown.actions` for other supported models.

| `analysis_angle` | Allowed next action |
|---|---|
| `EVENT_LIST` | `analysis drilldown-events run|export` only |
| `USER_LIST` | `analysis drilldown-entities run|export`; `analysis query create-result-cluster` |
| `ENTITY_LIST` | The same entity commands; `subject` identifies the analysis entity, which may be a custom entity rather than a user |
| `NONE` | No drilldown or result-cluster action |

`USER_LIST` is one special case of entity drilldown. A custom `ENTITY_LIST` result must be returned and saved as that entity type, not silently converted to users.

## Model coordinate meanings

Use only fragments actually returned in options; the table explains their business meaning and must not be used to synthesize missing choices.

| Model | Coordinate fields and special values |
|---|---|
| `event` | `group_values`, optional machine `date`, `metric_index`, optional `compare_index`, optional `scope=total`. Phase-summary row options already contain the only allowed `metric_index`; T5 total rows use `scope=total` without phase restrictions. The main time range omits `compare_index`; comparison block 1 uses `compare_index=0`. The chosen metric's `analysis_angle` decides events versus entities. |
| `retention` | `group_values`, machine `cohort_date`, `period_index`, `population=retained|lost`, optional `relation`. Only returned cohort rows and population-count period columns are selectable; average/rate/simultaneous-metric rows are not coordinates. |
| `funnel` | `group_values`, optional `date`, one-based `step`, `population=completed|churned`. Only returned step-population columns are selectable; conversion-rate columns are not. |
| `distribution` | `group_values`, machine `date`, optional raw `bucket`, `scope=total|bucket`. Bucket values are backend interval values returned by the contract, not localized column labels. Percentage and comparison rows are not selectable populations. |
| `interval` | `group_values`, optional machine `date`; the aggregate entity-count column returns `scope=total`. A raw `interval_bucket` is valid only when a returned column option explicitly contains it. Never infer a bucket from a displayed duration; descriptive interval statistics are not selectable populations. |
| `prop_analysis` | `group_values`, `population_index`. With configured user/entity populations, the row chooses `population_index`; otherwise it is `0`. |
| `path` | `session_level`, `current_nodes`, optional `next_nodes`, `relation=total|with_next|without_next|with_next_specific`, `current_is_more`, `next_is_more`. Copy the returned node objects; event names and group values are machine values. |
| `attribution` | `attribution_event_id`, `source_group_values`, `target_group_values`. The event ID is returned machine metadata for that row; never derive it from the displayed event name. |

## Entity result and user-event continuation

`analysis drilldown-entities run` returns `subject` and normalized `items[]`.

- For `subject.type=user`, each item contains canonical `user_id`. The response may also return `drilldown_context_id` and a user-event follow-up action. Only then may the Agent call `analysis drilldown-user-events run|export` with that exact context and returned `user_id`.
- For `subject.type=entity`, items contain `entity_value` and attributes. Custom entities do not have user event sequences, so no user-event context or follow-up is valid.
- `subject.column_name` is the authoritative machine identity column used to normalize `entity_value`; never substitute `#user_id` for a custom entity.
- `analysis query create-result-cluster` saves the selected subject as the corresponding entity's result cluster.

The entity export is for complete member data only. It does not create a new context for another drilldown step.

All three drilldown exports are full-download streams, not paging APIs. They accept no limit/offset/page controls and produce `csv.gz`; the platform `model_full_download_limit` remains the safety ceiling. Export artifacts never add selectable coordinates or user-event continuation identities.
