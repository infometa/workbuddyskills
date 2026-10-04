# Tool Reference

## `search`

对知识库进行关键词全文搜索。

- 必填：`q`，搜索关键词。
- 分页：`page` 默认 1，`size` 默认 10。
- 可选过滤：`min_score`、`id`、`title`、`category`、`database`、`is_open`。
- 主要返回：命中总数、标题、摘要、正文片段、URL、路径、文档 ID、分类、数据库、分片索引及相关性得分。

## `get_chunk`

使用 `id` 和从 0 开始的 `chunk_index` 获取一个文档片段。

## `get_chunks_range`

使用 `doc_id`、从 0 开始的 `start_chunk_index` 和大于 0 的 `count` 获取连续片段。适合补充搜索命中位置前后的上下文。

## `get_document_chunks`

按 `doc_id` 分页读取文档全部片段。`page` 默认 1，`size` 默认 10，单页最多 100 条。

## `get_document_detail`

使用 `doc_id` 获取文档的索引详情、元数据和全部片段。返回可能较大，仅在确有必要时调用。

## `sync_status`

只读查询当前知识库同步任务是否运行及其进度。该工具不会启动同步。
