# Analysis metadata resolution

Enter this workflow through either path:

1. `analysis adhoc run|export`, report create, or report update fails with `AI_QP_COMPILE_FAILED` and its metadata errors contain the structured fields below.
2. Ordinary event, property, metric, cluster, or tag metadata discovery has completed two successful remote miss rounds in the same host, project, authenticated principal, and Agent conversation, and a third remote discovery round would otherwise be needed.

For the structured compiler path, the metadata errors contain:

- `path`
- `slot_kind`
- `raw_value`
- `allowed_resource_types`
- `search_targets`
- `candidates`
- `next_action`

The Common compiler returns every unresolved slot from the same compile attempt. Treat that complete error array as one resolution plan. Do not run the structured path independently for each `path`.

`allowed_resource_types` and `search_targets` are authoritative for their exact paths. Do not add, remove, prioritize, or reinterpret resource types. `search_targets[].constraints` must be applied when filtering local rows.

## One catalog for the conversation

The complete analysis metadata catalog contains these resource types in one JSONL file:

- `event`
- `metric`
- `event_property`
- `user_property`
- `cluster`
- `tag`

Use the current Agent conversation context as the catalog base:

1. If the Agent host exposes a private artifact or workspace directory scoped to the current conversation, use it as `<agent-conversation-root>`.
2. Use:

```text
<agent-conversation-root>/ae-cli/analysis-metadata/
```

Do not assume a product-specific environment variable, Agent implementation, or launcher contract.

If the host has no stable conversation-scoped directory, create one private fallback root once:

```bash
mktemp -d "${TMPDIR:-/tmp}/ae-cli-analysis-metadata.XXXXXX"
```

Retain that absolute path in the current conversation state. Never create a new root per error, command, or turn.

Normalize the AE host to its lowercase URL origin without a trailing slash. Set `host-key` to the first 16 lowercase hex characters of the origin SHA-256. Use:

```text
<session-root>/<host-key>/project-<project_id>/catalog.jsonl
<session-root>/<host-key>/project-<project_id>/catalog.meta.json
```

Create the directory with mode `0700`. Do not put a token, user name, or user ID in its path.

Before reuse, require both files and verify:

- `schema_version=1`
- `resource_type=analysis_metadata`
- `complete=true`
- `host` and `project_id` match the current request
- `principal_fingerprint` is present
- JSONL SHA-256 equals `content_sha256`
- the authenticated principal has not changed during the conversation

If any check fails, discard the cached pair for this workflow and fetch it again. A `.part` file or JSONL without the completed metadata sidecar is never valid.

## Ordinary discovery workflow

1. Keep one miss budget for the current host, project, authenticated principal, and Agent conversation.
2. One ordinary discovery round is one successful remote event, property, metric, cluster, or tag list/search request. Put the current phrase and its useful synonyms in one `--queries` array instead of issuing one request per synonym.
3. A round consumes one miss only when it returns no confirmable candidate. A plausible candidate stops discovery and requires explicit user confirmation; it is not a miss.
4. Project lookup, exact `get`, filter-value lookup, and data queries do not consume this metadata-discovery budget. Validation, permission, network, and server errors are failures, do not consume a miss, and must not trigger the full-catalog fallback.
5. After at most two ordinary miss rounds, do not issue a third resource-specific list/search. The third remote metadata-discovery round must be exactly one aggregate search using every accumulated deduplicated query and the union of applicable resource types:

```bash
ae-cli analysis-meta catalog list \
  --project-id <project_id> \
  --queries '["<all accumulated deduplicated queries>"]' \
  --resource-types '["<union of applicable resource types>"]' \
  --limit-per-type 20
```

6. If the aggregate response contains a confirmable candidate, stop and ask for confirmation. If it remains unresolved or returns `has_more=true` without a candidate, download the complete catalog exactly once:

```bash
ae-cli analysis-meta catalog export \
  --project-id <project_id> \
  --output "<catalog_dir>/catalog.jsonl"
```

7. Search the complete JSONL locally, return only a small candidate subset to model context, and require confirmation before binding. A local no-match is a complete negative result for that snapshot.
8. Once the valid complete catalog exists, use it for every later metadata discovery in the same scope. Do not call online resource-specific metadata list/search commands or `analysis-meta catalog list|export` again. An exact `get` for details not present in the catalog remains outside the discovery budget.

This caps ordinary online metadata discovery at three successful remote rounds before the full-catalog fallback becomes eligible: at most two resource-specific misses followed by one aggregate catalog search. Errors never advance that counter.

## Compile-wide workflow

1. Read the complete compiler error array.
2. Keep existing compiler `candidates` for their exact paths. They require confirmation and no metadata lookup unless the user explicitly rejects every candidate for that path. After an explicit reject-all response, discard that rejected set and treat the path as requiring `next_action=search_candidates`, using its existing `raw_value`, `allowed_resource_types`, and `search_targets`.
3. Collect every empty-candidate path with `next_action=search_candidates`.
4. If at least one such path exists, check the one conversation catalog above.
5. If a valid complete catalog exists, skip every online metadata call and search it locally as described below.
6. If no valid catalog exists:
   - Generate useful synonyms for every empty-candidate path from its `raw_value` and `slot_kind`.
   - Deduplicate the synonyms from all paths into one `queries` array.
   - Take the union of those paths' `allowed_resource_types` into one `resource-types` array. Do not add other types.
   - Invoke exactly one aggregate online search:

```bash
ae-cli analysis-meta catalog list \
  --project-id <project_id> \
  --queries '["<all deduplicated synonyms>"]' \
  --resource-types '["<union of allowed resource types>"]' \
  --limit-per-type 20
```

7. Split the online rows back across paths:
   - Accept a row for a path only when its `resource_type` is allowed by that path.
   - Apply that path's `search_targets[].constraints`.
   - Prefer the server-provided exact matches before contained matches.
   - Deduplicate by `resource_type + resource_key`.
8. If every searched path now has at least one candidate, skip the full catalog and continue to confirmation.
9. If any searched path still has no candidate, download the complete catalog exactly once:

```bash
ae-cli analysis-meta catalog export \
  --project-id <project_id> \
  --output "<catalog_dir>/catalog.jsonl"
```

10. Search the one JSONL locally for every path still without a candidate:
   - Generate useful synonyms from that path's `raw_value` and `slot_kind`.
   - Filter rows by `search_targets[].resource_type`.
   - Apply every target `constraints` field.
   - Prefer exact `resource_key`, then exact `display_name`, then contained display name or remark.
   - Deduplicate by `resource_type + resource_key`.
   - Return only a small candidate subset to model context; never read the full catalog into context.
11. Aggregate candidates for all paths and ask the user to confirm each selected candidate in one interaction.
12. Keep the original definition unchanged. Build one `resolutions` object keyed by compiler path and rerun the original command once with `--resolutions`.

A reject-all response is a state transition, not task cancellation. Run the aggregate online search at most once for the rejected path set, then use the same complete-catalog fallback above if needed. Never repeat candidates the user already rejected. If the complete catalog has no different candidate, ask for an exact canonical name or a changed business definition.

Do not call event, property, metric, cluster, or tag list commands after entering the structured workflow. Do not run `--queries` synonym rounds: the aggregate online search is one call for the whole compile error array, never one call per path or resource type. The unified catalog capability replaces both repeated online searches and per-resource full exports.

Once a valid complete catalog exists for the current host, project, principal, and conversation, never call `analysis-meta catalog list` again in that scope, and never call `analysis-meta catalog export` again either. Search the complete local snapshot instead; a local no-match is a complete negative result for this snapshot.

An online response with `has_more=true` is bounded discovery, not a complete negative result. If any path remains unresolved after that response, use the one complete-catalog fallback instead of paging or broadening online queries. Permission, network, and server errors are failures, not empty search results, and must not trigger the full-catalog fallback.

## Confirmation and deterministic binding

Never use a compiler or local candidate without explicit user confirmation.

For each confirmed path, pass:

```json
{
  "resolutions": {
    "request.metrics[0].event": {
      "raw_value": "付费事件",
      "resource_type": "event",
      "resource_key": "payment"
    }
  }
}
```

The server verifies that:

- the path still exists in the unchanged definition;
- `raw_value` still matches that path;
- `resource_type` is allowed for that path;
- `resource_key` is currently accessible in the project and identity scope.

Handle `RESOLUTION_STALE`, `RESOLUTION_TYPE_NOT_ALLOWED`, and `RESOLUTION_PATH_INVALID` as deterministic validation failures. Do not retry the same resolution unchanged.

If the complete local catalog has no candidate for a path, ask the user for an exact canonical name or a different business definition. Never fabricate an entity.

Permission, network, and server errors are not empty catalogs. Report them and do not publish or reuse a failed catalog.
