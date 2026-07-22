# Announcements And Events Reference

Use for:

- 上市公司公告、公告原文、公告类型筛选
- 公司事件、行业事件、业绩预告、回购、质押、股权激励
- 最近发生了什么、消息面时间线、事件回放

## Tools

### search_announcements

- Use for original listed-company announcements.
- Prefer `company` or `ticker`.
- Use `content_type` for announcement type, e.g. `业绩预告`, `股权激励`, `股东会`, `股权变动`.
- 当前公告源以巨潮资讯为主，不包含港交所披露易原生公告。港股检索为空只能说明当前公告源未覆盖，不能表述为公司没有公告。

### search_events

- Use for structured events, including company events and market/industry events.
- Suitable for `业绩快报`, `回购`, `质押`, `政策事件`, `行业事件`.
- This is not a replacement for announcement original text.

### search_backtested_events

- Use when the page needs historical comparable events with valid event-level backtest fields.
- Pass at least one of `query`, `company`, `ticker`, `industry`, or `event_type`.
- Returned `backtest` is compact and public-facing; do not expect raw `back_test_result`.

### get_event_backtest

- Use after `search_backtested_events` or `search_events` returns a `doc_id` and the page needs one event's backtest detail.
- Returns valid windows only. `60d` is the v1 proxy for roughly 3 months.

### aggregate_similar_event_backtest

- Use for event-factor playbooks that need historical similar-event statistics.
- Default windows are `3d`, `5d`, `7d`, and `20d`.
- Request `60d` explicitly only when a long-horizon / roughly three-month view is needed, and treat it as supplemental unless it has enough valid samples.
- Treat the output as retrieval-based descriptive statistics, not a prediction.

### search_normalized_events

- Use to combine news, announcements, and structured events into a normalized event list.
- Good for "把最近消息面整理一下".
- This is a historical event view, not a future schedule source.

### get_entity_event_timeline

- Use for entity-centric timeline questions.
- Must pass at least one of `ticker`, `company`, or `industry`.
- Default time window is `1m`.

### get_document

- Use after `search_announcements` returns a `doc_id` and the user wants original/detail text.

## Parameters

- 跨市场公司检索遵循宽召回优先：先确认公司、市场和标准代码，首轮只保留公司/代码、时间窗和用户明确要求的公告类型，不叠加来源名、宽泛主题词等额外过滤。
- 港股、美股代码存在供应商变体时，一次代码空结果不能证明该公司没有文档；仅在当前公告源实际支持该市场时，才用可靠公司名去掉 `ticker` 重试一次。
- `time_window`: `1m` for recent events/announcements; use explicit dates for reporting periods.
- 今天 -> `time_window="1d"` or explicit same-day `start_date`/`end_date`; 本周/本月 -> explicit date range; 最近 N 天 -> `days=N`.
- Do not use trading-day phrases from a market-data subtask as document date filters unless the user explicitly applies that time limit to documents.
- `content_type`: strongest on announcements; best-effort on event/news indices.
- `limit`: use `5-10` for search, up to `20` for timeline if the user asks for a fuller history.
- 回测窗口: event backtest tools default to `3d`, `5d`, `7d`, and `20d`; label `20d` as “约 1 个月 / 20 个交易日”. `60d` is optional and should be requested only for long-horizon review; label it as “约 3 个月 / 60 个交易日” when valid.

## Few-Shot

### 用户: 宁德时代最新公告说了什么？

- 读取: `references/announcements-events.md`
- 调用: `search_announcements(company="宁德时代", time_window="1m", limit=5)`
- 如用户要原文: 再调用 `get_document(doc_id=..., doc_type="announcement")`
- 输出: 标题、发布日期、公告类型、摘要
- 限制: 不把事件索引结果写成公告原文

### 用户: 腾亚精工最近发生了什么？

- 读取: `references/announcements-events.md`
- 调用: `get_entity_event_timeline(company="腾亚精工", time_window="1m", limit=20)`
- 输出: 按时间列出事件、来源类型、摘要
- 限制: 这是历史事件时间线，不是未来日程表

### 用户: 这个事件有没有历史相似案例和事件后表现？

- 读取: `references/announcements-events.md`
- 调用: `aggregate_similar_event_backtest(query="<事件关键词>", industry="<已解析行业>", event_type="<事件类型>", windows=["3d","5d","7d","20d"], limit=20)`
- 如用户明确需要约 3 个月表现，或页面长周期模块需要补充: 再调用 `aggregate_similar_event_backtest(..., windows=["60d"], limit=20)`，不要因为 60d 缺失丢弃普通 3/5/7/20 日样本。
- 输出: 样本数、有效样本数、各窗口平均收益/中位数/胜率、样本事件列表
- 限制: 样本不足时只能写“样本不足”，不要编造收益、胜率或相似度

### 用户: 最近有哪些公司披露业绩预告？

- 读取: `references/announcements-events.md`
- 调用: `search_announcements(query="业绩预告", content_type="业绩预告", time_window="1m", limit=10)`
- 输出: 公司、标题、公告日期、来源
- 限制: 如果用户指定公司，优先传 `company`

## Common Mistakes

- 公告、新闻、研报是三个独立证据域。`search_events` 或新闻命中只能作为事件线索，不能填补公告原文；每个域分别保留各自返回的最新日期、来源和覆盖缺口。
- Do not use `search_events` when the user explicitly asks for announcement original text.
- Do not present a Hong Kong announcement empty result as evidence that no disclosure exists; state the native HKEX source gap.
- Do not promise future schedules from timeline tools.
- Do not merge multiple event sources into one certain causal conclusion.
- Do not mix event_info company/stock backtests with industry-index reactions unless the source label is explicit.
- For coverage and timeline caveats, also read `references/limitations.md`.
