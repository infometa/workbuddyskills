# Industry Chain Graph Reference

Read this for 产业链图谱 / 研究框架图谱 overview, bounded tree projection, node search, or industry-chain research maps.

For source gaps and public-safe wording, also read `references/limitations.md`.

## Tools

### `get_research_frame_overview`

Use for industry-chain graph frame metadata, root title, top-level outline, and coverage gaps.

Inputs:
- one of `identity`, `lycode`, `frame_id`, `topic`
- `include_identity`: default true
- `outline_limit`: 1-50

Prefer resolver-returned `canonical_id` or `rfg_frame_id`. Missing industry-chain graph coverage must remain a structured gap; do not substitute an industry graph, broad index, or example tree.

### `get_research_frame_tree`

Use for bounded public-safe tree projection.

Inputs:
- one of `identity`, `lycode`, `frame_id`, `topic`
- `max_nodes`: 1-200
- `include_data_leaves`, `include_search_leaves`

Returned nodes are limited to `node_id`, `title`, `node_type`, `level`, `path`, `parent_id`, `children_count`, `summary`, and `source_kind`. Do not expect raw `frame_json`, hidden notes, or internal fields.

### `query_research_frame_nodes`

Use for public node lookup inside a resolved industry-chain graph frame.

Inputs:
- `keyword` required
- one of `identity`, `lycode`, `frame_id`, `topic`
- optional `node_type`: `decision_branch`, `factor`, `data_leaf`, `search_leaf`
- optional `level`
- `limit`: 1-100

Search is over public title/summary/path, not hidden internal notes.

### `get_industry_chain_research_map`

Use for a compact WorkBuddy-ready industry-chain or research-framework map.

Inputs:
- one of `identity`, `lycode`, `frame_id`, `topic`
- `focus`: `overview`, `factors`, `data_requirements`, `all`
- `limit`: 1-80

`data_requirements` 表示后续应核验的数据/检索需求, not observed market facts. Keep `source_review` in downstream source-review sections.

## Rules

- Always preserve `coverage_gaps`.
- Treat `data_leaf` and `search_leaf` as evidence requirements unless another MCP later returns actual data/documents.
- If response status is `IDENTITY_AMBIGUOUS`, choose a candidate only after user/workflow disambiguation.
- If response status is `RESEARCH_FRAME_NOT_FOUND` or `RESEARCH_MAP_NOT_AVAILABLE`, state missing industry-chain graph coverage only.

## Few-Shot

- "半导体设备产业链图谱大纲" -> resolve identity, then `get_research_frame_overview(identity="<canonical_id>")`.
- "资本开支在图谱哪个位置" -> `query_research_frame_nodes(identity="<canonical_id>", keyword="资本开支")`.
- "给我产业链研究框架图" -> `get_industry_chain_research_map(identity="<canonical_id>", focus="all")`.
