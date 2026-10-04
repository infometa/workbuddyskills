# analysis entity-detail run

Run a bounded entity detail query through the capability gateway.

Read `analysis_data_retrieval.md` before choosing this command. Use `run` only when inline rows are enough; use `entity-detail export` for bounded artifact retrieval up to the detail export row cap.

Use this command for the first small entity detail preview that fits inline. It is not a pagination API; do not loop with offsets to collect more rows.

```bash
ae-cli analysis entity-detail run \
  --project-id <project_id> \
  --definition '{"entity":"user","cohort":{"relation":"and","items":[{"field":{"name":"level","type":"user_property"},"operator":"gte","values":[1]}]},"properties":[{"name":"country","type":"user_property"}],"sort":[{"field":"#user_id","order":"asc"}]}' \
  --preview-rows 100
```

Input:
- `--project-id` numeric project ID.
- `--definition` bounded entity detail JSON object with `entity`, `cohort`, optional `properties`, and optional `sort`.
- `--request-id` optional `cli_<32 lowercase hex>` lifecycle ID.
- `--use-cache` optional boolean.
- `--zone-offset` optional number.
- `--preview-rows` bounds returned business rows. Omit it to use the current cluster synchronous limit; explicit values are checked against that runtime maximum. Agents should normally pass 100.
- `--timeout-seconds` sync timeout, default 120, max 180.

`entity` may be `"user"` for the default user entity or `{ "id": 123 }` in multi-entity projects.

Property and identity rules depend on the entity:

- `entity="user"` resolves to the `#user_id` user entity. `properties` may contain user properties. Every row always contains `#user_id`, `#account_id`, and `#distinct_id` plus the requested properties.
- A custom entity (`{"id":123}` whose entity column is not `#user_id`) returns only its entity value column. Do not provide `properties`; doing so returns `CUSTOM_ENTITY_PROPERTIES_UNSUPPORTED`.

`#user_id` is an internal association key and is normally not meaningful to customers. In user-facing output, Agents should show account ID and visitor ID by default; retain `#user_id` for machine linkage or explicit troubleshooting.

`cohort` is AI-facing for simple entity-set filters and uses the same filter item shape as report/detail filters:

```json
{
  "relation": "and",
  "items": [
    {
      "field": { "name": "level", "type": "user_property" },
      "operator": "gte",
      "values": [1]
    }
  ]
}
```

Supported `cohort.items[].field.type` values are `user_property`, `tag`, and `cluster`. Event behavior cohort conditions are not supported by this command yet; do not invent raw cluster QP for them.

Do not put raw QP at the capability top level. Use `properties` items as strings or `{ "name": "...", "type": "user_property" }`, not `columnName/tableType`.

Do not use this command for full, unknown-size, or later-page detail retrieval. Use `analysis entity-detail export` and inspect its artifact metadata.

Output:

Returns JSON with `items`, exact `total` when available, `returned_rows`, `has_more`, `column_meta`, and `request_id`. `has_more=true` means more rows exist; use `analysis entity-detail export` instead of trying to page or claiming completeness.
