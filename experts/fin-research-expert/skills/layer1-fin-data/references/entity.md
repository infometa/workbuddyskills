# Entity Reference

Use for:
- 股票/ETF/港股名称和代码互查
- 公司基础信息、行业、交易所、板块
- 概念股、行业成分、ETF 成分、主题成分
- Layer 2 在多个工具之间传递稳定实体

Tools:

## search_security
- Fuzzy search by company/security name or ticker.
- `market`: `all` | `a_stock` | `etf` | `hk_stock`.

## search_security_with_market_data
- Use when discovery and latest comparable market facts are both needed.
- `sort_by`: `match` | `amount` | `volume`.
- A-share candidates use latest-available snapshots; ETF/HK candidates use latest-available daily rows.
- Keep identity candidates when `market_data_status="missing"`; do not rewrite missing facts as zero.
- When `metadata.extras.cache_status="stale"`, display `data_date` and label the result as a recent fallback.

## get_security_profile
- Use after ticker is known.
- `market`: `a_stock` | `etf` | `hk_stock`.

## rank_etf_candidates
- Use for a named index/theme when the user asks which listed ETFs correspond to it or wants evidence-based candidate comparison.
- Prefer a resolved `tracking_index_id`; otherwise pass a concise index/theme keyword.
- Preserve `product_variant`; ordinary tracking, enhanced, strategy, and feeder products are not interchangeable.
- The ranking uses returned daily amount, volume, turnover, premium and premium rate only. It has no AUM, bid/ask spread, order book, or realtime creation/redemption evidence.
- Present it as candidate comparison, never a fund recommendation.

## resolve_entities
- Use when Layer 2 needs stable entity IDs.

## get_entity_links
- Use to fetch lightweight relation hints for an entity.

## search_baskets
- Use for industry/theme/concept/ETF basket discovery.
- Pass the user's original industry/theme keyword into the search field before any constituent, ranking, or valuation call. The current gateway wrapper uses `keyword`; if `tools/list` exposes a different schema, follow the returned schema instead of guessing.
- `basket_type`: `industry` | `etf` | `concept` | `theme`.

## Resolver Target Basket Reuse
- If an upstream fin-graph resolver result is already available, prefer its `source_ids.fin_data_theme_basket_id` or `source_ids.fin_data_sw_basket_id` for fin-data basket calls.
- Keep the resolver result fields `canonical_id`, `source_ids`, and `coverage_gaps` in the internal evidence ledger so Layer 2 can explain the口径.
- Use `source_ids.fin_data_theme_basket_id` for lycode-backed theme baskets and `source_ids.fin_data_sw_basket_id` for mappable Shenwan industry baskets.
- If both target basket fields are missing, call `search_baskets` and state the basket coverage gap; do not use Same Boat `sector_id`, Fin Graph `graph_subject`, market index code, or user text as a fin-data `basket_id`.

## list_constituents
- Use after `search_baskets` when possible.
- Prefer `basket_id` over free-text basket name.

Rules:
- Do not guess uncommon ticker or basket IDs.
- Search first, then query constituents/profile.
- For multi-market discovery with comparison facts, prefer `search_security_with_market_data` over repeated per-symbol calls.
- Do not hard-code member lists in upper-layer skills.
- Keep a basket resolution ledger for upper-layer workflows: `user_input`, `resolved_basket_id`, `resolved_basket_name`, `basket_type`, `source_tool`, and the selected candidate reason.
- `list_constituents` must use a returned `basket_id` when present. Do not invent Shenwan, theme, ETF, or concept IDs from memory.
- If `search_baskets` returns multiple plausible rows, choose only an exact or clearly near match by name/type/source. Otherwise ask the user to pick from 3-5 candidates instead of silently selecting one.
- Do not reuse Same Boat `sector_id`, Fin Graph `subject`, or user text as a Fin Data `basket_id`.
- For Shenwan valuation, call `query_sector_valuation(industry_name="<returned industry/basket name>")` with an exact returned industry name. If the best basket is a concept, theme, ETF, or non-Shenwan basket, label that source clearly and do not pretend Shenwan valuation exists.
- Do not say engineering has not solved this, 工程上没有解决, or 后端没做 for basket resolution problems. Use `search_baskets`, state that no stable basket candidate was returned, or ask for clarification.
- For unsupported claims and investment-sensitive answering style, also read `references/limitations.md`.
