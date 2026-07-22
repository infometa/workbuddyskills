# Industry Windvane Playbook

Owned by `layer3-industry-windvane`. Use `layer2-html-research-playbook` only for the shared rendering contract.

Playbook type: industry-windvane

Use this reference for 行业多空、风向标、看多看空、短中长期拆解, or similar industry/theme direction pages.

## Evidence Inputs

Use only evidence already collected by the research workflow:

- resolver result for the industry/theme identity, including `canonical_id`, `source_ids`, and `coverage_gaps`;
- source IDs used for this page, especially `same_boat_sector_id`, `fin_data_theme_basket_id`, `fin_data_sw_basket_id`, `market_index_code`, `graph_subject`, and `rfg_frame_id`;
- dynamically resolved industry or theme name; never hard-code sample sector IDs or old demo parameters;
- industry index or representative market data, valuation when available, money/crowding signals, news/events, industry anomalies, Same Boat viewpoints, and graph or supply-chain context;
- public factor framework, factor evidence panels, and factor metric values from fin-graph when available;
- batch market reaction statistics from fin-data only when the target is clearly labeled as industry index, ETF, concept index, or representative stock;
- returned public source links for news, announcements, reports, or mini-program review pages.

## Required Layout

Use this exact product-prototype reading order:

1. topbar
2. tabs
3. hero
4. signal strip / 核心判断条
5. 期限拆解
6. 证据解读
7. 六维因子
8. 情景与验证矩阵
9. 原文索引与源头复核
10. 四类材料解释
11. 看点与风险
12. 数据口径

## Hero Rules

- Left side: user-facing conclusion, valid event-window cards, and `接下来最该盯的三条线`.
- Right side: horizontal score card with a large composite score or evidence-strength label, red/yellow/green scale, and a plain-language evidence interpretation.
- 不要使用环形计分, donut charts, waterfall score charts, oversized marketing heroes, tiny score widgets, or visual metaphors that imply guaranteed prediction.
- Match the WorkBuddy product prototype: pale gray page background, white rounded cards, sticky capsule tabs, dense long-report layout, text-only topbar title with optional evidence-cutoff metadata, and first screen split into content left plus score card right.
- Do not add an extra invented logo block in the topbar unless the source prototype contains one.
- Do not render fake workbench actions such as `生成资产底图`, `收藏`, or `引用口径` unless the generated HTML implements the action end-to-end. For this playbook, prefer no top-right actions.
- Tabs must follow the body section order exactly. Every tab must point to an existing section id, and every major body section in the required layout should either have a matching tab or be intentionally merged with the neighboring section.

## Factor Visualization Rules

- The product prototype uses horizontal six-factor bars as the main visual. Use bars by default; do not force a radar chart unless the user explicitly asks for radar.
- Factor names must follow retrieved data. Use Same Boat returned industry radar dimensions first. If no radar dimensions are returned, use fin-graph public factor names such as demand, supply, cost curve, valuation, policy, and upstream resource risk. Only fall back to generic six-factor labels when neither source returns usable dimension names.
- Put the six factor scores in a prominent section with labels, colored progress bars, and concise data-backed explanations. When `get_factor_metric_values` returns metrics, show at least one metric value or short-history change in the corresponding factor detail; do not reduce it to `观察` or `字段可用`.
- Below or beside the factor bars, add factor detail cards for every category. Each card must explain the industry meaning, support logic, pressure logic, and next verification point in analyst-facing language. Do not expose backend phrasing such as “tool returned”, “panel returned”, “not returned this round”, field names, parameter names, or raw availability notes; put data gaps only in 数据口径. This prevents the factor chart from feeling like a black-box judgment while keeping the page user-facing.
- When fin-graph factor tools are available, call `get_public_factor_framework`, `get_factor_evidence_panel`, and then `get_factor_metric_values` before assigning factor explanations. Use returned metric values first; use rule-based score bands only for dimensions without usable series.
- Follow the Mainland China market convention for signed factor semantics: positive/supporting/`+` factors and numbers are red; negative/opposing/`-` factors and numbers are green. Use amber for mixed or pending factors, and blue/teal/gray for neutral structure.

## Body Rules

- 原文索引 contains only clickable public source cards. Do not list market, graph, or financial data as source cards if they have no URL.
- 期限拆解 must match the product prototype but must be data-first: show compact white cards for valid event windows rather than forcing short/mid/long labels. The main horizon statistics should use retrieved `3d/5d/7d/20d`; prefer cards such as `3 日窗口`, `5-7 日窗口`, and `约1个月 / 20 个交易日`. Each card must include retrieved average return or win-rate, sample count when available, a small in-card sparkline, and one concise interpretation. Do not add a separate large return-path chart below the cards.
- Horizon sparklines must be data-bound, not decorative. Positive trend paths should move upward and negative trend paths should move downward. If a window has no valid values, omit that point from the main horizon card and explain the gap in 数据口径 or long-term validation language.
- Horizon statistics should prefer `compute_market_reaction_windows` over manual arithmetic when multiple historical events are involved.
- If only related-stock samples are available, label them as `相关个股事件样本`; do not call them industry index backtests.
- 证据解读 must explain the score or evidence-strength label in user-facing language. Do not show model-like decomposition. Use evidence cards such as `历史样本`, `行业景气`, `主要变量`, and `样本边界` to explain what is clear, what still needs observation, and what was skipped.
- 四类材料解释 should show industry graph, recent research summaries, market news, and related data tables as separate support cards. The graph card should separate factor framework, metric values, and source boundary. The market-news card must explicitly show `新闻情绪强度`, positive/risk clue counts or ratios, and the data source / classification basis. Do not draw an unlabeled sentiment trend line.
- 情景与验证矩阵 replaces prediction wording. It should show horizon/scenario, current judgment, historical behavior, and invalidation signal; it must not imply a guaranteed forecast. Use a four-column table where tags such as `看多`, `中性观察`, or `看空触发` are embedded inside the current-judgment cell. Do not create a standalone `标签` column.
- 数据口径 records source families, evidence window, optional gaps, statistics availability, identity evidence (`canonical_id`, selected `source_ids`), and `coverage_gaps` in user-facing terms. If there is 缺少来源覆盖, describe the missing family plainly; 不要用宽基指数、示例行业或假 ID 替代.

## Statistics Boundary

Do not invent win rate, backtest, average return, or sample-size charts. If `compute_market_reaction_windows` or an equivalent retrieved statistic is unavailable, keep the visual slot but use user-facing placeholders such as `样本不足` or `待接入真实统计`, never fake numbers. Use `3d/5d/7d/20d` as the main event-window set. Treat `60d` as optional long-horizon review only when it has valid values; do not filter out otherwise valid `3d/5d/7d/20d` samples because `60d` is missing or invalid. If `60d` exists as a key but has zero valid samples, skip it from horizon cards, evidence interpretation, scenario matrix, material charts, and headline conclusions; mention the missing long-horizon sample only in 数据口径. If a broad index has 60d values while the industry/event sample does not, do not use that broad-index number as a substitute. At most label it as an auxiliary cross-check in 数据口径.
