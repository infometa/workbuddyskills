---
name: layer1-doc-search
description: "Use when you need structured retrieval for news, company news, events, announcements, research reports, meeting minutes, morning briefings, timelines, or document details from the Doc Search source namespace."
---

# Doc Search

Use this skill for read-only document retrieval from the Doc Search source namespace.

Do not use this skill for structured market prices, financial time series, trading-strategy backtests, direct recommendations, or future event schedules. Descriptive event-level backtest tools in this skill are allowed only for retrieved historical event evidence.

## Runtime Binding

This skill defines the Doc Search logical source contract; it does not declare a separate user-visible MCP connection.

- In WorkBuddy, call Doc Search tools through the single `tongzhou-fin-research` Connector. Runtime tool names use `doc_search__<tool>`, for example `doc_search__search_announcements`.
- In Codex and retained legacy clients, the same canonical tool may appear as a bare name or a client-qualified server/tool name. Match the canonical tool suffix and keep the Doc Search source label.
- Do not bypass an available `tongzhou-fin-research` Connector by selecting similarly named global search tools such as `search_hot_news` or `search_company_news`.

## Progressive References

Load only the reference needed for the current question:

- `references/news.md`: general news, company news, hot news, morning briefings
- `references/announcements-events.md`: announcements, structured events, normalized events, entity timelines
- `references/research.md`: company research, industry research, strategy research, broker views
- `references/document-detail.md`: single/bounded-batch detail retrieval and source coverage statistics
- `references/examples.md`: cross-domain and cross-MCP few-shot routing examples
- `references/limitations.md`: source coverage, realtime wording, empty results, internal-field boundaries

Read this skill's `references/<name>.md` file before filling detailed tool parameters.

For combination queries, read multiple references. Example: "今天新能源为什么大跌" may need `references/news.md`, `references/announcements-events.md`, and `layer1-fin-data/references/screening.md`.

## Routing

Choose the narrowest retrieval family first:

The table uses canonical tool suffixes for readability. Under the WorkBuddy Connector, prepend `doc_search__` when selecting the actual tool.

| User intent | Read reference | Preferred tools |
|---|---|---|
| 今日热点、通用新闻、行业新闻 | `references/news.md` | `search_hot_news`, `search_documents` |
| 公司新闻、公司利好利空、互动新闻 | `references/news.md` | `search_company_news` |
| 盘前预案、每日早报、交易计划 | `references/news.md` | `search_morning_trading` |
| 电话会、路演、业绩说明会、会议纪要片段 | `references/news.md` | `search_meeting_minutes`, `get_document` |
| 公司事件、行业事件、业绩预告、回购、质押 | `references/announcements-events.md` | `search_events` |
| 历史相似事件、事件级回测、事件后平均走势 | `references/announcements-events.md` | `search_backtested_events`, `get_event_backtest`, `aggregate_similar_event_backtest` |
| 上市公司公告、公告原文、公告类型筛选 | `references/announcements-events.md` | `search_announcements`, `get_document` |
| 最近发生了什么、事件时间线、消息面回放 | `references/announcements-events.md` | `search_normalized_events`, `get_entity_event_timeline` |
| 个股研报、行业研报、策略研究、券商怎么看 | `references/research.md` | `search_research_reports` |
| 某一上市地研报覆盖数、映射缺口 | `references/research.md` | `get_research_coverage` |
| 用户选中某篇并要详情、正文摘要、可见内容片段 | `references/document-detail.md` | `get_document` |
| 同一结论需要核验 2-5 篇已选证据摘要 | `references/document-detail.md` | `get_document_summaries` |
| 文档库样本量、首末日期、来源时间范围 | `references/document-detail.md` | `get_document_source_coverage` |
| 不确定 `content_type` / `source_set` 取值范围 | `references/limitations.md` | `list_categories` |
| 复杂组合、不确定问法、跨 MCP 解释 | `references/examples.md` | combine the relevant tools |
| 空结果、覆盖范围、实时性、内部字段边界 | `references/limitations.md` | no retrieval tool by itself |

## Required Rules

- Prefer specific tools over `search_documents` when the content type is clear.
- 空召回不是公司事实：只有业务调用成功且目标列表为空时才标记 `empty`，并同时说明公司/主题、文档类型、来源范围和时间窗。
- 参数错误不是空召回。对可修正的 scope、时间窗或字段错误，先按工具合同修正；一个证据任务最多两次恢复，依次只做身份规范化、拆分文档类型、放宽一个过滤或使用同证据域的声明式 fallback。
- 非空但缺少标题、日期、来源或用户要求字段时标记 `partial`，保留已返回文档并列出缺口，不因一个字段缺失丢弃全部结果。
- 超时、服务失败、协议错误和授权要求分别标记 `error` / `auth_required`；不得把错误写成空召回，也不得切换到新闻、同舟观点或模型记忆伪装成公告/研报命中。
- Every search call must include at least one non-empty narrowing signal such as `query`, `ticker`, `company`, `industry`, `content_type`, `source_name`, `time_window`, or date range.
- Resolve relative time before calling tools: 今天/昨日/本周/本月/最近N天 must map to a supported `time_window`, `days`, or explicit `start_date`/`end_date`; include the actual date range in the answer.
- For "今天有什么新闻/热点", use `search_hot_news(query="今日热点", time_window="1d", limit=10)` instead of an empty query.
- For company research reports, pass the entity through `company` and/or `ticker` in `search_research_reports`; do not put a company name only in `query` when using a long window such as `1y`.
- Each research call accepts one company/listing. Split explicit company/ticker lists into separately labeled calls; `MULTI_ENTITY_RESEARCH_UNSUPPORTED` is a parameter error, not an empty result.
- For a listing-specific research question, preserve the resolved `ticker`, `market`, and `scope="listing"`; do not silently remove `ticker` or replace listing results with issuer-title matches.
- If issuer-wide coverage is useful, make a separate `scope="issuer"` call and label it as a broader issuer result.
- Normal research calls use `limit=5-10`; the hard single-call maximum is 20.
- A listing search may return a short-lived `continuation_ref`. When more evidence is needed, make the next call with only that reference; the gateway restores the original filters. Continue only while `continuation_status="available"`, and stop once enough evidence is collected or the status is `complete`, `limit_reached`, or `unavailable`. Treat `limit_reached` / `unavailable` as bounded retrieval rather than exhaustive coverage. Older responses may omit `continuation_status`; if they also omit the reference, stop without claiming completeness. Never display, decode, construct, share, or persist the reference.
- The configured announcement source is CNINFO-oriented and does not include native HKEX disclosures. A Hong Kong announcement empty result is a source-coverage gap, not evidence that the company made no disclosure.
- Return title, date/time, source, and short summary first. Do not fetch long body text unless the user asks for details.
- Treat `snippet` as search-match context, `summary` as a stored source summary, and `content` as bounded detail evidence. Never relabel one as another.
- In `get_document`, read `content_kind` before using `content`: `research_viewpoint`, `body_excerpt`, `event_analysis`, and `transcript_excerpt` have different evidence meanings. Type-specific fields are under `metadata`.
- `summary_status="unavailable"` means no stored summary was returned; `error` means the summary source failed. Do not fill either state from `content` or model memory.
- Use `get_document` only after a search result provides `doc_id` and a clear `doc_type`. For research results, treat `doc_id` as a short-lived opaque evidence reference: pass it back unchanged, never display or persist it, and rerun the search if it expires.
- Use `get_document_summaries` only for 2-5 explicitly selected search results needed by one evidence task. Pass each returned `evidence_ref` with its exact `doc_type`; never construct, persist, mix across users, or use batch summaries as an export path. This tool returns only stored summaries and must not return or reconstruct original text.
- Use `get_document_source_coverage` only when the user asks about source coverage, data time range, or whether an empty result may be a coverage gap. Treat its first/last dates as an aggregate snapshot, not proof of continuous daily coverage.
- Search results are candidates for selection. For research, call `get_document` only for `1-3` selected reports needed by the user's request or claim verification; never expand every result by default.
- Do not expose internal collection names, retrieval scores, request plans, or backend routing details to users.
- If no result is returned, say no matching documents were retrieved under the current filters. Do not invent events or reports.
- Event backtest tools return descriptive historical samples only. Do not present them as a future prediction, strategy backtest, target price, or recommendation.
- If a multi-part user question asks for document evidence plus another data domain, finish the document summary and then continue with the other domain before finalizing.
- Do not answer "will query / please wait" after tool use. Continue calling the needed tool or provide the completed answer.
- Treat a non-empty `documents` or `events` list as retrieved evidence. Summarize those items; do not call it an empty result.
- For coverage, freshness, timeline, and content-type caveats, read `references/limitations.md`.

## Output Shape

Prefer compact lists or tables. Include:

- title
- entity/company/industry when applicable
- publish/release date
- source or broker
- short evidence summary
- limitation or data-source caveat when relevant
