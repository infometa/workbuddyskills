# analysis adhoc run

Run one unified ad-hoc analysis inline query from an AI-facing model definition.

Use this command for AI-facing ad-hoc model analysis. Do not use removed ad-hoc QP builder or schema helper commands.

Typical closed loop: express the business question as an AI-facing definition -> let the compiler resolve metadata -> use `analysis filter-value list` only when an exact stored value remains unknown -> optionally resolve a physical route -> run -> verify `resolved`, warnings, and actual scope -> drill down only through the returned query context.

Routing: read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing this `run` command instead of `adhoc export`.

## Command

```bash
ae-cli analysis adhoc run \
  --project-id <project_id> \
  --model-type <model_type> \
  --definition '<json>' \
  [--resolutions '<confirmed_resolution_json>'] \
  [--request-id cli_<32 lowercase hex>] \
  [--use-cache true|false] \
  [--zone-offset <hours>] \
  [--fields '["列名"]'] \
  [--cluster-query-scope GLOBAL|SLAVE] \
  [--slave-cluster-id <id>] \
  [--preview-rows <n>] \
  [--timeout-seconds <n>]
```

## AI models

Read [`ai_models.md`](ai_models.md) for the single 12-model `model_type` registry, AI-facing `definition`, and SQL dynamic params contract.

For SQL model definitions, do not invent table or column names. If the table reference is known, inspect columns with `analysis-meta datatable columns-get`; if the table is unknown, ask for it instead of guessing.

## Input

- `--project-id`: target project ID.
- `--model-type`: one of the 12 AI-facing model names from [`ai_models.md`](ai_models.md). Do not pass `scenario`, `history_tag`, or `cluster`; tags and cohorts/clusters are separate capabilities.
- `--definition`: model-specific AI-facing definition JSON.
- `--resolutions`: only after user confirmation, pass deterministic bindings keyed by compiler error path. Keep `--definition` unchanged; follow [`../metadata_resolution.md`](../metadata_resolution.md).

Omit `--preview-rows` to use the current model and cluster synchronous row limit. An explicit value must be positive and cannot exceed that runtime limit; agents should normally pass 100 to bound context. `--timeout-seconds` defaults to 120 and has a maximum of 180. The routing rule lives in [`analysis_data_retrieval.md`](analysis_data_retrieval.md).

For `model_type=path`, `preview_rows` follows the analysis UI's graph contract: it limits real nodes per path level, not total nodes across the graph. Nodes beyond the per-level boundary are combined into a `more` node. `result.nodes` retains that synthesized node for graph structure and drilldown coordinates. `returned_rows` counts real business nodes actually returned across all levels; it excludes synthesized `more` nodes and the real nodes folded into them. The count may still exceed `preview_rows` because the boundary applies independently to each level. `has_more=true` means at least one level contains real nodes folded into `more`.

If the requested result exceeds the current runtime synchronous maximum, go directly to `analysis adhoc export`. Do not lower the requested row count, run a partial sync query first, or loop over repeated `run` calls.

Do not use raw QP, `events`, `event_view`, `visual_view`, removed ad-hoc QP builder outputs, or schema helper outputs as `--definition`.

Timezone contract: fixed `--zone-offset` values are integers from `-12` through `14`. Use `--zone-offset 99` for local-time mode, which analyzes timestamps as stored local time without applying a fixed UTC offset conversion; it does not mean UTC+99. Omit the flag to use the project's analysis default.

Cluster routing: omit both routing flags for current-self data. Before `GLOBAL` or `SLAVE`, call `analysis query-cluster list`; `SLAVE` requires exactly one returned physical cluster ID. SQL and attribution do not support `GLOBAL`; distribution with default intervals also rejects `GLOBAL`. These 查询集群 options are unrelated to 用户分群 definitions.

## Output

The response may include:

- `query_context_id`: Redis-backed context for follow-ups from this bounded synchronous preview.
- `sources[].drilldown`: compact allowed-action summary. Detailed coordinate options are read lazily with `analysis query-context get`; `preview_rows` remains the selection boundary.
- `title` / `rows` / `returned_rows` / `has_more`: tabular preview fields. `total` appears only when the backend supplies an exact total. When `has_more` is true, use `adhoc export`; there is no next-page request.
- `result`: direct result for non-tabular models. Path results also return top-level `returned_rows` and `has_more` using the per-level node contract above.
- `request_id`: lifecycle request id.
- `actual_cluster_query_scope`, optional `actual_slave_cluster_id`, and `cluster_query_scope_source`: actual physical data route. Verify these before comparing results or following the query context.

Execution failures are returned as command failures with `request_id`; only the explicit project-no-data condition is a successful empty result. Do not interpret an empty object as evidence that a failed query succeeded.

The execute, `--validate`, and `--dry-run` paths all compile the AI-facing definition. If metadata resolution needs clarification, the command fails with `AI_QP_COMPILE_FAILED`; inspect `meta.compile_status`, `meta.errors[]`, `meta.resolved`, and `meta.warnings`. Each metadata error retains `path`, `slot_kind`, `raw_value`, `allowed_resource_types`, `search_targets`, and `candidates`. Follow [`../metadata_resolution.md`](../metadata_resolution.md); do not guess from display text.

For a complex definition, finish the complete user-requested definition first, validate that exact definition once, and then run the same definition once. Never execute a simplified variant that omits requested filters or groups just to obtain a result. If validation rejects fields, inspect this command's model contract or capability schema once, correct all reported fields together, and revalidate the complete definition.

For a gateway `oneOf` error, focus on the selected `model_type` branch and shared input fields; other model branches are alternatives, not additional requirements. Apply every relevant correction together (for example, both `event_property_name` and string-valued `values` for funnel step filters). Local `INVALID_ANALYSIS_DEFINITION` is a pre-dispatch input failure, not a query failure. Passing this narrow local check is not proof that the full backend schema or query has passed. Follow the failure-evidence rules in `../SKILL.md` and honor the user's retry limit.

Read [`analysis_drilldown_contract.md`](analysis_drilldown_contract.md). Use the context only with an action advertised by the selected source, call `analysis query-context get`, and assemble the coordinate only from its returned option fragments. Do not pass raw QP or infer a coordinate from display text.
