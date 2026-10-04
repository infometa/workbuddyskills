# Common metric semantic definitions

> Trigger keywords: common metric, shared metric · Capability ids: `engage-setting.common-metric.{list,get,create,update,delete}` · Permission: `opsEditSetting`.

Common metric capabilities expose semantic event/formula definitions. Do not submit or reuse `metric_qp`, `Axxx`, display metadata, formula dependency internals, or property metadata.
Metric definitions and formula dependencies reject unknown fields. Event filter `field` accepts
either a technical-name string or `{"name":"...","type":"event_property"}`.

When metadata reports an event property as `array_row`, express it as an `object_group` filter
with `any_satisfy`, `none_satisfy`, or `all_satisfy`; its nested `conditions.items` may reference
only child properties of that parent. Flat filters on the `array_row` parent are rejected before
the metric is saved.

## Commands

```bash
ae-cli engage-setting common-metric list --project-id <project_id>
ae-cli engage-setting common-metric get --project-id <project_id> --metric-name <name>
ae-cli engage-setting common-metric create --project-id <project_id> --metric-type 1 \
  --metric-name <name> --metric-definition '<json>' \
  --metric-window-num 1 --metric-window-time-unit day --display-name <display_name>
ae-cli engage-setting common-metric update --project-id <project_id> --metric-type 1 \
  --metric-name <name> --metric-definition '<json>' \
  --metric-window-num 1 --metric-window-time-unit day --display-name <display_name>
ae-cli engage-setting common-metric delete --project-id <project_id> --metric-name <name> --yes
```

## Event metric

```json
{
  "type": "event",
  "event": "purchase",
  "aggregation": "sum",
  "property": "amount",
  "filters": {
    "relation": "and",
    "items": [
      {
        "field": "currency",
        "operator": "eq",
        "values": ["USD"]
      }
    ]
  }
}
```

Object-group filter example:

```json
{
  "type": "object_group",
  "field": "equipment_list",
  "operator": "any_satisfy",
  "conditions": {
    "relation": "and",
    "items": [
      {
        "field": "equipment_list.item_level",
        "operator": "gte",
        "values": [10]
      }
    ]
  }
}
```

Supported aggregations include `total_count`, `user_count`, `per_user_count`, `sum`, `avg`, `avg_per_user`, `max`, `min`, `distinct_count`, `median`, `percentile`, `variance`, and `stddev`.

Property aggregations require `property`. `percentile` additionally requires a numeric
`percentile` greater than `0` and at most `100`:

```json
{
  "type": "event",
  "event": "purchase",
  "aggregation": "percentile",
  "property": "amount",
  "percentile": 90
}
```

## Formula metric

```json
{
  "type": "formula",
  "expression": "purchases/refunds",
  "format": "percent",
  "dependencies": [
    {
      "type": "event",
      "key": "purchases",
      "event": "purchase",
      "aggregation": "total_count"
    },
    {
      "type": "event",
      "key": "refunds",
      "event": "refund",
      "aggregation": "total_count"
    }
  ]
}
```

Every dependency requires a non-empty, unique `key`, and every key must be used in
`expression`. Write bare keys only: use `purchases/refunds`, never `purchases.A100/refunds.A100`.
Aggregation codes are derived from each dependency. Formula dependencies follow the same
property and percentile requirements as event metrics.

Resolve every event and property through `ae-cli analysis-meta event list` and the corresponding property metadata before writing. `get` and `list` return `metric_definition`, `metric_definition_status`, and an optional unavailable reason. Raw metric QP is hidden.

`metric_type=1` remains required for setting-page common metrics. Metric windows remain separate from the semantic definition, and their unit must be `minute` / `hour` / `day`.
