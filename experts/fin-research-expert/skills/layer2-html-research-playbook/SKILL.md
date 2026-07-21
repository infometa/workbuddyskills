---
name: layer2-html-research-playbook
description: "Render an already-evidenced public equity research brief into a standalone WorkBuddy-ready HTML artifact. Use as the shared presentation dependency after a Layer 2 or Layer 3 workflow has fixed the research question, evidence, sections, source-review entries, gaps, and disclaimer; use layer3-industry-windvane or layer3-event-interpretation for those complete user stories. This skill does not authenticate, retrieve data, choose a research scenario, or add facts."
---

# HTML Research Renderer

This Layer 2 skill is the shared presentation layer. It turns a completed evidence brief into one standalone HTML file. It does not own the user story or decide which evidence to collect.

Every artifact is AI generated from public information and must preserve evidence, source-review, and missing-data boundaries. It does not constitute investment advice or an individual stock recommendation（AI 生成、基于公开信息、不构成投资建议、不构成个股推荐）.

## Routing Boundary

- 行业多空、风向标、六维因子、期限拆解: use `layer3-industry-windvane`.
- 事件影响、因子归因、产业链传导、历史相似事件: use `layer3-event-interpretation`.
- Other HTML requests may use this renderer only after an approved research workflow has supplied an explicit output contract. Candidate Playbook templates under `playbooks/cases` are review sources, not packaged runtime routes.

## Input Contract

The caller must provide:

- research title, subject identity, evidence window, and plain-language conclusion;
- ordered sections and the facts assigned to each section;
- source families and real source-review URLs when returned;
- evidence gaps, skipped modules, statistical sample boundaries, and disclaimer text.

If any required input is missing, return to the calling research workflow. Do not fill gaps from model memory or common sense.

## Render Workflow

1. Read `references/common.md`.
2. Preserve the caller's facts, units, signs, time windows, source labels, gaps, and conclusion strength exactly.
3. Build one standalone HTML file with inline CSS, no external scripts, stylesheets, images, or fonts, and only necessary inline interaction.
4. Use button tabs with `scrollIntoView`; do not use `href="#section-id"` navigation.
5. Keep real article, announcement, report, and mini-program links as source-review entries. For data without article-level links, show only the source type and never invent a URL.
6. Self-check mobile and PC layout, text overflow, source visibility, data gaps, and the four-part finance disclaimer.

## Output Boundary

- Presentation polish may change layout, hierarchy, color, and readability only. It must not add, remove, or reinterpret research evidence.
- Do not expose `layer1-*`, `layer2-*`, `layer3-*`, MCP tools, backend IDs, raw JSON, API keys, phone numbers, holdings, or trade history.
- Do not show tool failures, timeout messages, permission errors, parameter names, or backend service names.
- Do not output target prices, buy/sell points, position sizing, guaranteed returns, or individual stock recommendations.

## Required Reference

- `references/common.md`: HTML safety, source review, responsive layout, interaction, evidence boundaries, and disclaimer rules.
