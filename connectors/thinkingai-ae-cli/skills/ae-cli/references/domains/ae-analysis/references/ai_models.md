# Analysis AI-facing models

This file is the single reference for `model_type` spelling and AI-facing `definition` shape.

## Capability coverage

- `analysis adhoc run/export`: supports the 12 analysis models only.
- `analysis report create/update`: supports the same 12 analysis models plus `tag` for saved tag report data.
- `analysis report-data run/export`, `analysis dashboard-report-data run/export`, and `analysis bi-panel-page-data run/export`: execute existing saved assets. They do not accept `model_type`; use their own command references.

Do not pass raw QP, `events`, `eventView`, `visualView`, frontend DTOs, schema-generated payloads, `scenario`, `history_tag`, or `cluster` as AI-facing `definition` or `model_type`.

## Model type registry

Common analysis models (9):

- `event`: event analysis
- `retention`: retention analysis
- `funnel`: funnel conversion analysis
- `distribution`: distribution analysis
- `attribution`: attribution analysis
- `interval`: interval analysis
- `path`: path analysis
- `prop_analysis`: property analysis
- `sql`: SQL analysis

Scenario analysis models (3):

- `heat_map`: heat map analysis
- `rank_list`: ranking analysis
- `revenue`: revenue analysis

Report write only:

- `tag`: saved tag report data. Use this spelling in CLI.

## Common building blocks

Time range:

```json
{"mode":"previous","unit":"day","value":7}
```

- `mode`: `recent`, `previous`, `custom`, `start_to_today`, or `start_to_yesterday`.
- `recent` includes today/current unit; `previous` excludes today/current unit.
- For `custom`, pass `start_time` and `end_time`.
- For `start_to_today` and `start_to_yesterday`, pass `start_time`; omit `end_time` because the mode determines it.

Chinese natural-language time mapping (mandatory; do not infer a different mode):

| User wording | `time_range` input | Builder QP | Includes today |
|---|---|---|---|
| 最近7天 / 近7天 | `{"mode":"recent","unit":"day","value":7}` | `recentDay=0-7` | 是 |
| 过去7天 / 前7天 / 上7天 | `{"mode":"previous","unit":"day","value":7}` | `recentDay=1-7` | 否 |
| 今天 | `{"mode":"recent","unit":"day","value":1}` | `recentDay=0-1` | 是 |
| 昨天 | `{"mode":"previous","unit":"day","value":1}` | `recentDay=1-1` | 否 |

If the user explicitly says whether today is included, that explicit requirement overrides the phrase mapping. Relative dates are resolved at query time using the effective project/user timezone; do not invent absolute dates.

Field reference:

```json
{"field":{"name":"country","type":"user_property"}}
```

- `type` can be `event_property`, `user_property`, `cluster`, or `tag`.
- Omit `type` only when the field name is unambiguous.
- `prop_analysis` dimensions and filters support `user_property`, `cluster`, and `tag`; they do not support `event_property`.

Filter:

```json
{"field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}
```

- Operators include `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `exists`, `not_exists`, `between`, `contains`, and `not_contains`.
- Omit `values` for `exists` and `not_exists`.
- Use exactly two values for `between`.

Group:

```json
{"field":{"name":"country","type":"user_property"}}
```

Metric aggregation values must use semantic spelling, not internal A-codes. The whitelist is model- and property-type-specific because it mirrors the page controls:

- `event`: without property use `total_count`, `user_count`, or `per_user_count`; numeric properties support `sum`, `avg`, `avg_per_user`, `max`, `min`, `distinct_count`, `median`, `percentile`, `variance`, and `stddev`; string/date/datetime properties support `distinct_count`; boolean properties support `true_count`, `false_count`, `not_empty_count`, `empty_count`, and `distinct_count`.
- `retention` simultaneous metrics: without property use `total_count`, `user_count`, or `per_user_count`; numeric properties support only `sum` and `avg_per_user`; boolean properties support only `true_count`, `false_count`, `not_empty_count`, and `empty_count`.
- `distribution`: without property use `count`, `active_days`, or `active_hours`; numeric properties support `sum`, `avg`, `max`, `min`, `distinct_count`, `median`, `percentile`, `variance`, and `stddev`; string/date/datetime properties support `distinct_count`; boolean properties support `true_count`, `false_count`, `not_empty_count`, `empty_count`, and `distinct_count`.
- `attribution`: use `total_count` without `target_property`, or `sum` with a numeric `target_property`.
- `prop_analysis`: use `user_count` without property; property aggregations follow the event property-type rules except that `percentile` is not supported.
- `heat_map`, `rank_list`, and `revenue`: use the event whitelist except that `percentile` is not supported.

For total event count use `total_count`; `count` belongs only to distribution. Internal `Axxx` codes are persisted page details and are not valid authored AI definitions.

## Model definitions

### `event`

Use for event metrics, trends, grouping, filters, and comparisons.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "time_particle_size": "day",
  "metrics": [
    {"event": "login", "aggregation": "user_count"}
  ],
  "groups": [
    {"field": {"name": "country", "type": "user_property"}}
  ],
  "filters": [
    {"field": {"name": "country", "type": "user_property"}, "operator": "eq", "values": ["US"]}
  ],
  "relation": "and"
}
```

Property aggregation example:

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "metrics": [
    {"event": "purchase", "aggregation": "sum", "property": "amount"}
  ]
}
```

Omit `display_name` by default; apply business-facing labels in the final answer instead. Add this optional field only when the target host's capability schema or a successful validation explicitly supports `display_name` for that command. Support can differ by deployment and command; a saved report supporting it does not prove ad-hoc support. If rejected, remove only the unsupported label, preserving events, aggregations, properties, filters, and formula dependencies.

Formula metric example:

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "metrics": [
    {
      "formula": "revenue / users",
      "dependencies": [
        {"alias": "revenue", "event": "purchase", "aggregation": "sum", "property": "amount"},
        {"alias": "users", "event": "login", "aggregation": "user_count"}
      ]
    }
  ]
}
```

Formula rules:

- Write **bare aliases** only in `formula` (e.g. `"revenue / users"` or `"pay / dau"`).
- **Do not** write `alias.Axxx` (e.g. `"pay.A103"` / `"revenue.A103"`). Aggregation codes come from each dependency's `aggregation`; the builder expands aliases to real event tokens such as `purchase.amount.A103/login.A101`.
- After the builder returns `status=generated`, hard-validate by querying (`analysis adhoc run` / report-data / dashboard-report-data). Do not save a report or dashboard from an unqueried formula QP.

### `retention`

Use for retained/lost users from an initial event to a return event.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "time_particle_size": "day",
  "retention": {
    "initial_event": "register",
    "return_event": "login",
    "stat_type": "retention",
    "unit_num": 1,
    "rtn_rate_or_num": "rate",
    "groups": [
      {"field": {"name": "channel", "type": "user_property"}}
    ]
  }
}
```

Use `stat_type=lost` for lost-user analysis. Use `rtn_rate_or_num=count` when the user asks for user counts instead of rates.

Initial-event and return-event property filters use the retention-specific shape below. Put them inside `retention`; use `event_property_name` instead of a generic `field` object. Do not use top-level `filters`, `retention.filters`, or `initial_event_filters`.

```json
{
  "time_range": {"mode": "custom", "start_time": "2026-08-18 00:00:00", "end_time": "2026-08-18 23:59:59"},
  "time_particle_size": "day",
  "retention": {
    "initial_event": "register",
    "initial_filters": [
      {"event_property_name": "case_id", "operator": "eq", "values": ["retention_test"]}
    ],
    "initial_filter_relation": "and",
    "return_event": "login",
    "return_filters": [
      {"event_property_name": "case_id", "operator": "eq", "values": ["retention_test"]}
    ],
    "return_filter_relation": "and",
    "stat_type": "retention",
    "unit_num": 1,
    "rtn_rate_or_num": "rate",
    "groups": [
      {"field": {"name": "channel", "type": "event_property"}}
    ]
  }
}
```

### `funnel`

Use for ordered conversion steps with a conversion window.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "time_particle_size": "day",
  "funnel": {
    "steps": [
      {"event": "view_product"},
      {"event": "add_to_cart"},
      {"event": "purchase"}
    ],
    "window": {"value": 3, "unit": "day"},
    "groups": [
      {"field": {"name": "channel", "type": "user_property"}}
    ]
  }
}
```

If the user asks to match users across events by a shared event property, set `relation_event_property_name`.

Step-level event-property filters belong inside the matching `funnel.steps[].filters`. Use `event_property_name`, not the common `field` object. `values` is an array of strings, including `"true"` / `"false"` for boolean properties; omit values for existence operators. For example, ordered registration -> login -> first payment:

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 14},
  "time_particle_size": "day",
  "funnel": {
    "steps": [
      {"event": "register"},
      {"event": "login"},
      {"event": "payment", "filters": [
        {"event_property_name": "is_first_pay", "operator": "eq", "values": ["true"]}
      ]}
    ],
    "window": {"value": 7, "unit": "day"}
  }
}
```

Preserve step order, conversion window, and all requested filters when correcting input. Only actual funnel results support step counts and conversion rates; independent event UVs are not an ordered funnel.

### `distribution`

Use for user distribution buckets for an event or property metric.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "distribution_metrics": [
    {
      "event": "purchase",
      "aggregation": "sum",
      "property": "amount",
      "filters": [
        {
          "field": {"name": "vip_users", "type": "cluster"},
          "operator": "in_cluster"
        }
      ],
      "relation": "and",
      "interval_type": "user_defined",
      "quota_interval_arr": [100, 1000, 10000]
    }
  ],
  "groups": [
    {"field": {"name": "country", "type": "user_property"}}
  ]
}
```

Use `interval_type=def` for automatic buckets, `user_defined` for explicit numeric boundaries, and `discrete` to group by raw values.

Distribution filters must be attached to the corresponding `distribution_metrics[].filters`.
Do not use top-level `filters` or `relation` in a distribution definition.
When multiple metrics need the same filter, attach it to each metric explicitly. If the requested filter scope is ambiguous, clarify which metric it applies to before running the analysis.

### `attribution`

Use to attribute target conversions to touchpoint/source events.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 14},
  "attribution": {
    "target_event": "purchase",
    "target_aggregation": "total_count",
    "attribution_events": [
      {"event": "ad_click"},
      {"event": "campaign_view"}
    ],
    "attribution_model": "first",
    "window": {"value": 7, "unit": "day"},
    "direct_conversion": true
  }
}
```

`attribution_model` values: `first`, `last`, or `linear`.
The target aggregation is intentionally narrow: use `total_count` without a property, or `sum` with a numeric `target_property`. Do not use `user_count`.

### `interval`

Use for elapsed-time analysis between an initial event and a return event.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "time_particle_size": "day",
  "interval": {
    "initial_event": "register",
    "return_event": "first_purchase",
    "window": {"value": 7, "unit": "day"},
    "groups": [
      {"field": {"name": "channel", "type": "user_property"}}
    ]
  }
}
```

### `path`

Use for behavior paths before or after a source event.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "filters": [
    {"field": {"name": "account_id", "type": "user_property"}, "operator": "exists"}
  ],
  "relation": "and",
  "path": {
    "source_event": "purchase",
    "included_events": ["view_product", "add_to_cart", "purchase"],
    "session_interval": 30,
    "session_unit": "minute",
    "direction": "forward"
  }
}
```

`direction=forward` asks what users do after `source_event`; `direction=backward` asks what users did before it. Do not send original-QP fields such as `source_type` or `event_names`.

For path analysis, `preview_rows` is a graph-display boundary aligned with the analysis UI: it keeps up to that many real nodes per path level, then combines overflow nodes into `more`. `result.nodes` retains the synthesized `more` node for graph structure and drilldown coordinates. The top-level `returned_rows` counts real business nodes actually returned across all levels; it excludes synthesized `more` nodes and the real nodes folded into them. The count may still exceed `preview_rows` because the boundary applies independently to each level. `has_more=true` means at least one level contains real nodes folded into `more`; a linear multi-level path can return more real nodes than `preview_rows` with `has_more=false`.

Path `filters` are global member filters compiled to the original QP `user_filter`. They support `user_property`, `cluster`, and `tag`, but not `event_property`. Do not move a user filter into the source event's event-property filter.

Path session timeout accepts only these unit/value ranges:

- `second`: `1..999`
- `minute`: `1..999`
- `hour`: `1..24`

Do not use `day`. Express one day as `session_interval=24` with `session_unit=hour`.

Property types come from project metadata. If resolution says a field is an `event_property`, never relabel it as `user_property` just to satisfy the path schema. Remove the unsupported global filter, choose a model that supports event-property filtering, or ask the user to clarify the intended constraint. A familiar name such as `channel` is not universally an event or user property across projects.

For every non-SQL intent model, do not call `list_events` or `list_properties` as an execution prerequisite. The successful response must expose every internally resolved event/property in `resolved`, including `input`, `resolved_name`, `match_type`, and `path`. Use metadata discovery only after a structured `need_clarification` response or an explicit resolution capability error.

### `prop_analysis`

Use for user-property metrics, grouping, filters, and user-crowd comparison.

```json
{
  "prop_analysis": {
    "metric": {"aggregation": "user_count"},
    "groups": [
      {"field": {"name": "country", "type": "user_property"}}
    ],
    "filters": [
      {"field": {"name": "vip_level", "type": "user_property"}, "operator": "gte", "values": ["3"]}
    ],
    "user_crowds": [
      {
        "name": "US users",
        "filters": [
          {"field": {"name": "country", "type": "user_property"}, "operator": "eq", "values": ["US"]}
        ]
      }
    ]
  }
}
```

For property aggregations, pass the user property:

```json
{"prop_analysis":{"metric":{"aggregation":"distinct_count","property":"account_id"}}}
```

### `sql`

Use for SQL analysis. The AI-facing model has only:

- `sql`: required SQL text.
- `params`: optional dynamic parameter values and definitions, required only when SQL contains `${...}` placeholders.

Simple SQL:

```json
{"sql":"SELECT 1 AS value"}
```

Trino special identifiers must use double-quoted identifier delimiters:

```json
{"sql":"SELECT \"#user_id\", \"$part_event\" FROM hive.ta.v_event_1 WHERE \"$part_date\" BETWEEN '2026-07-01' AND '2026-07-07' LIMIT 20"}
```

Reserved words used as identifiers must also be double quoted, for example `SELECT "end" FROM ...`.

For multiline SQL JSON, ensure JSON decoding produces a real line break in the `sql` value. Do not submit a literal `\\n` sequence outside a quoted SQL string value; use a JSON escape that the caller decodes once before invoking the capability.

Event-table queries must include a date-partition predicate on the quoted `"$part_date"` column. The backend rejects SQL against an event table when this predicate is absent. This requirement is specific to event tables; do not invent a `$part_date` condition for a table whose discovered columns do not include it.

Typed condition-fragment placeholder:

```json
{
  "sql": "select * from events where country ${Text:country}",
  "params": [
    {"name": "country", "type": "text", "operator": "eq", "value": "US"}
  ]
}
```

Raw variable placeholder:

```json
{
  "sql": "select * from events where country = ${country}",
  "params": [
    {"name": "country", "type": "variable", "value": "'US'"}
  ]
}
```

Time placeholder:

```json
{
  "sql": "select * from events where ${PartDate:ds}",
  "params": [
    {"name": "ds", "type": "part_date", "recent_day": "1-7", "use_timezone": true}
  ]
}
```

Rules:

- If SQL has no `${...}` placeholder, omit `params`.
- If SQL has placeholders, every placeholder must have one matching item in `params`.
- Raw variables use `${name}`, not `${Variable:name}`. A selector's `value` must equal one of its `options[].value` values. `${PartDate:name}` expands to a complete predicate, so place it directly after `WHERE`/`AND` rather than after a column name.
- A `part_date` parameter must provide either `recent_day` or a complete custom range with both `start_time` and `end_time`; one-sided custom ranges are invalid.
- `use_timezone` is an optional boolean definition field that is only valid for `part_date`. It defaults to `false`. When `true`, that PartDate parameter uses the query's effective timezone selected by `zone_offset` or the current user/project default; when `false`, it follows the non-timezone-aware PartDate path. This is distinct from the command-level `zone_offset`.
- Do not pass SQL-IDE internals such as `sqlVoParams`, `sqlViewParams`, `paramType`, `paramName`, `paramExpress`, `commonFilter`, or `requiredEvents`.
- Delimit any Trino identifier containing `#`, `$`, `@`, spaces, punctuation, or a reserved word with double quotes, for example `"#user_id"`, `"$part_event"`, and `"end"`. Single quotes create string literals, not identifiers. Escape a literal double quote inside an identifier by doubling it. The CLI preserves the submitted SQL and does not rewrite identifiers.
- For an event table, include a date-partition predicate on the discovered `"$part_date"` column, for example `WHERE "$part_date" BETWEEN '2026-07-01' AND '2026-07-07'`. The backend rejects event-table SQL without this condition.
- Do not invent table or column names. If the user already provides a concrete table reference, use `analysis-meta datatable columns-get --project-id <project_id> --table-ref <table_ref>` to inspect columns before writing SQL. If the table itself is unknown, call `analysis sql-table list --project-id <project_id>` when available and select an exact returned `table_ref`; otherwise stop and ask for the table/data source. Ask the user only when multiple authorized tables remain semantically plausible after discovery.
- For a saved dynamic SQL report, put the default values in `analysis report create/update --definition`. Verify the default once with `analysis report-data run` without `--sql-params`, then verify a changed value with one value-only `--sql-params` override.
- `use_timezone` belongs to the saved parameter definition. To change it, update the report `definition`; never pass it through report-data `--sql-params`, which changes values only.
- SQL tags and SQL clusters do not use this general parameter contract. They accept only `${PartDate:name}` with `type=part_date`, and their tables must be discovered with `analysis sql-table list/columns --usage tag_cluster`; see `user_tag_models.md` and `user_cluster_models.md`.

### `heat_map`

Use for two-dimensional heat map analysis based on numeric event coordinate properties.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "heat_map": {
    "hot_event": "click",
    "hot_aggregation": "total_count",
    "x_prop": "screen_x",
    "y_prop": "screen_y",
    "filters": [
      {"field": {"name": "page", "type": "event_property"}, "operator": "eq", "values": ["home"]}
    ]
  }
}
```

For property metrics, set `hot_property` and use a property aggregation such as `sum` or `avg`.

### `rank_list`

Use for ranking users/entities by an event metric.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 7},
  "rank_list": {
    "rank_dimension": {"field": {"name": "#account_id", "type": "user_property"}},
    "rank_event": "purchase",
    "rank_aggregation": "sum",
    "rank_property": "amount",
    "rank_type": "dense_rank",
    "order_by": "DESC"
  }
}
```

`rank_type` values: `rank`, `dense_rank`, or `row_rank`.

### `revenue`

Use for revenue cohort metrics such as LTV, ROI, revenue, and cost.

```json
{
  "time_range": {"mode": "previous", "unit": "day", "value": 30},
  "initial_event": {"event": "register"},
  "pay_event": {"event": "purchase"},
  "revenue_metric": {"event": "purchase", "aggregation": "sum", "property": "amount"},
  "cost_metric": {"event": "ad_cost", "aggregation": "sum", "property": "cost"},
  "observation_days": 14,
  "selected_metrics": ["payAmount", "ltv", "roi"],
  "groups": [
    {"field": {"name": "channel", "type": "user_property"}}
  ]
}
```

`cost_metric` is optional when the user does not ask for cost/ROI.
`selected_metrics` supports `payUsers`, `payAmount`, `cumPayUsers`, `cumPayAmount`, `payRate`, `cumPayRate`, `ltv`, `ltvMultiple`, and `roi`.

### `tag` report write only

Use only with `analysis report create/update`; do not use with `analysis adhoc run/export`.

`tag_name` is the only tag-report name field. Do not send `cluster_name` for a tag report; `cluster_name` belongs only to audience-cluster commands.

```json
{
  "tag": {
    "tag_name": "vip_users",
    "time_range": {"mode": "recent", "unit": "day", "value": 7},
    "time_particle_size": "day"
  }
}
```

Prefer `time_range` for new tag reports. `recent_day`, `start_time`, and `end_time` are only for report readback or precise round-trip updates.
