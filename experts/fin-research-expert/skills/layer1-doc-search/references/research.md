# Research Reference

Use for:

- 个股研报、行业研报、策略研究、宏观研究
- 券商怎么看、机构观点、分析师观点
- 多篇研报共识、分歧和近期研究主题

## Tools

### search_research_reports

- Preferred tool for structured research retrieval.
- Use `company` or `ticker` for company research.
- For company-level questions such as "赛力斯近一年有没有研报", put the entity in `company` and/or `ticker`; do not put the company name only in `query` with `time_window="1y"`.
- Use `industry` and `content_type="行业研究"` for industry research.
- Use `content_type="策略研究"` or `content_type="宏观经济"` for broad strategy/macro research.
- Single-call `limit` max is `20`; normal use `5-10`.
- Each call accepts one company/listing. Do not send `FCX OR RIO`, comma-separated companies, or ticker lists; split them into independent calls. `MULTI_ENTITY_RESEARCH_UNSUPPORTED` is a parameter error, not an empty result.
- Exact listing searches may return a short-lived `continuation_ref`. Request another page only when the current evidence task needs it, and send only that reference on the next call because the gateway restores the original filters. Continue while `continuation_status="available"`; `complete` means the source page chain ended, while `limit_reached` or `unavailable` means the current retrieval is bounded and must not be described as exhaustive. Older responses without `continuation_status` remain valid; a missing reference means stop and avoid a completeness claim.
- Do not use continuation for issuer, industry, category, source-only, or free-text traversal.

### get_research_coverage

- Use only for bounded aggregate coverage of one explicit listing and market.
- It returns total and yearly sample counts, first/last dates, mapped/ambiguous counts, and a gap state, never report IDs or a report list.
- `mapping_incomplete` means the sidecar has not reconciled every source sample; it is not evidence that reports do not exist.

### search_documents

- Use `search_documents(doc_type="research", source_set="research", ...)` only for unified-entry or mixed retrieval.
- It routes to structured research search, but precise company/industry fields are still preferred.

### get_document

- Use after a research result is selected and the user wants detail text or a longer excerpt.
- The gateway-provided `doc_id` is an opaque, subject-bound evidence reference rather than a report database ID. Pass it back unchanged, do not expose it in the answer, and rerun `search_research_reports` when it expires.
- Search results are a candidate list. Expand only the `1-3` reports selected by the user or required to verify a specific claim; do not fetch every report by default.
- Returned content is a sanitized **研报详情摘要** / **可见观点片段**, normally requested with `max_length=2000`. It is not the full report, complete PDF, or a guaranteed article-level source link.
- If the detail is empty or partial, retain the visible metadata and explain the gap instead of completing the report from model memory.

## Parameters

- 公司研报遵循宽召回优先：先确认公司、市场和标准代码；首轮使用 `company` 和可确认的 `ticker` 加时间窗，不再叠加无必要的 `query`、`source_name` 或行业过滤。
- `time_window`: company research can use `1y`; broad research should usually stay within `3m`.
- Long windows such as `1y` are valid only when the call is scoped by `company`, `ticker`, `industry`, `content_type`, or `source_name`; a query-only call is treated as broad retrieval.
- If another subtask says 最近 N 个交易日, do not apply that window to research reports unless the user explicitly asks for reports from those days.
- 今天/本周/本月 for reports should be converted to explicit dates or an equivalent short `time_window`, then surfaced in the answer.
- `source_name`: broker name filter.
- `content_type`: common values include `公司研究`, `行业研究`, `策略研究`, `宏观经济`.
- 公司身份解析支持 A 股、港股、美股和英国市场的主数据。优先复用已解析的标准代码，不要自行猜测或手工补零。
- 查询某一上市地时显式传 `ticker`、`market` 和 `scope="listing"`。服务端只使用该市场的安全代码变体，不会用标题同名结果替代目标上市地。
- 查询发行人整体覆盖时传 `company` 和 `scope="issuer"`；发行人范围可以补充公司标题召回，但结果只能描述为发行人相关研报，不能冒充某一上市地的精确覆盖。
- 精确上市地结果为空只表示当前来源与时间窗未命中。需要发行人整体覆盖时必须另行说明并使用 issuer scope，不能静默放宽。
- For broad queries without `company` or `industry`, keep the time window narrow.
- If the tool returns `INVALID_BROAD_TIME_RANGE` or `MISSING_RESEARCH_FILTERS`, treat it as a parameter/scope error. Retry with `company`/`ticker` for company research or narrow the time window/type for broad research; do not report it as "no research reports found".

## Few-Shot

### 用户: 贵州茅台最近有哪些研报？

- 读取: `references/research.md`
- 调用: `search_research_reports(company="贵州茅台", time_window="1y", limit=5)`
- 输出: 标题、券商、发布日期、研报类型、摘要
- 限制: 不把行业周报误写成公司专属研报

### 用户: 赛力斯去年一年都没有研报吗？

- 读取: `references/research.md`
- 先解析公司身份；如能拿到代码，调用: `search_research_reports(company="赛力斯", ticker="601127.SH", time_window="1y", limit=10)`
- 不要调用: `search_research_reports(query="赛力斯", time_window="1y", limit=10)`
- 如果返回 `INVALID_BROAD_TIME_RANGE`，说明这次调用没有按公司维度收窄，应重试 scoped search；不是研报未命中

### 用户: 康哲药业最近一年有公司研报吗？

- 读取: `references/research.md`
- 精确港股调用: `search_research_reports(company="康哲药业", ticker="0867.HK", market="hk_stock", scope="listing", time_window="1y", limit=10)`
- 如用户要发行人整体覆盖，另行调用: `search_research_reports(company="康哲药业", scope="issuer", time_window="1y", limit=10)`
- 输出: 标题、机构、发布日期、报告类型、短摘要
- 限制: 不手工改供应商代码，不静默去掉 ticker，也不把发行人结果写成港股上市地精确结果

### 用户: 白酒行业最近有哪些行业研究？

- 读取: `references/research.md`
- 调用: `search_research_reports(industry="白酒", content_type="行业研究", time_window="3m", limit=5)`
- 输出: 标题、券商、日期、核心摘要
- 限制: 只提炼可见研报观点，不替分析师做确定结论

### 用户: 最近策略研究在关注什么？

- 读取: `references/research.md`
- 调用: `search_research_reports(query="策略", content_type="策略研究", time_window="1m", limit=10)`
- 输出: 近期策略标题、机构、发布时间、共同主题
- 限制: 不把样本内观点写成全市场共识

## Common Mistakes

- 公告、新闻、研报是三个独立证据域。研报命中不能替代公告或新闻；分别保留各自返回的最新日期、机构/来源与时间窗。
- Do not send company research requests to generic news search first.
- Do not treat `INVALID_BROAD_TIME_RANGE` / `MISSING_RESEARCH_FILTERS` as an empty result.
- Do not treat `MULTI_ENTITY_RESEARCH_UNSUPPORTED` as an empty result; split the requested companies/listings and label each result separately.
- Do not infer "no reports in the past year" from a query-only call. Only say no matching reports were retrieved after a successful scoped `company`/`ticker` or `industry` search returns an empty `documents` list.
- Do not silently change a listing-scoped question into issuer scope. If issuer coverage is useful, label it as a separate broader retrieval.
- Do not expose report chunk IDs, internal ES indices, scores, or backend routing details.
- Do not display, persist, share, decode, or construct `continuation_ref`; it is a one-time traversal capability bound to the current subject and query.
- Do not paste long copyrighted excerpts; summarize briefly and cite title/source/date.
- Do not claim “已读取完整研报” or “已阅读全文” when `get_document` returned only sanitized detail content.
- For source coverage and detail-text caveats, also read `references/limitations.md`.
