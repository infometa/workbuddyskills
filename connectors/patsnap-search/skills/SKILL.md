---
name: patsnap-search
description: Search Patsnap patent and literature data through the Patsnap MCP connector.
---

# Patsnap Patent & Literature Search

Use this connector when the user asks to search Patsnap global patent and literature databases, retrieve patent or academic paper intelligence, or fetch Markdown-formatted patent/literature details.

当用户需要检索智慧芽全球专利数据库和文献库、获取专利或论文情报，或拉取专利/文献 Markdown 详情时，使用此 Connector。

Available tools:

- `patsnap_search`: Professional patent and academic paper search tool. It supports natural-language queries, semantic search, keyword search, BM25-based text retrieval, and filters such as assignee, IPC classification, date, and jurisdiction.
- `patsnap_fetch`: Fetch Markdown-formatted patent or literature content by URL, or by publication number for patents. Patent results may include bibliographic details, claims, descriptions, and drawings; literature results provide basic abstract metadata.

工具说明：

- `patsnap_search`：专业的专利和期刊论文检索工具，支持自然语言查询、语义搜索、关键词检索、BM25 文本检索，以及申请人、IPC 分类、日期、受理局等过滤条件。
- `patsnap_fetch`：专业的专利和论文内容获取工具，支持通过 URL 获取专利或文献 Markdown 内容，也支持通过公开号获取专利内容。专利数据可包含著录项、权利要求、说明书和附图；论文数据提供基础摘要元信息。

When calling tools, follow the MCP tool schemas exposed by the server. Do not invent unsupported filters or identifiers.

调用工具时，以 MCP Server 暴露的 tool schema 为准，不要编造未支持的过滤条件或标识符。

Authentication:

- This connector uses a user-provided Patsnap API key.
- If authentication fails or the API key expires, ask the user to regenerate or update their Patsnap API key in WorkBuddy.

认证说明：

- 此 Connector 使用用户自填的智慧芽 API Key。
- 如果认证失败或 API Key 失效，请提醒用户在 WorkBuddy 中重新填写或更新智慧芽 API Key。
