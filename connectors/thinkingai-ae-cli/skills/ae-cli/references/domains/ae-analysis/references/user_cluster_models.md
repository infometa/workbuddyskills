# User cluster definition models

This is the canonical `--definition-request` contract for direct user-cluster create/update. Shared operators, properties, time ranges, and filters are defined in [`audience_models.md`](audience_models.md).

Top-level variants:

- condition: `{"type":"condition","conditions":{"relation":"and|or","items":[...]}}`
- SQL: `{"type":"sql","sql":"...","params":[{"name":"partdate","type":"part_date","recent_day":"1-7"}]}`

For `user-cluster update`, `type` must match the existing cluster type. The update command cannot change a cluster between condition and SQL, and it cannot change the cluster's analysis entity.

For SQL clusters, quote Trino special identifiers with double quotes, for example `{"type":"sql","sql":"SELECT \"#user_id\" FROM v_user_1 WHERE vip_level >= 3"}`. This applies to identifiers containing `#`, `$`, `@`, spaces, or punctuation; single quotes are string literals.

If a SQL cluster reads an event table, include a predicate on the quoted `"$part_date"` date-partition column; the backend rejects event-table SQL without it. This does not apply to the user-table example above.

SQL clusters support only `${PartDate:name}` dynamic placeholders. Each placeholder requires a matching `params` item with `type=part_date` and either `recent_day` or `start_time` plus `end_time`. General SQL parameter types (`text`, `number`, `variable`, `time`, and `selector`) are rejected for SQL clusters.
For `recent_day`, `0-7` means 最近7天 and includes today; `1-7` means 过去7天 and excludes today.

Discover tables with `analysis sql-table list --project-id <project_id> --usage tag_cluster`, then inspect columns with the same `--usage tag_cluster`. This table set is server-authorized specifically for SQL tags/clusters and differs from the default analysis SQL set.

Optional `include_filter` and `exclude_filter` use the shared filter-group shape.

## Event node

Required: `type=event`, `event`. Defaults: `operator=eq`, `value=1`, `aggregation=count`.

```json
{
  "type":"event",
  "event":"pay",
  "operator":"gte",
  "value":2,
  "aggregation":"count",
  "property":"amount",
  "time_range":{"mode":"recent","unit":"day","value":7},
  "filters":{"relation":"and","items":[{"field":"platform","operator":"eq","values":["ios"]}]}
}
```

## User-property node

Required: `type=user`, `field`, `operator`. `values`, `time_relative`, and `time_unit` are optional.

```json
{"type":"user","field":"vip_level","operator":"gte","values":[3]}
```

## Tag or cluster membership node

Required: `type=tag|cluster`, `field`. `operator` defaults to `in_cluster`; optional fields are `values`, `cluster_date_policy`, and `specified_cluster_date`.

```json
{"type":"tag","field":"user_level","operator":"eq","values":["vip"]}
{"type":"cluster","field":"payer_users","operator":"in_cluster"}
```

## Compound node

`group` is another `{relation,items}` condition group.

```json
{"type":"compound","group":{"relation":"or","items":[{"type":"user","field":"country","operator":"eq","values":["US"]},{"type":"cluster","field":"payer_users","operator":"in_cluster"}]}}
```

## Behavior-sequence node

Required: `type=behavior_sequence`, `completed`, `steps`. Each step requires `event`; optional step fields are `completed`, `filters`, `relative_to_first`, and `window`. The sequence also accepts `time_range` and `window`.

```json
{
  "type":"behavior_sequence",
  "completed":true,
  "steps":[{"event":"view_item","completed":true},{"event":"pay","completed":true,"window":{"value":7,"unit":"day"}}],
  "time_range":{"mode":"recent","unit":"day","value":30},
  "window":{"value":7,"unit":"day"}
}
```

## Complete condition request

```json
{
  "type":"condition",
  "conditions":{"relation":"and","items":[
    {"type":"event","event":"pay","operator":"gte","value":2,"aggregation":"count","time_range":{"mode":"recent","unit":"day","value":7}},
    {"type":"user","field":"country","operator":"eq","values":["US"]}
  ]}
}
```
