---
name: layer3-industry-windvane
description: "Generate the complete 行业多空风向标 user story as one evidence-backed HTML file. Use when the user names a dynamic industry or theme and asks for an industry bull/bear windvane, short/mid/long horizon view, six-factor diagnosis, scenario matrix, or the reviewed WorkBuddy 做同款 page. This Layer 3 workflow authenticates, resolves cross-source identity, orchestrates reusable Layer 2 research modules, handles missing event samples, and then delegates HTML rendering."
---

# 行业多空风向标

This is a Layer 3 user-story workflow. It owns the end-to-end task from a named industry or theme to one reviewable HTML artifact. It does not create new MCP data rights.

The final page is AI generated from public information and must expose evidence sources and limitations. It does not constitute investment advice or an individual stock recommendation（AI 生成、基于公开信息、不构成投资建议、不构成个股推荐）.

## Trigger Contract

Use for 行业多空、风向标、六维因子、期限拆解、情景矩阵, or the reviewed industry long/short Playbook page.

Do not use for a normal industry question that only needs a text brief, a named-stock analysis, broad market timing, or personal portfolio advice. Route those to the narrower existing workflow.

## Required Dependencies

- `fin-mcp-gateway` for authentication, grants, quotas, and safe calls.
- `layer1-fin-graph`, `layer1-fin-data`, `layer1-doc-search`, and `layer1-same-boat` for source contracts.
- `layer2-industry-brief` for the reusable industry evidence brief.
- `layer2-evidence-ledger` for evidence strength, conflicts, and gaps.
- `layer2-transmission-chain-builder` or `layer2-research-red-team` only when the retrieved evidence needs chain or falsification analysis.
- `layer2-html-research-playbook` for presentation only.

## Workflow

1. Call the current client's `tongzhou-fin-research` OAuth Connector/MCP directly. If authorization is required or the business call fails authentication, stop and show only the approved OAuth guidance; do not inspect local API-Key state.
2. Dynamically resolve the user's industry or theme with `resolve_research_identity`. Preserve `canonical_id`, selected `source_ids`, and `coverage_gaps`; never hard-code sample industries, historical IDs, or demo parameters.
3. Read all four Layer 1 contracts before business calls. Use only resolver-returned IDs for each source family; do not borrow a Same Boat sector ID for Fin Data or Fin Graph.
4. Run `layer2-industry-brief` to collect market and valuation evidence, news and reports, graph factors and anomalies, Same Boat viewpoints, and source-review URLs within an explicit evidence window.
5. Build an evidence ledger. Separate facts, interpretation, support, pressure, mixed evidence, and unknowns. Use user-facing evidence-strength language, not model decomposition.
6. Use retrieved `3d/5d/7d/20d` event-window statistics only when valid samples exist. Skip `60d` and every other unsupported long window from the horizon analysis, overall judgment, and scenario matrix; mention the gap only in 数据口径. Never substitute a broad index or example number.
7. Read `references/playbook.md`, then read `../layer2-html-research-playbook/SKILL.md` and its `references/common.md`. Render exactly one standalone HTML file.
8. Verify PC-width composition first, then mobile layout. Check Mainland China red-up/green-down semantics, source-review entries, statistics labels, missing-data boundaries, and the four-part disclaimer.

## Output Contract

The page must follow this reading order: topbar, tabs, hero, core signal strip, horizon breakdown, evidence interpretation, six-factor section, scenario and validation matrix, source review, four evidence families, watch points and risks, data methodology.

The first viewport must show the dynamically resolved subject, evidence window, plain-language conclusion, evidence strength, and the next three variables to verify. Tabs must use buttons plus `scrollIntoView`, not hash navigation.

## Failure And Safety Contract

- Missing source families remain visible as coverage gaps; they are not replaced with invented data.
- Data without article-level URLs is labeled by source type only. Do not create fake links.
- Do not expose internal IDs, tool names, raw responses, or failure logs in the HTML.
- Do not promise returns, predict deterministic direction, read holdings or trade history, or provide individual stock recommendations.
