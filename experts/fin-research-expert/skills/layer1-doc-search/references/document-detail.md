# Document Detail Reference

Use when:

- The user asks for 原文、正文、详情、具体内容、摘一段.
- A prior search result already produced `doc_id` and `doc_type`.
- The user selected one document from a list.
- One claim needs cross-checking against 2-5 already selected document summaries.
- The user asks what document sources and date ranges are actually covered.

Do not use this as the first step for broad search questions.

## Tool

### get_document

- Required: `doc_id`, `doc_type`.
- For research documents, treat `doc_id` as a short-lived opaque evidence reference. Pass it back unchanged; never guess, display, persist, decode, or transform it.
- `doc_type` must identify a single document family, e.g. `news`, `announcement`, `research`.
- `max_length` controls returned text length. Research detail defaults to `2000` characters and remains subject to the service-side cap.
- All supported document types use the same core fields: `summary`, `summary_status`, `content`, `content_kind`, `content_truncated`, and `metadata`.
- `summary` is stored metadata only. `content` is bounded detail evidence; use `content_kind` to distinguish research viewpoints, body excerpts, event analyses, and transcript excerpts.
- Research keeps the stored report viewpoint in `content` with `content_kind="research_viewpoint"`; it is not renamed to another top-level key.
- Announcement summaries come from stored announcement metadata. When unavailable, keep `summary_status="unavailable"` and use `content` only as a labeled body excerpt.

### get_document_summaries

- Required: `documents`, containing 2-5 items with the exact search-returned `evidence_ref` in `doc_id` and matching `doc_type`.
- Use only when one research step genuinely needs several selected summaries. For one item, keep using `get_document`.
- The response is partial-success capable: preserve each item's `success` or `error` state and do not discard successful siblings.
- A service-side cumulative summary budget still applies. Only existing summary fields and basic title/source/date context may be returned; never fall back to original text, source links, meeting transcripts, or report body content.

### get_document_source_coverage

- Optional: `source_types`; omit it only when the user truly wants the complete configured source overview.
- Returns source type, aggregate sample count, valid/missing date count, first date, last date, and statistics time.
- It does not return document IDs, lists, or physical index names. First/last dates do not prove continuous daily coverage.

## Flow

1. Search first with the domain-specific tool.
2. Present a compact list.
3. If the user selects one document, call `get_document`. If one claim needs 2-5 selected summaries, call `get_document_summaries` once instead of issuing repeated detail calls.
4. Use `summary` as the concise stored summary. Use `content` according to `content_kind`; research `content` is a **可见观点片段**, not the full report or complete PDF.
5. If content is empty or partial, preserve the returned title/source/date metadata and state the gap; never fill missing text from model memory.

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
- 调用: `get_document(doc_id="<research_doc_id>", doc_type="research", max_length=2000)`
- 输出: 标题、券商、日期、研报详情摘要（可见观点片段）
- 限制: 详情来自结构化字段和截断正文，不是完整研报、完整 PDF 或文章级源链接

### 用户: 把这三篇研报的摘要证据放在一起核验

- 前提: 三篇结果均来自当前用户刚完成的搜索，并带 `evidence_ref` 和明确 `doc_type`
- 调用: `get_document_summaries(documents=[{"doc_id":"<ref1>","doc_type":"research"},{"doc_id":"<ref2>","doc_type":"research"},{"doc_id":"<ref3>","doc_type":"research"}], max_length=800)`
- 输出: 按篇列出标题、来源、日期、已有摘要和失败项
- 限制: 最多 5 篇；只展示摘要，不读取原文、逐字稿或研报正文

### 用户: 研报、公告和新闻分别覆盖到什么时候？

- 调用: `get_document_source_coverage(source_types=["research","announcement","news"])`
- 输出: 每类来源的样本数、首末日期、缺失日期数及统计时间
- 限制: 只说明聚合覆盖，不把首末日期之间写成连续完整覆盖

## Common Mistakes

- Do not guess `doc_id`.
- Do not call `get_document` with `doc_type="all"`.
- Do not fetch body text for every search result.
- Do not split 2-5 selected documents into repeated single calls when `get_document_summaries` is available.
- Do not pass raw IDs, stale references, another user's references, or more than 5 items to `get_document_summaries`.
- Do not present batch summaries as original text or use body fields to fill a missing summary.
- Do not say “已读取完整研报”“已阅读全文” or imply access to the complete PDF when only sanitized detail content was returned.
- Do not expose backend index names, internal IDs, or opaque `doc_id` values in the answer.
- For content truncation and source caveats, also read `references/limitations.md`.
