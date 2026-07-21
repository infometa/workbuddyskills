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
