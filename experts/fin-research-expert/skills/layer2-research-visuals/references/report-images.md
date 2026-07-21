# Report Image Contract

Use for report or article images only after the authenticated research workflow has returned the underlying evidence. Same Boat visual entries use `schema_version="research-visual/1"`.

## Eligibility

Embed an image only when the evidence contains:

- `kind=image` or `kind=table_image`;
- `status=renderable`;
- a stable HTTPS `media.url` on the approved public media host, returned by the authenticated tool;
- `provenance.source_type` and a clear evidence reason for selecting the image.

Show `provenance.publisher`, `provenance.report_title`, `provenance.published_at` and `provenance.page_or_position` when returned. Missing fields remain missing. Do not infer a publication date, page number, institution or report title from an image filename or nearby prose.

## Display

Use ordinary Markdown image syntax, not a numeric Widget runtime. Immediately adjacent to it:

1. Show publisher/institution, report title, publication date and page/position when available.
2. State in one sentence why the figure supports the answer.
3. Render `provenance.source_url` as the source-review link only when it is non-null and genuine.
4. For `kind=table_image`, label it as a table screenshot and explicitly distinguish it from structured table data.

Keep the conclusion and key evidence in text. 图片加载失败时，原研究回答、来源类型和文字证据仍须可读。

## Table Screenshot Boundary

- A `kind=table_image` entry remains an image. Do not treat pixels as verified rows or columns.
- 对表格截图不做 OCR，不从模糊图片重构精确数字，也不把模型识别结果冒充 MCP 返回数据。
- If the same bundle provides a real `kind=table` or `fallback_table`, prefer that structure for exact values and use the screenshot only as supporting context.

## MCP Image Content

When an authenticated tool returns an MCP image content block, WorkBuddy may display it inside the tool-result surface. Treat that as a visual supplement:

- Keep the same provenance and textual summary in the answer.
- Do not assume the image appears inline beside final prose on every client.
- Do not convert undocumented binary content into a report claim.
- Use the returned table/text fallback when the client cannot show image content.

## No Fake Link

- Apply the existing `no fake link` contract before rendering any source-review action.
- Apply a strict no-fake-link rule to every image and source-review entry.
- If `provenance.source_url` is null, show `provenance.source_type` and other returned fields but render no link.
- Do not link a portal home page or search page as if it were the report source.
- Do not synthesize an image URL, remove access controls, proxy an image to bypass restrictions or redistribute an entire report.
- If `media.url` is expired, login-only, anti-hotlink blocked or rights-unclear, omit the image and preserve the report summary.

## Fallback

When eligibility fails, return the available report title, institution, publication date, evidence summary and genuine source type/link. “No displayable report image was returned” is a valid boundary, not a reason to insert a stock image.
