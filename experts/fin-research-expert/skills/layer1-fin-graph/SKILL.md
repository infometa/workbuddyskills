---
name: layer1-fin-graph
description: "Use when you need industry/theme identity resolution, industry graph nodes/public factors, industry-chain graph overview/tree/node/map access, industry viewpoints, anomalies, crowding, or macro graph panels from the Fin Graph source namespace."
---

# Fin Graph

Use this skill for read-only industry/theme graph and research-framework queries.

Do not use it for raw SQL, private research notes, personal holdings, trade history, direct recommendations, or price forecasts.

## Runtime Binding

This skill defines the Fin Graph logical source contract; it does not declare a separate user-visible MCP connection.

- In WorkBuddy, call Fin Graph tools through the single `tongzhou-fin-research` Connector. Runtime tool names use `fin_graph__<tool>`, for example `fin_graph__resolve_research_identity`.
- In Codex and retained legacy clients, the same canonical tool may appear as a bare name or a client-qualified server/tool name. Match the canonical tool suffix and keep the Fin Graph source label.
- Do not bypass an available `tongzhou-fin-research` Connector by selecting a similarly named global or deferred graph tool.

## Progressive References

Load only the reference needed for the current question:

- `references/identity.md`: canonical industry/theme identity, lycode, Same Boat sector, fin-data basket, SW, market code, industry-chain frame mapping
- `references/industry-chain-graph.md`: 产业链图谱 / 研究框架图谱 overview, bounded tree, node search, industry-chain research map
- `references/industry-graph.md`: 行业图谱 overview, public node search, public factor framework, factor evidence, metric values
- `references/market-signals.md`: industry indices, viewpoints, crowding, anomalies, anomaly details, macro graph panels
- `references/limitations.md`: source boundaries, missing coverage, public-safe projection, no-fabrication rules

Read this skill's `references/<name>.md` file before filling detailed tool parameters.

For combination queries, read multiple references. Example: "半导体设备行业多空和产业链图谱" needs `references/identity.md`, `references/industry-chain-graph.md`, and often `references/industry-graph.md`.

## Routing

Choose the narrowest tool family first:

The table uses canonical tool suffixes for readability. Under the WorkBuddy Connector, prepend `fin_graph__` when selecting the actual tool.

| User intent | Read reference | Preferred tools |
|---|---|---|
| Resolve industry/theme/source IDs and inspect source coverage | `references/identity.md` | `resolve_research_identity`, `list_research_identities`, `get_research_identity_coverage` |
| 产业链图谱 / 研究框架图谱 overview/tree/node/map | `references/industry-chain-graph.md` | `get_research_frame_overview`, `get_research_frame_tree`, `query_research_frame_nodes`, `get_industry_chain_research_map` |
| 行业图谱 overview/node brief | `references/industry-graph.md` | `list_supported_subjects`, `get_graph_overview`, `get_industry_graph`, `query_graph_nodes`, `get_graph_node_brief` |
| Public factors and evidence | `references/industry-graph.md` | `get_public_factor_framework`, `get_factor_evidence_panel`, `get_factor_metric_values` |
| Industry views/anomalies/crowding | `references/market-signals.md` | `list_industry_indices`, `get_industry_views`, `list_industry_anomalies`, `get_anomaly_detail`, `get_industry_crowding` |
| China/global macro dashboard | `references/market-signals.md` | `get_macro_data` |
| Empty result, coverage gap, sensitive wording | `references/limitations.md` | no retrieval tool by itself |

## Required Rules

- Resolver-before-call guardrail: for cross-source industry/theme work, call `resolve_research_identity` first. Do not pass Same Boat `sector_id`, fin-data `basket_id`, SW code, market code, or industry-chain `frame_id` directly into another source unless the resolver returned that target field.
- Prefer resolver-returned `canonical_id`, `rfg_frame_id`, `graph_subject`, `market_index_code`, `same_boat_market_code`, `resolved_subject`, and `resolved_index_code` over guessed names or remembered examples.
- Keep an internal subject resolution ledger: `user_input`, `resolved_subject`, `resolved_index_code`, `index_type`, `evidence_tool`. Final output should show only user-readable source口径, not internal logs.
- Load the relevant reference before calling detailed tools; do not keep all tool parameter notes in context by default.
- Keep source boundaries visible: 产业链图谱/研究框架图谱 is a bounded source map, 行业图谱 tools are public-safe graph/factor projections, industry views are generated viewpoint content, and Fin Data/Doc Search/Same Boat remain separate logical source namespaces inside the aggregated Connector.
- If no mapping, frame, metric, viewpoint, anomaly, or macro series is returned, state the specific missing coverage. Do not invent mappings, node content, sample statistics, source links, or market data.
- Treat `SOURCE_UNAVAILABLE` and `INDUSTRY_CHAIN_GRAPH_SOURCE_UNAVAILABLE` as source errors, not empty coverage or parameter validation. State only that the relevant graph source is temporarily unavailable; do not claim the tool was not called. After either error, stop dependent identity/frame calls for that source and finish with any independently successful evidence.
- Do not expose physical database tables, SQL, raw frame JSON, hidden notes, backend errors, personal account data, or tool logs.
- Do not say engineering has not solved this / 不要说工程上没有解决. Use resolver/list tools first; if no candidate is returned, say no stable graph theme or industry-index candidate was matched under current filters.
- If a multi-part question needs market data, documents, or Same Boat viewpoints too, finish the graph output and then use the relevant sibling skill/MCP.
- Do not answer "will query / please wait" after tool use. Continue calling the needed tool or provide the completed answer.

## Output Shape

Prefer compact lists or tables. Include:

- resolved identity/source IDs when relevant
- frame/topic/node path when relevant
- metric/date/source family when returned
- coverage gaps and source boundaries when relevant
