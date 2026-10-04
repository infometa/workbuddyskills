# Shared audience definition primitives

This file contains only the primitives shared by user-cluster and user-tag semantic definitions. Read the domain-specific contract before constructing JSON:

- [`user_cluster_models.md`](user_cluster_models.md) for cluster condition/SQL definitions.
- [`user_tag_models.md`](user_tag_models.md) for tag condition/metric/first-last/SQL definitions.

Use semantic snake_case only. Never send compiler or UI fields such as `filts`, `conditionType`, `eventName`, `uceCalcuSymbol`, `C030`, `columnName`, `ftv`, `tagValue`, or `taSqlVo`.

## Operators

`eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `exists`, `not_exists`, `between`, `contains`, `not_contains`, `is_true`, `is_false`, `regex`, `not_regex`, `in_cluster`, `not_in_cluster`.

## Property reference

A property is either a name or a typed object:

```json
"country"
```

```json
{"name":"country","type":"user_property"}
```

## Time range

Use semantic `mode`, `unit`, and `value` fields. Always pass `unit` with `recent` or `previous`; the supported units are `day`, `week`, `month`, `quarter`, and `year`.

| User intent | `time_range` |
|---|---|
| Today | `{"mode":"recent","unit":"day","value":1}` |
| This week | `{"mode":"recent","unit":"week","value":1}` |
| This month | `{"mode":"recent","unit":"month","value":1}` |
| This quarter | `{"mode":"recent","unit":"quarter","value":1}` |
| This year | `{"mode":"recent","unit":"year","value":1}` |
| Yesterday | `{"mode":"previous","unit":"day","value":1}` |
| Previous month | `{"mode":"previous","unit":"month","value":1}` |
| From a fixed date through today | `{"mode":"start_to_today","start_time":"2026-07-01"}` |
| From a fixed date through yesterday | `{"mode":"start_to_yesterday","start_time":"2026-07-01"}` |

Use `custom` only when both boundaries are fixed:

```json
{"mode":"recent","unit":"day","value":7}
{"mode":"previous","unit":"day","value":30}
{"mode":"custom","start_time":"2026-07-01","end_time":"2026-07-07"}
```

Do not pass backend `recent_day` encodings inside `time_range`; the capability compiles the semantic object to the existing analysis representation.

## Filter group

Groups use `{relation,items}`. Each item has `field`, `operator`, and optional `values`:

```json
{"relation":"and","items":[{"field":"country","operator":"eq","values":["US"]}]}
```

Pass a semantic object directly to `--definition-request`. Create/update validate and compile it in the same operation. Use `--validate` for schema validation or `--dry-run` for a no-write execution preview; there is no separate public definition build command.
