# Industry Graph And Public Factors Reference

Read this for 行业图谱 topics, public nodes, public factor framework, factor evidence, and metric values.

For safety boundaries, also read `references/limitations.md`.

## Subject Discovery

Use `list_supported_subjects(index_type="industry_III_index", limit=...)` to discover industry graph subjects.

Use returned subject/category names for:
- `get_graph_overview`
- `get_industry_graph`
- `query_graph_nodes`
- `get_graph_node_brief`
- public factor tools

Do not put Same Boat sector ids, fin-data basket ids, or raw user text directly into industry graph `subject`/`category` when resolver/list tools have not confirmed the graph subject.

## Tools

### `get_graph_overview` / `get_industry_graph`

Use for industry graph summary and restricted outline.
- `subject` or `category`: returned graph subject
- `graph_type`: optional
- `outline_limit`: 1-50

### `query_graph_nodes`

Use for public node positioning by name.
- `category`: returned graph subject
- `keyword`
- `node_type`: e.g. `AnalyticalDimension`, `DataDimension`
- `limit`: 1-50

### `get_graph_node_brief`

Use only after node discovery.
- `subject`
- `node_name`
- `node_type`: default `AnalyticalDimension`

Only whitelisted node families return short public briefs.

### `get_public_factor_framework`

Use for Playbook factor cards, six-factor explanations, and public attribution.
- `subject`
- `graph_type`
- `factor_keywords`
- `limit`: 1-30

### `get_factor_evidence_panel`

Use for factor evidence panels. It returns public summaries, linked data dimensions, available metric names, and evidence boundaries.
- `subject`
- `factor_names`: max 12
- `graph_type`

### `get_factor_metric_values`

Use when a factor card needs public metric values.
- `subject`
- `factor_names`: max 12
- `metric_keywords`
- `max_points_per_metric`: 1-24
- `limit`: 1-50

It returns only metric name, unit, latest point, and short history. Do not ask for raw fields or full graph export.

## Rules

- Prefer `resolve_research_identity` first for cross-source industry work; then use returned `graph_subject` if available.
- 行业图谱 and 产业链图谱/研究框架图谱 are separate graph surfaces. Do not claim they are identical.
- If a node is outside the public brief whitelist, say that the public-safe summary is unavailable.

## Few-Shot

- "白酒图谱有哪些公开因子" -> resolve identity, then `get_public_factor_framework(subject="<graph_subject>")`.
- "供需节点有没有公开摘要" -> `query_graph_nodes(...)`, then `get_graph_node_brief(...)`.
