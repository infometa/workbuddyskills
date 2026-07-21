# Document Detail Reference

Use when:

- The user asks for 原文、正文、详情、具体内容、摘一段.
- A prior search result already produced `doc_id` and `doc_type`.
- The user selected one document from a list.

Do not use this as the first step for broad search questions.

## Tool

### get_document

- Required: `doc_id`, `doc_type`.
- `doc_type` must identify a single document family, e.g. `news`, `announcement`, `research`.
- `max_length` controls returned text length; keep it modest unless the user asks for more.

## Flow

1. Search first with the domain-specific tool.
2. Present a compact list.
3. If the user asks for details, call `get_document`.
4. Summarize or excerpt the returned sanitized content.

## Few-Shot

### 用户: 第一篇公告展开看看

- 前提: 上一轮 `search_announcements` 返回了第一篇的 `doc_id`
- 读取: `references/document-detail.md`
- 调用: `get_document(doc_id="<first_doc_id>", doc_type="announcement", max_length=2000)`
- 输出: 标题、发布日期、公告类型、正文摘要
- 限制: 不输出完整长篇公告

### 用户: 这篇研报具体讲了什么？

- 前提: 已知研报 `doc_id`
- 读取: `references/document-detail.md`
- 调用: `get_document(doc_id="<report_id>", doc_type="research", max_length=2000)`
- 输出: 标题、券商、日期、核心段落摘要
- 限制: 研报详情来自结构化字段和截断正文，不承诺完整 PDF 全文

## Common Mistakes

- Do not guess `doc_id`.
- Do not call `get_document` with `doc_type="all"`.
- Do not fetch body text for every search result.
- Do not expose backend index names or internal IDs beyond what is needed to identify the selected document.
- For content truncation and source caveats, also read `references/limitations.md`.
