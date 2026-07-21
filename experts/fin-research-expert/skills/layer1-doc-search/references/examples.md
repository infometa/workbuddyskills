# Combination Examples

Use this reference when the user question needs multiple doc-search families or doc-search plus another MCP.

## Few-Shot

### 用户: 今天新能源板块为什么大跌？

- 读取: `references/news.md`, `references/announcements-events.md`, and `layer1-fin-data/references/screening.md`
- 先查行情: use fin-data ranking/screening for sector or representative constituents
- 再查消息: `search_documents(query="新能源", doc_type="news", industry="新能源", time_window="1w", limit=5)`
- 如需事件: `search_normalized_events(industry="新能源", time_window="1w", limit=10)`
- 输出: 先给行情事实，再给可能因素
- 限制: 不把相关性写成确定因果

### 用户: 最近券商怎么看中际旭创？股价表现也带一下

- 读取: `references/research.md` and `layer1-fin-data/references/market.md`
- 研报: `search_research_reports(company="中际旭创", time_window="3m", limit=5)`
- 行情: use fin-data `query_data` or `get_latest_snapshot`
- 输出: 研报标题/券商/日期、观点共性、股价背景
- 限制: 不把研报观点写成投资建议

### 用户: 宁德时代最近公告和新闻有什么重要变化？

- 读取: `references/news.md`, `references/announcements-events.md`
- 公告: `search_announcements(company="宁德时代", time_window="1m", limit=5)`
- 新闻: `search_company_news(company="宁德时代", time_window="1m", limit=5)`
- 输出: 分为公告事项和新闻事项，按时间排序
- 限制: 公告和新闻来源边界要分开

### 用户: 白酒行业最近研究、新闻、估值一起看一下

- 读取: `references/research.md`, `references/news.md`, and `layer1-fin-data/references/macro_financial.md`
- 研报: `search_research_reports(industry="白酒", content_type="行业研究", time_window="3m", limit=5)`
- 新闻: `search_documents(query="白酒", doc_type="news", industry="白酒", time_window="1m", limit=5)`
- 估值: use fin-data `query_sector_valuation`
- 输出: 研究观点、近期事件、估值位置、边界说明
- 限制: 没有估值或研报结果时明确降级

## Ordering Rules

- For "为什么/影响/怎么看", collect factual evidence first, then explain cautiously.
- For "研报怎么看", research search comes before news search.
- For "公告说了什么", announcement search comes before event/news search.
- For "最近发生了什么", timeline tools are better than manually merging isolated searches.
- For investment-sensitive wording, empty-result caveats, and source-coverage caveats, also read `references/limitations.md`.
