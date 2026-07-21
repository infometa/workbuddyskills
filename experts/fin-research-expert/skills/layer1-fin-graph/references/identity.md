# Identity Resolution Reference

Read this when the task involves industry/theme names, lycodes, Same Boat sector ids, fin-data basket ids, market/index codes, SW codes, or industry-chain frame ids.

For cross-source work, also read `references/limitations.md`.

## Tools

### `resolve_research_identity`

Use first when an industry/theme will be reused across graph, market, Same Boat, doc, or playbook tools.

Inputs:
- `query`: industry/theme name, `lycode`, `theme:<lycode>`, `industry:sw:l3:<name>`, market code, SW code, Same Boat sector id, or industry-chain frame id
- `query_type`: `auto`, `name`, `lycode`, `canonical_id`, `same_boat_sector_id`, `market_code`, `sw_code`, `rfg_frame_id`, `basket_id`
- `include_candidates`, `include_coverage`
- `limit`: 1-20

Use returned `source_ids` directly:
- `same_boat_sector_id` for Same Boat sector tools
- `same_boat_market_code` or `market_index_code` for industry viewpoint tools when available
- `fin_data_theme_basket_id` / `fin_data_sw_basket_id` for fin-data baskets
- `rfg_frame_id`, `rfg_topic`, `graph_subject` for industry-chain graph / industry graph tools

不要把 Same Boat `sector_id`、fin-data `basket_id`、申万代码、产业链图谱 `frame_id` 互相硬传。

### `list_research_identities`

Use to discover canonical identities and coverage:
- `keyword`
- `identity_type`: `all`, `industry`, `theme`, `concept`, `fallback`
- `primary_system`: `all`, `lycode`, `rfg`, `sw`
- `has_rfg`, `has_same_boat`, `has_market_data`
- `limit`: 1-100

## Rules

- If resolver returns `ambiguous`, show candidates or ask the caller to pick one; do not silently choose.
- If resolver returns fallback `rfg:<frame_id>`, state that lycode coverage is missing.
- If source names conflict, preserve the warning and tell the user which source ID was used.
- Do not expose physical tables, SQL, raw DB errors, or internal resolver logs.

## Few-Shot

- User: "半导体设备产业链图谱" -> call `resolve_research_identity(query="半导体设备")`, then use returned `rfg_frame_id` with industry-chain graph tools.
- User: "1026011 对应哪些图谱/观点口径" -> call `resolve_research_identity(query="1026011", query_type="lycode")`.
- User: "有哪些半导体相关 canonical 主题" -> call `list_research_identities(keyword="半导体", limit=20)`.
