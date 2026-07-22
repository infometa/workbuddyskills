# Layered Capability Reference

The WorkBuddy Fin Research Expert exposes approved public financial research workflows only. Layer 2 modules and Layer 3 user stories inherit the authenticated Connector's Layer 1 namespace/tool grants; they do not create additional data rights.

The WorkBuddy packaging presents this as a single `同舟股市投研专家`: one public-equity expert for sector moves, stock analysis, event impact, report mining, and reusable Playbook outputs. Core public-market `layer1-*` skills are tool contracts, `layer2-*` skills are reusable research and presentation modules, and reviewed `layer3-*` skills own complete user stories; broad market timing, cross-asset allocation, sales, care, PA, account diagnosis, trade review, and event prediction are not exposed as launch capabilities until matching MCP contracts and review approvals exist. Descriptive historical event backtest and similar-event aggregation may be used only when returned by the approved doc-search and fin-data MCP tools.

## WorkBuddy Ecosystem Alignment

This file is an internal routing reference, not a user-facing product catalog.

| WorkBuddy module | This package's role | Boundary |
|---|---|---|
| Expert | `同舟股市投研专家` is the single user-facing role | Do not split v1 into multiple same-brand experts. |
| Connector | Tongzhou MCP Gateway provides governed public-market data and document access | The gateway grant profile is authoritative. |
| Skill | `fin-mcp-gateway` teaches authentication and routing; Layer 1 defines source contracts, Layer 2 supplies reusable modules, and Layer 3 owns reviewed user stories | No Skill creates new data rights or private advisory workflows. |
| Playbook | `playbooks/cases` provides reusable HTML examples and "做同款" prompts | Samples must stay within approved public research workflows. |

Use user-facing scene names in answers and marketplace copy: 个股分析、行业异动、事件解读、研报挖掘、证据页、同舟观点整理. Keep `layer1-*`, `layer2-*`, `layer3-*`, server/tool names, IDs, and MCP session details inside internal routing, tests, and debugging.

## Approved Layer 1 Source Namespaces

WorkBuddy exposes these logical sources through one `tongzhou-fin-research` Connector. The source names remain useful for routing and grants, but they are not four user-visible Connector entries.

| Source namespace | WorkBuddy tool prefix | Layer 1 skill | Purpose | Status |
|---|---|---|---|---|
| `fin-data-query` | `fin_data__*` | `layer1-fin-data` | Structured market, macro, financial, ranking, basket, and security data | launch |
| `doc-search` | `doc_search__*` | `layer1-doc-search` | News, announcements, events, research reports, morning notes, document details | launch |
| `fin-graph` | `fin_graph__*` | `layer1-fin-graph` | Industry graph, industry views, crowding, anomalies, macro panels | launch |
| `same-boat` | `same_boat__*` | `layer1-same-boat` | 同舟 research sectors, analysts, market news, quotes, viewpoints, event interpretation | launch |

## Released Tool Contract Catalog

This compact catalog is the release-grant index. It does not replace each Layer 1 parameter reference. Before a call, load the preferred Layer 1 reference named below and follow the live `tools/list` schema. Market scope, units and dates are always bounded by fields actually returned by the source.

<!-- RELEASED_TOOL_CATALOG_START -->
| Namespace | Released tools | Markets / coverage | Required inputs | Units | Date semantics | Preferred route | Fallback / errors |
|---|---|---|---|---|---|---|---|
| `fin-data-query` | `get_schema` `list_metrics` `list_featured_indicators` | Source metadata; market depends on metric | None or discovery filter | Returned metadata | No market date unless returned | `layer1-fin-data` market or macro preflight | Narrow discovery once; classify schema error as service/error, not empty evidence |
| `fin-data-query` | `query_data` `batch_query_data` | A/H/US, index and source-supported series | Resolved entity/metric plus bounded date range | Source field unit/currency | Preserve each series' actual dates | `layer1-fin-data/references/market.md` | Split batch or narrow metric once; empty/unsupported/error remain distinct |
| `fin-data-query` | `get_kline_series` | Source-supported securities; currently daily K-line contract | Resolved market and ticker, bounded points/date range | Price currency and volume unit returned | Trading dates from rows | `layer1-fin-data/references/market.md` | Retry normalized code once; unsupported interval/market is not an empty company fact/error |
| `fin-data-query` | `get_latest_snapshot` `batch_get_latest_snapshots` | A/H/US/ETF/index where available | Resolved market+ticker or bounded identifiers | Returned currency, percent and volume units | Display source quote/trading time | `layer1-fin-data/references/market.md` | Split batch once; retain per-symbol partial/unsupported/error state |
| `fin-data-query` | `compute_market_reaction_windows` `compute_batch_reaction_windows` | Securities, ETF/index and mapped industry series | Resolved identifiers, event dates, explicit windows | Percent return and source price unit | Event date plus trading-day windows | `layer1-fin-data/references/market.md` | Drop invalid windows, not samples; insufficient sample and service error are separate |
| `fin-data-query` | `search_security` `search_security_with_market_data` `get_security_profile` `resolve_entities` `get_entity_links` | A/H/ETF and returned overseas coverage | Name/code; profile/links require resolved identity | Identity and returned market units | Preserve candidate market date; stale cache must be labeled | `layer1-fin-data/references/entity.md` | Name/code normalization once; keep identity when market data is missing; ambiguous/unsupported/error must not be silently selected |
| `fin-data-query` | `search_baskets` `list_constituents` | Industry/theme/concept/ETF baskets | Keyword then returned `basket_id` | Weights/units exactly as returned | Constituent as-of date when present | `layer1-fin-data/references/entity.md` | Ask on ambiguity; no broad-index substitute, fake basket, or hidden error |
| `fin-data-query` | `query_sector_valuation` | Supported Shenwan industry names | Exact resolved industry name | Returned PE/PB and percentile units | Preserve valuation date | `layer1-fin-data/references/macro_financial.md` | Parent/near-match only when labeled; empty coverage differs from error |
| `fin-data-query` | `rank_etf_candidates` `rank_securities` `list_top_movers` `screen_stocks` `count_stocks` `detect_stock_patterns` | Supported A-share/ETF/basket universe | Explicit universe, field/condition, date and limit | Returned price/percent/count units | Trading/data date from result | `layer1-fin-data/references/screening.md` or `entity.md` for ETF candidates | Narrow universe once; no fabricated ranking or unavailable AUM/spread fields on empty, unsupported, or error results |
| `fin-data-query` | `search_macro_indicators` `query_macro_series` | China/global source-supported macro series | Indicator discovery then ID and date range | Source unit/frequency | Observation/release dates from rows | `layer1-fin-data/references/macro_financial.md` | Retry a normalized keyword once; preserve frequency gaps and error state |
| `fin-data-query` | `query_financial_indicators` | Supported listed-company fundamentals | Resolved company/ticker and indicators | Reported currency, ratio or percent | Report period and announcement date when returned | `layer1-fin-data/references/macro_financial.md` | Keep field-level partial; do not infer missing values after error |
| `fin-data-query` | `query_advisor_report` | Supported market daily report types | Explicit report type/date scope | Mixed source units | Report/trading date returned | `layer1-fin-data/references/market.md` | Fall back to individual market facts, not a model-written report after service error |
| `doc-search` | `search_documents` `list_categories` | Public document index across returned markets/types | Query plus explicit type/source/date filters when known | Document metadata | Published/indexed dates as labeled | `layer1-doc-search/references/limitations.md` | Discover valid categories or relax one filter; empty/unsupported/error stay distinct |
| `doc-search` | `search_company_news` | A/H/US/UK company news in indexed sources | Resolved company; ticker optional by market | Document metadata | Preserve publication date | `layer1-doc-search/references/news.md` | Code-empty then company-name retry once; never claim no news on error |
| `doc-search` | `search_events` `search_normalized_events` `get_entity_event_timeline` | Indexed company/industry events | Resolved entity/topic, event/date scope | Event metadata | Event and publication times kept separate | `layer1-doc-search/references/announcements-events.md` | Relax event subtype once; partial timeline, unsupported source and error are explicit |
| `doc-search` | `search_hot_news` `search_morning_trading` | Indexed market/industry news and morning notes | Topic/market/date window | Document metadata | Returned publication/trading date | `layer1-doc-search/references/news.md` | Narrow broad intent or use general documents; do not fill empty/error with memory |
| `doc-search` | `search_announcements` | Indexed announcements; HKEX native coverage excluded unless returned | Resolved company/ticker, announcement/date filters | Document metadata and reported units | Announcement date | `layer1-doc-search/references/announcements-events.md` | Company-name retry once; disclose source gap instead of treating error as no announcement |
| `doc-search` | `search_research_reports` | Indexed A/H/US/UK broker research coverage | Resolved company/industry and date window | Report metadata | Report publication date | `layer1-doc-search/references/research.md` | Code-empty then company-name retry once; no complete-coverage claim after error |
| `doc-search` | `search_backtested_events` `get_event_backtest` `aggregate_similar_event_backtest` | Returned historical event samples only | Event identity/sample IDs and explicit 3/5/7/20d windows | Sample count and percent return | Event date plus trading-day horizons | `layer1-doc-search/references/announcements-events.md` | Omit invalid 60d; insufficient sample differs from unsupported/error |
| `doc-search` | `get_document` | A previously returned indexed document | Returned document identifier | Text/document metadata | Preserve source publication date | `layer1-doc-search/references/document-detail.md` | Do not guess IDs or fabricate links; unavailable body/error leaves metadata-only evidence |
| `doc-search` | `get_document_summaries` | 2-5 selected search results from one evidence task | Current subject-bound evidence references and exact document types | Stored summaries only | Preserve each source publication date | `layer1-doc-search/references/document-detail.md` | Missing summary or error remains explicit; no original-text fallback, export path, cross-user references, or more than five items |
| `doc-search` | `get_document_source_coverage` | Configured public document source families | Optional public source-type list | Aggregate counts only | First/last indexed dates plus statistics time | `layer1-doc-search/references/document-detail.md` | Source error remains unavailable; no document lists or internal index names, and endpoints do not imply continuous coverage |
| `fin-graph` | `list_supported_subjects` `resolve_research_identity` `list_research_identities` `get_research_identity_coverage` | Industry/theme identity systems, not company tickers | Query/identity filters; coverage requires resolved identity | IDs and coverage flags | Resolver as-of only when returned | `layer1-fin-graph/references/identity.md` | Show candidates or coverage gaps; never cross-borrow IDs after error |
| `fin-graph` | `get_research_frame_overview` `get_research_frame_tree` `query_research_frame_nodes` `get_industry_chain_research_map` | Bounded industry-chain research frames | Resolver-returned frame/topic plus depth/limit | Graph labels/weights as returned | Frame/source date when present | `layer1-fin-graph/references/industry-chain-graph.md` | Parent frame only when labeled; no invented chain nodes on empty/error |
| `fin-graph` | `get_industry_graph` `get_graph_overview` `query_graph_nodes` `get_graph_node_brief` | Public-safe industry graph subjects | Resolver-returned subject/node and bounded depth/limit | Graph fields as returned | Snapshot/as-of when returned | `layer1-fin-graph/references/industry-graph.md` | Use supported-subject discovery; preserve unsupported subject and service error |
| `fin-graph` | `get_public_factor_framework` `get_factor_evidence_panel` `get_factor_metric_values` | Supported public factor subjects | Resolved subject/factor/metric | Source metric unit/scale | Evidence and observation dates | `layer1-fin-graph/references/industry-graph.md` | Omit unsupported factor/value; never model-fill an empty/error panel |
| `fin-graph` | `list_industry_indices` `get_industry_views` `get_industry_crowding` | Supported industry indices and levels | Returned index/name; crowding needs explicit level | Returned score/percentile scale | View/as-of date | `layer1-fin-graph/references/market-signals.md` | Labeled parent-industry fallback once; missing scale or error stays partial |
| `fin-graph` | `list_industry_anomalies` `get_anomaly_detail` | Returned industry anomaly feed | Filters then returned anomaly ID | Returned move/score units | Event/observation time | `layer1-fin-graph/references/market-signals.md` | Detail only for returned ID; no causal claim when detail is empty/error |
| `fin-graph` | `get_macro_data` | Supported China/global macro panels | Panel/indicator filters | Returned source unit/frequency | Observation/release date | `layer1-fin-graph/references/market-signals.md` | Keep graph panel boundary; use fin-data macro only as labeled fallback after error |
| `same-boat` | `get_schema` `list_research_sectors` `search_research_sectors` | Same Boat sector taxonomy | None or sector query | Taxonomy metadata | As-of only when returned | `layer1-same-boat` sector discovery | Normalize query once; ambiguous/empty/unsupported/error must be visible internally |
| `same-boat` | `search_analysts` `get_analyst_profile` | Indexed Same Boat analysts | Name query then returned analyst ID | Profile metadata | Profile/update date when returned | `layer1-same-boat` analyst route | Do not guess analyst ID; empty profile and service error differ |
| `same-boat` | `list_market_news` `get_market_news` `get_market_news_analysis` | Same Boat market/sector news | Sector/market filters then returned news ID | Returned importance/popularity/sentiment scales | Publication/event time | `layer1-same-boat` market-news route | Fetch detail only for returned ID; no fake analysis or link after error |
| `same-boat` | `list_market_quotes` `get_market_quote_analysis` | Same Boat quote/market interpretation feed | Market filters then returned quote/content ID | Returned quote units and analysis fields | Quote/content time | `layer1-same-boat` quote route | Market data remains fin-data primary; empty analysis/error is not a price fact |
| `same-boat` | `list_market_viewpoints` `list_sector_viewpoints` `list_analyst_viewpoints` `get_market_viewpoint_detail` | Returned market, sector and analyst viewpoints | Resolved market/sector/analyst filters; detail ID | Returned sentiment/radar/score scales | Viewpoint publication time | `layer1-same-boat` viewpoint route | Preserve scale and source; no complete-consensus claim after empty/error |
| `same-boat` | `generate_content_url_link` | Selected Same Boat article/content only | Returned content ID | URL metadata | Link expiry/as-of when returned | `layer1-same-boat` source-review route | Use only returned URL; 403/empty/error means no article-level link, never a fake link |
| `same-boat` | `get_research_visual_evidence` | Selected supported Same Boat content | Returned content ID and visual request | Source chart/table scale | Content/visual date | `layer1-same-boat/references/visual-evidence.md` | Text evidence remains valid if visual unsupported; never synthesize source image after error |
<!-- RELEASED_TOOL_CATALOG_END -->

## Approved Layer 2 Routes

| Route | Trigger | Layer 1 dependencies | Evidence contract | Status |
|---|---|---|---|---|
| `layer2-stock-brief` | Named listed company or security | fin-data-query, doc-search | Security identity plus at least one of snapshot, news, announcement, or report | launch |
| `layer2-stock-narrative-valuation` | Named stock plus narrative, implied valuation, overpricing, moat, or rally-review question | fin-data-query, doc-search, stock/research/announcement evidence | Security identity, market cap or price context, financial/report assumptions when available, and explicit DCF/no-DCF boundary | launch |
| `layer2-industry-brief` | Named industry/theme | fin-data-query, doc-search, fin-graph, same-boat | Basket or industry identity plus recent news/event/report, graph evidence, or Same Boat sector viewpoint evidence | launch |
| `layer2-announcement-brief` | Announcement, annual report, forecast, buyback, restructuring | doc-search, fin-data-query | Announcement search result and document summary before interpretation | launch |
| `layer2-research-digest` | Research report, broker view, institution comparison | doc-search, fin-data-query, same-boat | Recent report list or same-boat viewpoints with dates and source type | launch |
| `layer2-policy-event-brief` | Policy, regulator, official meeting, event impact | doc-search, fin-data-query, fin-graph, same-boat | Event/news evidence, affected area, and follow-up variables | launch |
| `layer2-evidence-ledger` | Evidence ledger, source audit, support/opposition evidence | already retrieved public-research evidence | Evidence table with source type, time window, support/opposition/gap labels, and conflicts | launch |
| `layer2-transmission-chain-builder` | Transmission chain, event impact path, upstream/downstream links | already retrieved event/industry/market evidence | Event -> mechanism -> chain position -> benefit/pressure -> validation indicators | launch |
| `layer2-research-red-team` | Red-team review, risk critique, falsification checks | already retrieved public-research evidence | Counter-evidence, narrative gaps, key assumptions, and falsification signals | launch |
| `layer2-research-visuals` | Normal-answer K line, trend, event-return chart, governed report image | already retrieved and validated public-research evidence | WorkBuddy inline visual plus source-backed text/table fallback | launch |
| `layer2-html-research-playbook` | Shared HTML rendering after a workflow has fixed its output contract | already retrieved and typed public-research evidence brief | Presentation-only artifact with source labels, responsive layout, and explicit evidence limits; does not choose the scenario | launch |

## Approved Layer 3 User Stories

| Route | User story | Composed Layer 2 modules | Output contract | Status |
|---|---|---|---|---|
| `layer3-industry-windvane` | Named industry/theme to a complete 行业多空风向标 HTML page | industry brief, evidence ledger, optional transmission/red-team, HTML renderer | Resolved identity, valid horizons, six-factor evidence, scenario matrix, source review, and methodology gaps | launch |
| `layer3-event-interpretation` | Named policy/announcement/news event to a complete 事件因子解读 HTML page | event/announcement brief, transmission chain, evidence ledger, red-team, HTML renderer | Event title/source, objective factors, attribution, supported exposure, valid historical samples, and falsification checks | launch |

## Spreadsheet Capability Mapping

This matrix is the sanitized coverage view derived from the 同舟 capability spreadsheet. It is committed here so the WorkBuddy expert package can route product scenarios without shipping the raw workbook.

Status values:

- `launch`: Supported by approved Layer 2 workflows and Layer 1 sources for v1.
- `partial`: Can provide a bounded answer, but the expert must name missing coverage or avoid overclaiming.
- `future`: Requires new data, private account integration, personalization, or a new Layer 2 workflow before public exposure.
- `excluded`: Intentionally outside the open WorkBuddy v1 package.

### Evidence Source Arbitration Matrix

Use this matrix before selecting tools. It prevents duplicate Doc Search / Same Boat / Fin Graph calls for the same evidence need.

| Evidence need | Primary source | Supplement rule |
|---|---|---|
| Market price, index move, constituents, valuation, financials | `fin-data-query` | Supplement with documents or Same Boat only for explanation. |
| Public news breadth, announcements, broker reports, event timelines | `doc-search` | Supplement with market data or Same Boat interpretation only after the public source is established. |
| Important market news tiering or analyst interpretation | `same-boat` `market_news` / `market_news_analysis` | Use Doc Search only to cross-check broader public coverage. |
| Industry structure, graph outline, crowding, anomaly list | `fin-graph` | Use Same Boat or Doc Search only for interpretation or event evidence. |
| Industry long/short wind vane, sector score, analyst reasons | `same-boat` `market_viewpoint` | Use Fin Data/Graph for market and structural checks. |
| Anomaly reasons, risk assessment, related events, logic chains | Same Boat or Fin Graph anomaly detail, whichever produced the selected anomaly | Use Doc Search for related public-event evidence. |

Do not use Same Boat as a substitute for exchange market data, public announcements, or broker report retrieval. Do not use Doc Search as a substitute for Same Boat `importance_score`, `sentiment_score`, `radar`, or analyst interpretation. For normal answers, prefer one primary source plus one supplement.

### 业务 V2 包装视图

#### 股市投研主线

| V2 scenario | Public entry | Capability status | Exposure rule |
|---|---|---|---|
| 行业/板块异动归因 | `layer2-industry-brief` | launch | May appear in quick prompts and public description. |
| 个股批判性分析 | `layer2-stock-narrative-valuation`, `layer2-stock-brief` | launch | Use narrative/valuation when the user asks why the story or valuation may be right/wrong; never as buy/sell advice. |
| 事件解读分析 | `layer3-event-interpretation`, backed by event/announcement Layer 2 modules | launch | Produce the reviewed event-to-evidence-to-HTML user story; narrower text questions may stop at Layer 2. |
| 市场热点话题观察 | `layer2-industry-brief`, `layer2-policy-event-brief`, same-boat market news | partial | Only summarize returned public evidence after the topic is narrowed to an industry, event, or report angle; no direction recommendation. |
| 板块重要新闻 | 行业要闻智能解读 alias | launch | Treat as important sector-news digest with source and time window. |
| 相似事件列表 | 高度关联事件匹配 sub-scenario | partial | Prefer doc-search similar-event aggregation when valid backtest samples exist; otherwise return only retrieved related-event clues and name sample limits. |

#### 研报挖掘子场景

| V2 scenario | Public entry | Capability status | Exposure rule |
|---|---|---|---|
| 报告核心要点提炼 | `layer2-research-digest` | launch | Public report summary with source boundaries. |
| 热门行业/个股机构要点萃取 | `layer2-research-digest`, same-boat viewpoints | launch | Good single-expert use case when the time window is explicit. |
| 机构观点横向对比 | `layer2-research-digest`, same-boat viewpoints | partial | Compare returned viewpoints only; do not claim complete institution coverage. |
| 报告智能对话 | `layer2-research-digest` | partial | Bound answers to retrieved report chunks/details. |

#### 暂不上线能力

| V2 scenario | Capability status | Handling |
|---|---|---|
| 账户投资风格观察 / 账户投资优化建议 / 交易表现复盘 / 交易习惯回顾 / 交易心理偏差与引导 | future/excluded | Requires private holdings/trades, consent, and a separate advisory workflow. |
| 事件波动预判 | future | Current MCP set does not provide predictive event movement forecasts; offer public event timeline, impact variables, and historical descriptive samples instead. |
| 事件回测结果 | partial | Use doc-search compact event backtest and fin-data market reaction windows only as historical descriptive statistics; do not present them as predictions or strategy backtests. |
| 智能插入投研图表 | launch | Use `layer2-research-visuals` for structured market/event charts in normal answers; report images remain conditional on stable, permitted source evidence. |

### 同舟小程序

| Spreadsheet capability | Recommended route | Status | Notes |
|---|---|---|---|
| 行业要闻智能解读 | `layer2-industry-brief`, `layer2-policy-event-brief`, same-boat market news | launch | Use same-boat or doc-search evidence; keep the explanation plain-language. |
| 板块重要新闻 | 行业要闻智能解读 alias, `layer2-industry-brief`, same-boat market news | launch | V2 alias for important sector-news digest; include time window and source type. |
| 行业关键数据/指标一览 | `layer2-industry-brief`, fin-data-query, fin-graph | launch | Use structured data and graph context; avoid unsupported metrics. |
| 金融资讯影响力评级 | same-boat market news `importance_score` / `popularity_score` | partial | Can filter and tier Same Boat market news by returned importance/popularity scores; do not present it as an independently calibrated rating model. |
| 机构研调观点脉络 | `layer2-research-digest`, same-boat viewpoints | partial | Supported for recent viewpoints; timeline and trend-change detection must stay bounded by returned evidence. |
| 行业多空风向标与多维诊断 | `layer3-industry-windvane`, composed from industry/evidence modules | launch | The reviewed user story is available; omit unsupported horizons or factors, record gaps in methodology, and avoid deterministic forecasts. |
| 轻量化行业报告 | `layer2-industry-brief` | launch | Best initial fit for single-expert quick industry reports. |
| 行业异动归因 | `layer2-industry-brief`, fin-graph anomalies, same-boat anomaly interpretation | launch | Preserve source boundaries between market moves, graph anomaly, and same-boat explanation. |
| 高度关联事件匹配 | `layer2-policy-event-brief`, doc-search timelines, same-boat market news | partial | Requires bounded event matching; do not claim full historical similarity scoring. |
| 相似事件列表 | 高度关联事件匹配 sub-scenario, doc-search timelines/backtested events | partial | Prefer `aggregate_similar_event_backtest` for returned historical samples; no full similarity score or complete case-library guarantee. |
| 行业逻辑推理 | `layer2-industry-brief` | partial | Evidence-led reasoning only; no hidden chain or deterministic causality. |
| 行业异动真伪鉴定 | New or extended anomaly verification workflow | partial | Can present evidence and uncertainty, not a binary truth claim. |
| 股票多空预期 | `layer2-stock-brief`, `layer2-stock-narrative-valuation` | partial | Can summarize bullish/bearish evidence and implied assumptions; no direct buy/sell or forecast. |
| 账户投资风格观察 | Private account integration | future | Requires holdings and behavior data not in open v1. |
| 个股风险透视 | `layer2-stock-brief`, `layer2-stock-narrative-valuation` | partial | Public risk factors, narrative weak links, and falsification signals only unless user account data is later authorized. |
| 账户投资优化建议 | Private account integration | future | Requires holdings, suitability, and possibly regulated advisory workflow. |
| 交易表现复盘 | Personal trade-history integration | future | Requires user trades and permissions. |
| 交易习惯回顾 | Personal trade-history integration | future | Requires user behavior data and privacy controls. |
| 交易心理偏差与引导 | Personal trade-history and coaching workflow | future | Needs a separate behavioral coaching design and consent model. |

### 智能投顾

| Spreadsheet capability | Recommended route | Status | Notes |
|---|---|---|---|
| 通用金融问答 | Single expert fallback plus Layer 2 routing | partial | Useful as a routing shell; avoid making it a vague all-purpose promise. |
| 市场热点话题观察 | `layer2-industry-brief`, `layer2-policy-event-brief`, same-boat market news | partial | Narrow broad hotspot questions to industry, policy/event, or report evidence before answering. |
| 事件解读分析 | `layer3-event-interpretation`, composed from event/announcement modules | launch | Use the reviewed event user story for HTML; narrower text questions may stop at the matching Layer 2 brief. |
| 事件脉络追踪 | doc-search timelines, same-boat market news | partial | Needs a bounded event-window answer. |
| 事件波动预判 | Historical event evidence plus separate prediction workflow | future | Current v1 should not predict market movement from events. |
| 事件回测结果 | doc-search event backtest, fin-data market reaction windows | partial | Use compact historical windows only. Main windows are 3/5/7/20 trading days; label `20d` as “约 1 个月 / 20 个交易日”. Use `60d` only as an optional long-horizon supplement when valid, and avoid strategy-backtest wording. |
| 相似案例匹配 | doc-search similar-event aggregation | partial | Use returned sample counts, valid windows, and missing-sample counts; do not invent similarity scores. |
| 关联标的与上下游关系梳理 | `layer2-industry-brief`, fin-graph | launch | Good graph-backed scenario; avoid recommendation wording. |
| 个股异动分析 | `layer2-stock-brief` | launch | Use stock identity, market data, news, announcements, and research evidence. |
| 市场复盘报告 | Dedicated close-review workflow | future | Not packaged in the reviewed v1 scope; narrow to a specific stock, industry, event, or report instead. |
| 复盘风格个性化定制 | WorkBuddy personalization or memory | future | Requires style memory or user preference management. |
| 个股批判性分析 | `layer2-stock-narrative-valuation`, `layer2-stock-brief` | launch | Frame as narrative, valuation assumptions, evidence for/against, and falsification signals; not investment advice. |
| 个股投资亮点 | `layer2-stock-brief`, `layer2-stock-narrative-valuation` | partial | Use "关注点/亮点" wording, not "值得买"; use narrative valuation only when the user asks whether the story is supportable. |
| 热门个股榜单 | fin-data-query rankings plus `layer2-stock-brief` after the user selects a stock | partial | Can show returned rankings as market data only; no personalized recommendation or opportunity framing. |
| 行业/板块批判性分析 | `layer2-industry-brief` | launch | Use indicators, news, graph views, and same-boat viewpoints. |
| 行业/板块异动归因 | `layer2-industry-brief`, fin-graph anomalies, same-boat anomaly interpretation | launch | Strong fit for fin-graph plus same-boat. |
| 报告核心要点提炼 | `layer2-research-digest` | launch | Use report search and document detail. |
| 报告智能对话 | `layer2-research-digest` | partial | Works when report evidence can be retrieved; full-document chat may need stronger document session UX. |

### 研报数据平台

| Spreadsheet capability | Recommended route | Status | Notes |
|---|---|---|---|
| 报告核心要点提炼 | `layer2-research-digest` | launch | v1 core scenario. |
| 报告智能对话 | `layer2-research-digest` | partial | Bound answers to retrieved report chunks/details. |
| 智能插入投研图表 | `layer2-research-visuals` | launch | Structured market/event charts use authenticated evidence and WorkBuddy inline rendering with table fallback; report images require a stable verifiable source. |
| 机构观点横向对比 | `layer2-research-digest`, same-boat viewpoints | partial | Needs comparison output template and source normalization. |
| 热门行业/个股机构要点萃取 | `layer2-research-digest`, same-boat viewpoints | launch | Good candidate for a quick prompt if the time window is explicit. |

## Route Selection Rules

1. If the user names a company or ticker, start with `layer2-stock-brief`, unless the wording is specifically about an announcement, report, implied valuation, narrative, moat, overpricing, or rally review.
2. If the user asks "贵不贵", "估值透支了吗", "市场隐含什么预期", "为什么涨这么多/跌这么多", "主升浪怎么来的", or "这个故事能不能支撑", use `layer2-stock-narrative-valuation`.
3. If the user names an announcement, annual report, forecast, buyback, restructuring, or dividend, use `layer2-announcement-brief` first.
4. If the user asks "券商怎么看" or "研报有什么观点", use `layer2-research-digest`.
5. If the user asks about an industry, policy, regulator, or official meeting, prefer `layer2-industry-brief` or `layer2-policy-event-brief`.
6. If the user asks about 同舟投研, analyst interpretation, market news analysis, or sector viewpoints, include `same-boat`.
7. If a route is `partial`, state the missing coverage plainly and avoid publishing it as complete advice.

## Excluded Families

The package must not route to:

| Excluded family | Status | Reason |
|---|---|---|
| `layer2-sales-*` | excluded | Requires sales profile, sales RAG, strategy recommendation, or customer communication workflow data. |
| `layer2-care-*` | excluded | Requires private holdings, redemption, reassurance, or customer care state. |
| `layer2-pa-*` | excluded | Requires PA-specific profile, opportunity, strategy, or memory integrations. |
| customer profile workflows | excluded | Requires private identity/profile permissions. |
| sales RAG or strategy workflows | excluded | Requires non-public sales content and regulated recommendation controls. |
| personal holdings workflows | excluded | Requires user account holdings and consent model. |
| personal trade-history workflows | excluded | Requires user trades, behavioral data, and privacy controls. |
| suitability, allocation, or individualized trading advice | excluded | Requires separate regulated advisory design and approval. |

## Output Contract

Every route should produce:

- route name and evidence window when useful
- facts and source types first
- interpretation second
- missing data or unavailable capability clearly labeled
- limitation note and non-personal-advice boundary

Do not expose raw MCP JSON, backend IDs, raw SQL, physical tables, index scores, full document text, API keys, SMS codes, or full phone numbers.
