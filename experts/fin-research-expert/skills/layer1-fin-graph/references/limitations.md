# Limitations And Safety Reference

Read this for source coverage, public-safe projection, empty results, and investment-safety wording.

## Source Boundaries

- fin-graph is read-only graph/research-framework infrastructure. It is not a general SQL or Neo4j query interface.
- Industry-chain graph tools return bounded public-safe projections, not raw `frame_json`, hidden notes, full internal trees, or internal reasoning.
- Industry graph tools expose restricted summaries, public node names, whitelisted briefs, public factor evidence, and public metric values only.
- Industry viewpoints are generated content tied to `index_code`; they do not prove the industry has no other news, reports, or opinions.
- Anomaly tools query existing anomaly results; they do not trigger fresh detection.
- Macro panels read graph nodes currently connected to `get_macro_data`; they are not a complete macro database.

## Empty Results And Gaps

- If resolver has no match, say no stable canonical identity was found under current filters.
- If the industry-chain graph frame is missing, state 产业链图谱 coverage is missing. Do not substitute a broad index, 行业图谱, or example frame.
- If factor metrics are missing, say that factor has no public series in the current graph projection.
- If `list_industry_anomalies` returns empty, only say the current date/filter returned no anomaly records.
- If a tool returns an error code for unavailable source, timeout, overload, or validation, do not call it an empty result.

## Safety

- Do not fabricate mappings, frame nodes, source links, market data, event samples, sample statistics, or historical windows.
- Do not expose physical DB tables, SQL, raw backend errors, API stack traces, tool logs, personal holdings, trade history, or customer account profiles.
- Do not present factor scores, event windows, graph branches, or industry-chain graph data requirements as forecasts, target prices, or buy/sell recommendations.
- Keep final wording descriptive and evidence-based. State source type and coverage gap when important.

## Cross-MCP Use

- Use fin-data for structured prices, rankings, constituents, valuation, and market time series.
- Use doc-search for news, announcements, research reports, event backtests, document bodies, and source links.
- Use Same Boat for internal 投研 content, analysts, market news analysis, market quote analysis, and sector viewpoints.
- Use resolver output as the ID bridge; do not pass one MCP's source-specific ID to another MCP without a resolver-returned target field.
