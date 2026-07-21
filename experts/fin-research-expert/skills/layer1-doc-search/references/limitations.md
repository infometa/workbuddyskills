# Limitations

## Coverage

- doc-search is primarily an Elasticsearch retrieval service.
- It does not guarantee coverage of every news source, announcement source, broker report, or all historical documents.
- The configured announcement source is currently CNINFO-oriented and does not include native HKEX disclosures.
- Structured report identity resolution supports A-share, Hong Kong, US, and UK security masters, but overseas vendor codes can still be heterogeneous; empty overseas results require one company-name retry.
- Company alias resolution may use ODS company metadata. If ODS is unavailable, retrieval may fall back to text matching and become less precise.
- Mixed retrieval can be wider because different indices have different fields.

## Freshness

- Do not promise absolute realtime news coverage.
- For "today" questions, mention that results are based on documents retrieved under the requested filters and time window.
- Use returned publish/release dates in the answer.

## Timeline Boundaries

- `search_normalized_events` and `get_entity_event_timeline` are historical event views.
- They are not future schedule/calendar tools.
- Multiple reports about the same event may still appear separately.

## Content Boundaries

- `content_type` is strongest on announcements and research. On news/events/morning briefings it is best-effort.
- Research search prioritizes structured report metadata and summaries. It is not guaranteed full PDF paragraph retrieval.
- `get_document` returns sanitized and truncated content.
- Avoid long verbatim excerpts; summarize title/source/date and key points.

## Discovering Filter Values

### list_categories

- Use when uncertain about which `content_type` / `source_set` values a given `doc_type` supports.
- `doc_type`: `all` | `news` | `announcement` | `research` | `event`.
- Inspect the returned enums before filling search parameters; do not guess `content_type`.
- This is a discovery tool only; it never returns documents.

## Internal Fields

Do not expose:

- ES index names
- raw query DSL
- internal scores
- backend routing details
- physical storage names
- long raw document IDs unless the user needs to select a returned document

## Empty Results

Say:

- "当前筛选条件下未检索到相关文档。"
- Include the key filters: company/industry/query/time window/content type.
- Suggest one narrower or broader retry if useful.
- For overseas company research, retry once with a reliable company name and no ticker before declaring an empty sample.
- For Hong Kong announcements, say the native HKEX announcement source is not covered instead of saying the company made no announcement.

Do not invent missing news, events, announcements, or research reports.

## Few-Shot

### 用户: 你确定这是全部公告吗？

- 回答口径: 不承诺全市场绝对完整覆盖；说明这是当前 doc-search 在指定公司和时间窗下检索到的公告结果。
- 如需补充: 可放宽 `time_window` 或增加 `content_type`/`source_name` 约束重新检索。

### 用户: 下周这家公司有什么事件？

- 回答口径: 当前时间线工具是历史事件回放，不是未来日程表。
- 可替代: 检索近期公告或新闻，说明未覆盖未来事件日历。
