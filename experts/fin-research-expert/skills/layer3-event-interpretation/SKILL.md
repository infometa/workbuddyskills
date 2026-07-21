---
name: layer3-event-interpretation
description: "Generate the complete 事件因子解读 user story as one evidence-backed HTML file. Use when the user asks to turn a policy, announcement, news, company, or industry event into a reviewed event interpretation page with objective factors, attribution, value-chain exposure, historical similar events, market reaction windows, source review, and falsification checks. This Layer 3 workflow authenticates, orchestrates reusable Layer 2 modules, and delegates HTML rendering only after the evidence brief is complete."
---

# 事件因子解读

This is a Layer 3 user-story workflow. It owns the complete event-to-evidence-to-HTML task and uses only the gateway grants already available to the expert.

The final page is AI generated from public information and must expose evidence sources and limitations. It does not constitute investment advice or an individual stock recommendation（AI 生成、基于公开信息、不构成投资建议、不构成个股推荐）.

## Trigger Contract

Use for 事件因子解读、政策或公告影响、产业链传导、事件异动归因、历史相似事件, or the reviewed event interpretation Playbook page.

Do not use for a plain announcement summary, a normal policy brief, a generic HTML restyle, deterministic event prediction, or personal trade advice. Route those to the narrower existing workflow.

## Required Dependencies

- `fin-mcp-gateway` for authentication, grants, quotas, and safe calls.
- The matching Layer 1 contracts for `layer1-doc-search`, `layer1-fin-data`, `layer1-fin-graph`, and `layer1-same-boat` when those source families are used.
- `layer2-policy-event-brief` or `layer2-announcement-brief` for event facts; add `layer2-stock-brief` or `layer2-industry-brief` only when the event subject requires it.
- `layer2-transmission-chain-builder`, `layer2-evidence-ledger`, and `layer2-research-red-team` for mechanism, evidence, and falsification.
- `layer2-html-research-playbook` for presentation only.

## Workflow

1. Complete the current-turn gateway authentication gate. On missing or failed credentials, stop before collecting or interpreting event evidence.
2. Establish the event title, event type, affected subject, evidence window, and at least one public event source. Resolve company or industry identity before market, graph, or Same Boat calls.
3. Run the narrow event brief: use `layer2-announcement-brief` for announcements and filings, otherwise use `layer2-policy-event-brief`. Add stock or industry context only when needed to explain the affected subject.
4. Build the event-to-mechanism-to-value-chain path with `layer2-transmission-chain-builder`. Show business weight only when revenue share, product share, orders, capacity, shipment, margin, or another returned fact supports it; otherwise use a qualitative exposure band with its basis.
5. Build an evidence ledger and red-team check. Separate objective facts, rule-based explanatory scores, interpretation, opposing evidence, and unproven assumptions.
6. Include similar events and `3d/5d/7d/20d` market reactions only when comparable records and valid samples are returned. Treat `60d` as optional; when it has no valid event samples, omit it from the analysis and mention the gap only in data methodology. Never invent returns, win rates, sample counts, or similarity scores.
7. Read `references/playbook.md`, then read `../layer2-html-research-playbook/SKILL.md` and its `references/common.md`. Render exactly one standalone HTML file.
8. Verify the canonical PC-width layout, responsive fallback, Mainland China red-up/green-down signed values, event-title source link, source labels, evidence gaps, and the four-part disclaimer.

## Output Contract

The page must follow this reading order: topbar, tabs, hero, event factors and objective data, attribution reasoning, value-chain position and business exposure, historical similar events, post-event market reaction, source review, evidence chain, opposing evidence, and next verification items.

The event title and its source-review entry must appear at the beginning of the hero. Use a real returned article, announcement, report, or mini-program URL; when no article-level URL exists, show the source type without a fake link.

## Failure And Safety Contract

- Do not convert source failure or missing samples into a neutral-looking fabricated section.
- Do not expose internal routes, tools, IDs, backend wording, raw responses, or retry logs.
- Rule-based contribution is explanatory only and must be labeled. It is not a market metric, forecast, or investment signal.
- Do not promise returns, output target prices or buy/sell points, read holdings or trade history, or provide individual stock recommendations.
