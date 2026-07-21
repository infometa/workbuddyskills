# Connector Contract

## WorkBuddy Role

Tongzhou MCP Gateway is the WorkBuddy Connector for this expert. It exposes approved public financial research capabilities through one governed OAuth boundary.

This skill is not the connector itself. It is the companion instruction layer that teaches the expert how to use the connector safely:

- call the dependency Connector directly instead of running a credential preflight;
- keep OAuth tokens, API Keys, codes, and private data out of chat, logs, commands, and reports;
- route user requests to the narrowest approved workflow;
- call only gateway-backed namespaced tools;
- turn returned evidence into user-facing research outputs.

## Connector Surface

The standard expert declares one dependency in `.codebuddy-plugin/plugin.json`: `tongzhou-fin-research`. The Connector owns one canonical Streamable HTTP MCP server at `/mcp/tongzhou-research` and delegates OAuth discovery, PKCE, callback handling, secure storage, refresh, and reauthorization to the WorkBuddy runtime.

Four service families remain namespaced behind that one connection:

- `fin_data__<tool>`
- `doc_search__<tool>`
- `fin_graph__<tool>`
- `same_boat__<tool>`

They are not four user-visible Connector entries. The Connector package, expert package, logs, and chat output contain no access token, refresh token, API Key, or user code.

The standard expert zip references the approved Connector by dependency name but does not embed the Connector source or root `.mcp.json`. Local unpublished validation installs the Connector separately into WorkBuddy's Connector marketplace. This keeps Expert and Connector review/release boundaries explicit.

Do not conflate this Expert dependency shape with a standalone WorkBuddy Connector marketplace package. A standalone submission uses `connector-meta.json`, `mcp.json`, an icon, and when required a `token-schema.json`; its `mcpServers` block has one HTTPS production server.

## Runtime Rule

The first business tool call is the authentication check. Do not run Shell, npm, Node, `gateway_api.cjs`, a hand-written HTTP client, or a separate `tools/list` preflight in an ordinary WorkBuddy research turn. If authorization is required, let WorkBuddy open the OAuth page, ask the user to approve it, and retry the original Connector call once.

The current package intentionally has no local business bridge. A missing local API Key or `~/.config/fin-mcp-gateway` file says nothing about the protected Connector session.

The Connector transport may be stateless and omit `mcp-session-id`. Header absence is not an authentication or business failure. WorkBuddy owns initialization and transport handling; the expert must not require a session header, run a session workaround, or expose transport diagnostics to the user.

## User-Facing Language

Use business labels with users:

- company research;
- sector move attribution;
- event impact analysis;
- market review;
- report digest;
- Tongzhou research lookup.

Do not surface internal labels such as `layer1-fin-data`, `layer2-stock-brief`, `tools/list`, raw server grants, document IDs, graph node IDs, MCP session IDs, or route fallback details unless the user is explicitly debugging the integration.

## Governance Boundary

Layer 2 workflows do not create new data rights. The authenticated gateway principal's server and tool grants are authoritative. If a workflow requires a tool outside the current grant, state that the current account is not authorized for that capability and stop.

Never bypass the gateway through unrelated globally visible or deferred tools, including `mcp__fin-doc__*`, `mcp__fin-data-query__*`, `mcp__fin-graph__*`, `mcp__same-boat__*`, `search_hot_news`, or similarly named direct tools. Client-qualified tools are valid only when their server is the configured `tongzhou-fin-research` connection.

## Connector Failure Modes

When the Connector fails after native OAuth, it is not available for this turn. The expert must not answer from cached data, prior-turn data, model memory, or unrelated MCP tools.

When a call returns a parameter or scope error, treat it as a routing issue, not as a factual market conclusion. For example, `INVALID_BROAD_TIME_RANGE` and `MISSING_RESEARCH_FILTERS` mean the report search must be narrowed before saying no report sample was found.

If no business tool returned evidence, do not create or claim a Markdown, HTML, PDF, chart, status report, or other research artifact. Do not expose `Gateway`, `MCP session ID`, API-Key status, server/tool names, error codes, or upstream-layer diagnoses. For a non-authentication failure, the complete user-facing result is: `本次数据服务暂时不可用，未生成分析结果，请稍后重试。`
