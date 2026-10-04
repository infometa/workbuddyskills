# analysis-meta catalog list

Use only for a structured AI-QP metadata compile failure that requires one aggregate online search across selected resource types.

Do not use it for ordinary asset discovery or when the compiler already returned candidates. Follow [`../metadata_resolution.md`](../metadata_resolution.md).

Online search:

```bash
ae-cli analysis-meta catalog list \
  --project-id <project_id> \
  --queries '["付费事件","支付事件","充值事件"]' \
  --resource-types '["event","metric"]' \
  --limit-per-type 20
```

Capability id: `metadata.catalog.list`.

## Input

Sends `project_id`, `queries`, `resource_types`, and optional `limit_per_type`. Queries are OR matched only inside the selected resource types.

## Output

Both modes return unified rows with:

- `resource_type`: `event`, `metric`, `event_property`, `user_property`, `cluster`, or `tag`
- `resource_key`: canonical server-defined identifier
- `display_name`
- `remark`
- `scope`: `event` or `user` for property rows
- property type fields when applicable

Online rows also contain `matched_query`, `matched_field`, and `match_type`. Results are limited independently per resource type. `has_more=true` and `truncated_resource_types` identify types with additional matches; do not page them in the structured resolution workflow.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--queries` | Online mode | JSON array of 1–20 deduplicated keywords, OR matched. |
| `--resource-types` | Online mode | JSON array containing only `event`, `metric`, `event_property`, `user_property`, `cluster`, or `tag`. |
| `--limit-per-type` | No | Online result limit per selected resource type; default 20, maximum 200. |
Use at most one online search for the complete compiler error array. If every path gets candidates, ask for confirmation. If any path remains empty, use [`catalog_export.md`](catalog_export.md) once.
