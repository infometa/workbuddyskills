# News Reference

Use for:

- 今日热点、通用新闻、行业新闻、主题新闻
- 某家公司最近新闻、利好利空、互动类消息
- 电话会、路演、业绩说明会、会议纪要
- 盘前策略、每日早报、交易预案

## Tools

### search_hot_news

- Use for high-attention or market-wide news.
- 今日热点 -> `query="今日热点", time_window="1d", limit=10`.
- 最近大事 -> use a topic keyword plus `time_window`.

### search_company_news

- Use for company-level news.
- Prefer `company` or `ticker` over a loose company-name-only `query`.
- Add `time_window` for "最近/近期".

### search_morning_trading

- Use for daily morning briefings, pre-market notes, and trading plans.
- Typical `query`: `盘前`, `早报`, `交易预案`.

### search_meeting_minutes

- Use for meeting minutes, earnings calls, roadshows, and transcript snippets.
- Prefer `company` or `ticker`, then add `query` for the discussed topic.
- Use `source_name` when the user cares about a speaker, attendee, or named participant.
- `content_type` maps to meeting type such as `业绩说明会`, `电话会`, `路演`.

### search_documents

- Use only when the user asks for general/industry news and no specific atomic tool fits.
- Prefer `doc_type="news"` and a clear `query` or `industry`.

## Parameters

- 跨市场公司新闻遵循宽召回优先：先确认公司与市场，首轮使用可靠公司名或标准代码加时间窗，不同时叠加 `query`、`source_name` 和 `content_type` 等多个窄过滤。
- 海外代码检索为空时可在总恢复预算内用可靠公司名去掉 `ticker` 重试一次；一次代码空结果不能证明该公司没有文档。
- `time_window`: use `1d` for today, `1w` for this week, `1m` or `1y` for recent meeting transcripts and company news.
- `source_name`: media/source/author filter.
- `content_type`: best-effort filter for news/event labels or meeting type; do not assume exact cross-index equivalence.
- `limit`: normally `5-10`; avoid large result dumps.
- 港股、美股等海外公司新闻来自当前已接入媒体集合，只能表述为“当前来源与时间窗下检索到”，不能承诺全量资讯覆盖。

## Few-Shot

### 用户: 今天有什么热点新闻？

- 读取: `references/news.md`
- 调用: `search_hot_news(query="今日热点", time_window="1d", limit=10)`
- 输出: 标题、发布时间、来源、简短摘要
- 限制: 不承诺覆盖所有新闻源或绝对实时

### 用户: 保隆科技最近有什么新闻？

- 读取: `references/news.md`
- 调用: `search_company_news(company="保隆科技", time_window="1m", limit=5)`
- 输出: 公司、标题、时间、来源、摘要
- 限制: 如果命中为空，说明当前过滤条件下未检索到

### 用户: 今天盘前怎么说？

- 读取: `references/news.md`
- 调用: `search_morning_trading(query="盘前", time_window="1d", limit=5)`
- 输出: 早报/预案标题、时间、作者/来源、提及方向
- 限制: 不把盘前观点写成确定投资建议

### 用户: 宁德时代最近电话会提到海外产能了吗？

- 读取: `references/news.md`
- 调用: `search_meeting_minutes(company="宁德时代", query="海外产能", time_window="1y", limit=5)`
- 如需详情: `get_document(doc_id=<chunk_id>, doc_type="meeting_minutes")`
- 输出: 会议名称、日期、发言人、命中片段摘要
- 限制: 当前返回的是片段级转录命中，不保证自动拼接整场会议上下文

## Common Mistakes

- 公告、新闻、研报是三个独立证据域。新闻只证明当前新闻来源的命中情况；分别保留各自返回的最新日期、来源和时间窗，不用新闻日期代表公告或研报日期。
- Do not call a search tool with empty parameters.
- Do not use company news as announcement original text.
- Do not describe meeting transcript snippets as verbatim full-meeting records unless `get_document` or multiple chunks confirm it.
- Do not fetch full text unless the user asks for details.
- For unsupported coverage and empty-result wording, also read `references/limitations.md`.
