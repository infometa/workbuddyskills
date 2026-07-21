---
name: layer1-same-boat
description: "Use for read-only Chinese investment research / 投研知识库 queries: 行业/板块/概念研究目录, 分析师资料, 研报观点, 市场要闻, 分析师解读, 行情异动归因, 行业观点, market news, analyst viewpoints, sector viewpoints."
---

# 投研内容查询

Use this skill when the user asks for structured read-only investment research content from the internal 投研/同舟 content database, even if they do not mention "Same Boat" by name.

Typical trigger phrases include:

- 投研知识库, 投研内容, 同舟投研, 研究目录, 行业目录, 板块目录, 概念目录
- 分析师资料, 分析师观点, 分析师解读, 研报观点, 行业观点, 板块观点
- 市场要闻, 要闻解读, 新闻解读, 行情异动, 异动归因, 异动详情
- 投研图表, 研报图片, 表格截图, 观点雷达, visual evidence
- investment research, analyst profile, analyst viewpoint, market news, market anomaly, sector viewpoint

Do not use this skill for natural-language routing, FinLLM AI search, strategy manager content, strategy performance, user login, follows, favorites, content saves, backend operations, uploads, ASR/TTS, or raw SQL execution.

User-facing outputs must label Same Boat content as retrieved research/news/viewpoint 证据, keep 来源 and time-window boundaries, and avoid investment-advice or stock-recommendation wording.

## Runtime Binding

This skill defines the Same Boat logical source contract; it does not declare a separate user-visible MCP connection.

- In WorkBuddy, call Same Boat tools through the single `tongzhou-fin-research` Connector. Runtime tool names use `same_boat__<tool>`, for example `same_boat__list_market_news`.
- In Codex and retained legacy clients, the same canonical tool may appear as a bare name or a client-qualified server/tool name. Match the canonical tool suffix and keep the Same Boat source label.
- Do not bypass an available `tongzhou-fin-research` Connector by selecting a similarly named global or deferred research tool.

## Routing

Choose the narrowest tool family first:

The table uses canonical tool suffixes for readability. Under the WorkBuddy Connector, prepend `same_boat__` when selecting the actual tool.

| User intent | Preferred tools |
|---|---|
| 当前暴露了哪些虚拟实体和字段、有哪些投研数据可查 | `get_schema` |
| 查行业、板块、概念、研究对象目录 | `list_research_sectors`, `search_research_sectors` |
| 查分析师资料、券商/头衔、研究领域、标签、奖项 | `search_analysts`, `get_analyst_profile` |
| 查市场要闻、新闻摘要、要闻列表、单条新闻、重要要闻筛选 | `list_market_news`, `get_market_news` |
| 查某条要闻下指定分析师的专业解读或白话解读 | `get_market_news_analysis` |
| 查行情异动、异动列表、异动原因、异动归因、风险和事件链 | `list_market_quotes`, `get_market_quote_analysis` |
| 查行业观点、板块观点、某行业下不同分析师观点、某分析师观点、观点详情 | `list_market_viewpoints`, `list_sector_viewpoints`, `list_analyst_viewpoints`, `get_market_viewpoint_detail` |
| 获取已定位要闻解读或行业观点中的图表、研报图片、表格截图与雷达证据 | `get_research_visual_evidence`; load `references/visual-evidence.md` |
| 为已定位的市场要闻、行情解读或行业观点补充可点击的小程序原文入口 | 优先保留列表/详情返回的文章级 URL；缺失时调用 `generate_content_url_link` |

## Required Rules

- Use MCP tools only. Never generate or pass raw SQL.
- Expose only virtual schema/tool names to users, not physical database tables or fields.
- Use stable entity IDs from tool results when making follow-up calls.
- If an upstream fin-graph resolver result is already available, prefer `source_ids.same_boat_sector_id` for Same Boat sector tools and keep `source_ids.same_boat_market_code` as market/index口径 evidence, not as a replacement sector id.
- Preserve `canonical_id`, `source_ids`, and `coverage_gaps` from the resolver result in the internal evidence ledger so Layer 2 can explain the research口径.
- Label `sector_id_system` explicitly when known: a Same Boat `sector_id` may equal `lycode`, but it remains the Same Boat sector id for Same Boat calls. Do not pass raw `lycode` as `sector_id` unless the resolver returned it as `source_ids.same_boat_sector_id`.
- For sector or analyst follow-up queries, resolve IDs first instead of guessing.
- For sector-named news or viewpoints such as "AI 算力有哪些同舟观点", first call `search_research_sectors(query=...)` or `list_research_sectors(...)`, then pass returned `sector_id` values into `list_market_news`, `list_market_viewpoints`, or `list_sector_viewpoints`.
- `list_sector_viewpoints` requires a stable `sector_id`, not a sector name. Do not pass the user's raw sector text as `sector_id`.
- For detail tools, call the list/search tool first and reuse returned IDs: `get_market_news(news_id=...)`, `get_market_news_analysis(news_id=..., analyst_id=...)`, `get_market_quote_analysis(quote_id=...)`, `get_market_viewpoint_detail(viewpoint_id=...)`.
- 只有用户明确需要图表、图片、表格截图，或视觉材料能直接支撑当前结论时，才在详情查询后调用 `get_research_visual_evidence`。普通文字回答不要调用该工具。
- 需要视觉证据时只加载 `references/visual-evidence.md`，不要在普通 Same Boat 查询中展开视觉契约。
- 用户明确需要源头复核、原文入口或 HTML 证据页时，先复用列表/详情返回的真实文章级 URL。入选的 Same Boat 内容没有文章级 URL 时，才调用 `generate_content_url_link`，并且只使用返回的 `url_link`：`content_type` 只能是 `market_news`、`market_quote` 或 `market_viewpoint`；前两类必须复用已返回的 `analyst_id`，观点类复用 `viewpoint_id`。
- 工具参数约束不变：market_news 和 market_quote 需要 analyst_id，market_viewpoint 不需要。
- `generate_content_url_link` 之前必须先完成列表/详情查询并复用原始 `news_id`、`quote_id` 或 `viewpoint_id`，不得猜 ID，也不要为了未入选页面的内容批量生成链接。
- 网关登录页、OAuth 授权页、控制台、服务/反馈页、搜索页和门户首页不是内容原文，绝不能作为源头复核链接。若直接 URL 与 `url_link` 都未返回，只标注“同舟要闻/同舟观点”等来源类型，不生成“同舟认证证据”“认证查看”或其他可点击替代入口。
- If the user asks "同舟怎么看/分析师怎么看/有没有观点" without naming an analyst, prefer list tools and summarize multiple returned items; only call analyst-specific detail after an `analyst_id` is present.
- If the user asks for important market news, headline impact, or 金融资讯影响力评级, use `list_market_news(importance_scores=[4, 5], limit=...)` when a high-importance filter is appropriate, then sort or group returned items by `importance_score`, `popularity_score`, and `publish_time`. Treat these as Same Boat returned scores, not as an independently calibrated rating model.
- If the user asks for 行业多空风向标、行业分数、看多看空理由 or sector sentiment, first resolve the sector with `search_research_sectors(query=...)`, then call `list_sector_viewpoints(sector_id=..., time_range="1w" or "1m", limit=...)`. Use returned `sentiment`, `sentiment_score`, `radar`, `summary`, `content`, `analyst`, `analyst_count`, and `publish_time` as the evidence base.
- Mention returned `publish_time` or the explicit filter window when summarizing time-sensitive content.
- If a tool returns an empty result, say the current query found no matching 投研内容. Do not invent content.
- Do not treat database, timeout, upstream, or validation errors as empty results. If an error code contains `DATABASE_UNAVAILABLE`, `QUERY_FAILED`, `QUERY_TIMEOUT`, `UPSTREAM_UNAVAILABLE`, or `UPSTREAM_FAILED`, state that the Same Boat source is temporarily unavailable or the filter needs correction.
- For market prices, full historical行情, macro data, or financial indicators, use the Fin Data source namespace instead of this skill (`fin_data__*` in the WorkBuddy Connector; `fin-data-query` in retained direct-server clients).
- Same Boat market news, market quotes, and viewpoints are 同舟投研内容 sources. Do not use them as substitutes for exchange market data, public announcements, or structured broker report retrieval.
- Keep investment wording descriptive and evidence-based. Do not turn content summaries into deterministic forecasts or direct recommendations.

## Output Shape

Prefer compact lists or tables. Include:

- title/name
- stable `entity_id`
- sector or analyst when available
- `publish_time` when available
- the relevant score or sentiment field when available: `importance_score`, `popularity_score`, `sentiment`, `sentiment_score`, and `radar`
- a real returned article-level URL or generated `url_link` only when source review is requested; otherwise keep a non-clickable source-type label
- visual evidence only when requested or directly useful: `schema_version`, selected `visuals`, exact `fallback_table`, and returned provenance fields
