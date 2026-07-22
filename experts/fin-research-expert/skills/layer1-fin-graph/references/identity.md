# Identity Resolution Reference

Read this when the task involves industry/theme names, lycodes, Same Boat sector ids, fin-data basket ids, market/index codes, SW codes, or industry-chain frame ids. This is an 行业/主题身份解析器，不是上市公司证券解析器。

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

### `get_research_identity_coverage`

Use after identity resolution when the workflow must explain which graph, market, Same Boat, basket, or industry-chain targets are actually available. Pass the resolver-returned canonical identity or supported source identifier; preserve returned `coverage_gaps` and do not convert a missing target into an inferred mapping.

## Rules

- 公司问题先由支持该市场的证券/公司解析能力确认名称、市场、交易所和标准代码；不得把行业 canonical identity、图谱节点或 `market_index_code` 当作公司证券身份。
- 同名公司、两地上市或 A/H/美股候选并存时，保留候选并要求用户确认，不能静默选择一个上市地。
- 公司与行业同时出现时，公司证券身份与行业身份必须分别确认；公司 ticker 不得作为 `lycode`/`frame_id`，行业代码也不得作为证券 ticker。
- If resolver returns `ambiguous`, show candidates or ask the caller to pick one; do not silently choose.
- If resolver returns fallback `rfg:<frame_id>`, state that lycode coverage is missing.
- If source names conflict, preserve the warning and tell the user which source ID was used.
- Do not expose physical tables, SQL, raw DB errors, or internal resolver logs.

## Few-Shot

- User: "半导体设备产业链图谱" -> call `resolve_research_identity(query="半导体设备")`, then use returned `rfg_frame_id` with industry-chain graph tools.
- User: "1026011 对应哪些图谱/观点口径" -> call `resolve_research_identity(query="1026011", query_type="lycode")`.
- User: "有哪些半导体相关 canonical 主题" -> call `list_research_identities(keyword="半导体", limit=20)`.
