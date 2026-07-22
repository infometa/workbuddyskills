# Playbook Style

## WorkBuddy Role

WorkBuddy Playbook cases are the proof and reuse layer. They answer the question "what did these capabilities actually produce" by showing a concrete artifact, the prompt that generated it, and the associated expert/skill/connector capabilities.

For this expert, Playbook cases should demonstrate public financial research outputs. The reviewed industry and event cases run through `layer3-industry-windvane` and `layer3-event-interpretation`; those user-story workflows compose evidence modules and call `layer2-html-research-playbook` only for shared rendering. They are not separate data capabilities and must not extend the expert beyond approved gateway grants. For any complex artifact, use `layer2-evidence-ledger`, `layer2-transmission-chain-builder`, and `layer2-research-red-team` for source audit, impact chain, and falsification checks before HTML rendering.

## Required Playbook Shape

Each Playbook case should include:

- `case.json` as the case metadata file;
- one output artifact for the current package, usually `output.html`;
- `cover.png` at 720x400 for official WorkBuddy inspiration submission;
- a clear card title;
- `HTML` as the output type for the current package;
- a short description focused on the user problem;
- tags that match user-facing scenes, not internal route names;
- used capability badges such as `fin-data-query`, `doc-search`, `fin-graph`, and `same-boat`;
- a toolset description for the WorkBuddy right-side detail panel, usually shown as `同舟股市投研专家` plus the public evidence families it uses;
- a detailed introduction explaining the result and evidence boundaries;
- a source review area with clickable source links when the gateway evidence includes URLs, document links, report links, mini-program links, or original-page links;
- a reusable "做同款" prompt with variables;
- a standalone `output.html` sample.

Repository-only long previews such as `cover-portrait.png` may be kept for QA,
but the exported submission bundle should normalize `case.json.cover_image` to
`cover.png` and `case.json.cover_mode` to `landscape`.

Official-style "做同款" prompts should be explicit enough to reproduce the artifact:

- name the visible capability, such as 同舟股市投研专家, not internal route IDs;
- specify the subject, for example `{公司名/股票代码}` or `{行业/主题}`;
- state the evidence window and source families to retrieve;
- list fixed sections in the expected order;
- require a top tab navigation bar inside the HTML artifact when the page has multiple major sections;
- define card fields, including title, source label, short summary, time, and source link when returned;
- require source-review links and a clear fallback when links are not returned;
- require a single-file HTML output with inline styles and any essential
  interaction embedded locally; no external rendering assets.
- avoid multi-turn setup. The prompt should be one-shot: after the user fills
  placeholders such as `{公司名/股票代码}` or `{行业/主题}`, WorkBuddy can produce
  the reviewed output shape without asking for hidden files or manual context.

## Output Principles

The artifact should show the result before explaining the machinery:

1. State the research question and evidence window.
2. Show the main conclusion, confidence, and gaps in the first viewport.
3. Use a top tab navigation bar for pages with 4+ major sections. Prefer `button[data-target]` with a tiny inline `scrollIntoView` handler; do not use hash links such as `href="#section-id"` because host routing may intercept them.
4. Separate facts, interpretation, risk, and next verification items.
5. Keep source labels visible:行情数据、公告、新闻、研报、行业图谱、同舟观点.
6. For any key fact with a returned source URL, show a user-facing "查看源头" link. Source-review anchors may use returned `http(s)` URLs, but external rendering resources are still forbidden: no CDN scripts, external stylesheets, remote images, fonts, or `@import`. If a market, financial, or graph datum has no URL, do not render it as a source card or missing-field warning; attribute it in the body or methodology as 同舟行情库、同舟财务指标库、同舟行业图谱, and never invent a link.
7. Use Mainland China market colors consistently: red for positive/up/`+`/bullish/supporting evidence, green for negative/down/`-`/bearish/risk or opposing evidence, blue/teal/gray for neutral structure, and amber for mixed, boundary, missing, or pending evidence.

## Industry Windvane Visual Contract

Detailed layout rules now live in `skills/layer3-industry-windvane/references/playbook.md`. Keep this file as the cross-type publishing contract.

The shared visual boundary is: do not use circular score rings, donut charts, waterfall score charts, oversized marketing heroes, tiny radar thumbnails, thin unreadable radar labels, or visible tool-failure chips. Do not expose phrases such as `接口失败`, `超时`, `外部数据源暂不可用`, `未返回可用数据`, backend parameter names, or raw tool logs in final HTML.

## User-Facing Patterns

Prefer these public names in cards, prompts, and artifact headings:

- 事件因子解读
- 行业多空风向标

Avoid making Playbook titles sound like internal research workflow names. Terms such as "个股批判性分析", "研报共识与分歧雷达", and "行业/板块异动归因" can remain internal reasoning labels, but should not be the first thing a WorkBuddy user sees.

## What Not To Do

- Do not use Playbook examples to advertise account diagnosis, trade review, sales scripts, PA workflows, customer profile workflows, or private holdings analysis.
- Do not include raw MCP JSON, internal route labels, backend IDs, search scores, graph node IDs, API keys, SMS codes, full phone numbers, account identifiers, holdings, trade history, or raw document text.
- Do not imply that a sample HTML artifact was generated from live current data unless the artifact records a valid evidence window and source boundaries.
- Do not make the "做同款" prompt depend on a hidden local file, a private account, or a non-public workflow.
- Do not fabricate source URLs. Only link to URLs returned by the gateway evidence or to clearly labeled public review entry points.

## Packaging Relationship

The expert is the user-facing role. The gateway is the connector. `fin-mcp-gateway` is the method and safety layer. The two reviewed `layer3-*` skills own complete user stories, `layer2-html-research-playbook` is their shared presentation layer, and `playbooks/cases` are reusable proof examples. Candidate case templates remain source-only until review.

When writing or updating a Playbook prompt, avoid `layer1-*`, `layer2-*`, and `layer3-*` names in the user-facing text. If route IDs are needed for tests or review notes, keep them out of user-visible copy.

For case metadata, keep `skills: []` when the capability is bundled inside this
expert rather than independently listed in the WorkBuddy Skill marketplace. Link
the real `同舟股市投研专家` Expert and `同舟公开 MCP Gateway` MCP instead of inventing
marketplace Skill IDs.
