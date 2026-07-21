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

### search_documents

- Use `search_documents(doc_type="research", source_set="research", ...)` only for unified-entry or mixed retrieval.
- It routes to structured research search, but precise company/industry fields are still preferred.

### get_document

- Use after a research result is selected and the user wants detail text or a longer excerpt.

## Parameters

- `time_window`: company research can use `1y`; broad research should usually stay within `3m`.
- Long windows such as `1y` are valid only when the call is scoped by `company`, `ticker`, `industry`, `content_type`, or `source_name`; a query-only call is treated as broad retrieval.
- If another subtask says 最近 N 个交易日, do not apply that window to research reports unless the user explicitly asks for reports from those days.
- 今天/本周/本月 for reports should be converted to explicit dates or an equivalent short `time_window`, then surfaced in the answer.
- `source_name`: broker name filter.
- `content_type`: common values include `公司研究`, `行业研究`, `策略研究`, `宏观经济`.
- 公司身份解析支持 A 股、港股、美股和英国市场的主数据。优先复用已解析的标准代码，不要自行猜测或手工补零。
- 港股研报源可能混用 4/5 位代码，美股可能混用交易所后缀或供应商格式；服务端会做代码变体召回并在代码零结果时使用标题全文索引回退。
- 海外公司 scoped search 成功但结果为空时，仍应用可靠公司名去掉 `ticker` 重试一次；不能由单一代码格式的空结果推断“没有研报”。
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
- 调用: `search_research_reports(company="康哲药业", ticker="0867.HK", time_window="1y", limit=10)`
- 若 scoped 结果为空: 保留可靠公司名，去掉 `ticker` 重试一次
- 输出: 标题、机构、发布日期、报告类型、短摘要
- 限制: 港股代码可能存在 4/5 位及供应商后缀差异，不能把一次代码空结果写成“没有研报”

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

- Do not send company research requests to generic news search first.
- Do not treat `INVALID_BROAD_TIME_RANGE` / `MISSING_RESEARCH_FILTERS` as an empty result.
- Do not infer "no reports in the past year" from a query-only call. Only say no matching reports were retrieved after a successful scoped `company`/`ticker` or `industry` search returns an empty `documents` list.
- Do not expose report chunk IDs, internal ES indices, scores, or backend routing details.
- Do not paste long copyrighted excerpts; summarize briefly and cite title/source/date.
- For source coverage and detail-text caveats, also read `references/limitations.md`.
