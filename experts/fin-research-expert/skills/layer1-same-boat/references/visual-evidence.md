# Same Boat Visual Evidence

Load this reference only after a Same Boat detail has been resolved and the current answer benefits from visual support. Ordinary text answers do not need this tool.

## Call Contract

- Market-news analysis: `get_research_visual_evidence(content_type="market_news_analysis", content_id=news_id, analyst_id=analyst_id)`.
- Market viewpoint: `get_research_visual_evidence(content_type="market_viewpoint", content_id=viewpoint_id)`; do not pass `analyst_id`.
- Use `visual_kinds` only when the answer needs a narrower family.
- Keep the default limit unless a small number of additional items is directly relevant. The server hard limit is 12.
- Use `preferred_section_indices` only when the detail already identifies the relevant source section. Do not send the user's full question as a ranking parameter.

The result must declare `schema_version="research-visual/1"`. Treat any other major schema version as unsupported and continue with the original text evidence.

## Result Contract

Each entry provides a semantic `kind`, `status`, title, source-section context, provenance and optional `fallback_table`.

- `chart`: consume ordered categories, named series, series types, values and units. Never calculate drawing coordinates in Layer 1.
- `table`: use the returned columns and rows after presentation markup has been removed.
- `radar`: draw only when `status=renderable` and the source returned a scoring scale. For `fallback_only` or `radar_scale_undefined`, show the dimension/value table and state that the scoring basis was not returned.
- `image`: eligible public report figure.
- `table_image`: a table screenshot. It is not structured data and remains an image.

For clients without inline visual support, use `fallback_table` exactly as returned. Do not re-query the source, model-compute missing values or silently change units.

## Image Display

Use an eligible `media.url` as a 普通 Markdown 图片, outside any numeric Widget runtime. Keep nearby text useful when the image cannot load.

Show returned provenance next to the image:

- `provenance.source_type` always;
- `provenance.publisher`, `provenance.report_title`, `provenance.published_at` and `provenance.page_or_position` when present;
- `provenance.source_url` only when it is non-null and is the genuine article/report link.

无文章级链接时只标注已返回的来源类型和元数据，不渲染链接，也不拿门户首页或搜索页代替。For `table_image`, label it as a table screenshot；不要 OCR，也不要重构精确数值。

## Failure Boundaries

- `data.result=null` means the requested content identity was not found.
- A non-null bundle with `visuals=[]` means the detail exists but no eligible visual matched.
- Invalid or unsafe entries may be omitted while valid siblings remain. Use `quality.issue_counts` only to explain coverage gaps, not as research evidence.
- A broken image, unsupported visual type or unavailable Widget must not fail the underlying research answer.
- Never expose internal media addresses, copy image bytes into the answer, bypass access controls or fabricate missing provenance.
