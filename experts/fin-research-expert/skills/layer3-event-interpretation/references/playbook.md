# Event Factor Impact Playbook

Owned by `layer3-event-interpretation`. Use `layer2-html-research-playbook` only for the shared rendering contract.

Playbook type: event-factor-impact

Use this reference for 事件影响、因子归因、政策/公告/新闻传导、产业链权重, or historical similar-event interpretation pages.

## Evidence Inputs

Use only evidence already collected by the research workflow:

- event description, affected company or industry, evidence window, and conclusion boundary;
- public news, announcement/PDF, market and financial data, industry graph context, Same Boat viewpoints, and user-provided facts;
- public factor framework, factor evidence panels, and factor metric values from fin-graph when available;
- historical similar-event statistics only when returned by `aggregate_similar_event_backtest` or provided by the user.

## Required Layout

Use this exact product-prototype reading order:

1. topbar
2. tabs
3. hero
4. 事件影响因子与客观数据
5. 因子归因如何推导结论
6. 公司产业链地位与核心业务权重
7. 历史相似事件
8. 相似事件后的股价平均走势
9. 源头复核
10. 证据链、反方证据与后续验证

## Hero Rules

- Lead with one plain-language conclusion about what the event changes and what remains unproven.
- At the very beginning of the hero, show the event title and review entry. If an article, announcement, report, or mini-program URL is available, make the event title a visible source-review link before company/industry metadata and before the conclusion. If no article-level URL exists, show the event title with source type only and do not create a fake link.
- Show composite impact or evidence-strength as a horizontal score card, not a circular score.
- Show factor cards as row-style metrics with separators and a bottom progress line, not as small boxed KPI tiles. Each card should read like: factor title + direction badge, two objective metric rows, percentile/progress label, progress bar.
- Match the supplied event prototype at PC width as the canonical layout: pale gray long-report background, white rounded cards, text-only page title, top right workbench actions, sticky capsule tabs, event-source review block, metadata chips, a left-side conclusion narrative, a right-side report-date/conclusion-grade card, then a four-column summary strip.
- Portrait covers are only responsive previews. They may stack the hero and summary cards, but must not drive the primary PC layout.
- Do not add an extra invented logo block in the topbar unless the source prototype contains one.
- Use Mainland China market color convention for signed market/factor values: positive/upward/`+` factors and numbers are red; negative/downward/`-` factors and numbers are green. Neutral, pending, or methodology elements should use blue/amber/gray rather than red/green.

## Factor Rules

Each factor must have:

- clear name and direction: positive, negative, neutral, or pending;
- objective data: price, volume, capacity, margin, revenue share, order, policy threshold, announcement number, or other measurable fact when available;
- source family and review path;
- a concise explanation of how the factor affects the final conclusion.
- When fin-graph factor tools are available, use `get_public_factor_framework` first, then `get_factor_evidence_panel` for selected factors, then `get_factor_metric_values` for measurable current values or short histories. Factor cards should prefer returned metric values over generic `观察` labels, and cite source family in user-facing language.
- For valuation factors, use fin-data as the numeric source. Named-stock event pages should use `query_data` with `pe_ttm`, `pe`, `pb`, and `market_cap` after resolving the ticker; industry event pages should use `query_sector_valuation` only after resolving a stable Shenwan industry name. fin-graph may identify that valuation is a relevant factor, but PE/PB values should come from fin-data, not from the graph.

## Rule-Based Quantification

When retrieved evidence includes factor frameworks, evidence panels, source links, and historical statistics but not complete current numeric values, produce a transparent `规则评分` instead of filling the page with backend-gap wording. If `get_factor_metric_values` returns usable metrics, use those values first and only use rule scoring for missing dimensions.

- Factor strength score: start from 50, add up to +15 for a matching public graph factor, +15 for a factor evidence panel with concrete metric names, +20 for matching historical event statistics, +10 for source-review links, and +10 for direct value-chain exposure. Subtract up to -15 for clear opposing evidence. Cap scores to 0-100.
- Factor direction must still be evidence based: use `正向`, `负向`, `观察`, or `中性`. Do not claim a current price, capacity, share, margin, PE/PB, or revenue percentage unless it is actually provided.
- If exact current values are unavailable, show useful substitutes such as `指标已确认`, `规则评分 64/100`, `暴露等级：高/中/低`, or `证据等级：强/中/弱`; avoid repeated backend-gap phrasing. Put missing-value boundaries in 数据口径, not inside every factor card.
- Attribution contribution may be rule-based only when labeled as `规则贡献`, using direction × factor strength × exposure band. It is an explanatory score, not a financial metric or investment signal.

## Attribution Layout Rules

- At PC width, the attribution section must be a two-column layout: left table, right `归因合成结果` score panel.
- The right score panel must include the composite score, a one-sentence contribution summary, and signed factor contribution bars centered around zero.
- Do not render the attribution table as a full-width block with the score panel below it at desktop widths.

## Company Chain And Weight Rules

- Explain the company's position in the industry chain: upstream, midstream, downstream, platform, equipment, material, channel, or end demand.
- At PC width, render this section as two columns: left `chain-map` with four linked nodes, right `business-panel` with business exposure rows and horizontal progress bars.
- The company/current-position node should be visually highlighted. Do not render all chain nodes as unrelated equal cards.
- Show core-business exposure or impact weight only when evidence provides revenue share, product share, capacity share, order amount, shipment proportion, segment margin, or a clearly stated business contribution.
- If exact weight is unavailable, use a qualitative exposure band and state the basis, for example `暴露等级：高（供应商份额字段 + 车企排产线索）`. Do not label this as exact revenue weight.

## Similar Event Rules

- Present historical similar events only when the evidence includes comparable-event records or user-provided cases.
- Keep the source prototype structure: four matching-condition cards first, then a vertical `event-list` of horizontal sample rows with date/sample id, event title, short evidence note, and similarity badge.
- Do not render the historical sample rows as a four-card grid at PC width.
- Compute and present `相似度` from retrieved evidence: demand/policy match 25%, value-chain match 25%, valid backtest windows 25%, public source review 15%, and negative/mixed evidence adjustment up to -10%. Keep the explanation user-facing; do not mention backend fields, internal services, or backend availability. Badges should read like `相似度 84%`.
- Show 3-day, 5-day, 7-day, and 20-day average走势 as the main post-event path when statistics are actually provided; label 20d as `约1个月 / 20 个交易日`.
- Treat 60d as an optional long-horizon supplement, not a required main window. Request and display 60d only when the user asks for roughly three months or when the returned valid sample count is enough to support a long-horizon review. Do not drop otherwise valid 3d/5d/7d/20d samples because 60d is missing or invalid.
- When both company-event backtest and industry/index backtest are available, plot and tabulate them side by side as `公司事件样本` vs `行业基准样本`, and show excess return as `公司 - 行业`.
- Prefer `aggregate_similar_event_backtest` for sample statistics. Use `60d` as the v1 display proxy for `约 3 个月 / 60 个交易日` only in the optional long-horizon supplement.
- If market-reaction evidence is recomputed with fin-data, label the target clearly as stock, index, ETF, or concept. Do not merge company-event backtest with industry/index backtest without source labeling.
- If the product prototype requires the historical module before the statistics source is ready, keep the visual structure with user-facing boundary labels such as `样本不足` or `需行业基准复核`; do not invent returns, win rates, sample sizes, or similarity scores.

## Source Rules

- 原文索引 should prioritize official announcements, public news, report links, and mini-program review links.
- Market, finance, and graph data without article-level links should be attributed by 来源类型 in the factor cards or data-methodology section, not shown as fake source cards.
- Keep the final page analytical and readable for non-professional users while preserving source review.
