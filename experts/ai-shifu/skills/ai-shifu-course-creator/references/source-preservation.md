# Source Preservation

Select the smallest source spans that must survive authoring without semantic or structural drift, then verify them after every affected rewrite. This file decides preservation scope; it does not define MarkdownFlow encoding.

## Required References

- `data-contracts.md#segment-schema`

## Preservation Decisions

Treat required code and fence languages, image URLs, immutable alt text and ordering, regulated wording, fixed numeric thresholds, required quotations, and table blocks as preservation candidates.

- Select only spans whose exact wording, value, ordering, or structure is a source requirement.
- Keep surrounding explanations adaptive.
- Never preserve an entire lesson; doing so removes the adaptive generation the lesson depends on.
- Record each selected segment through the `preserve_block` and `source_span` fields defined in `data-contracts.md#segment-schema`.
- Preserve author-selected immutable content even when nearby authored text is localized.

## Verification

- Compare every selected span with its authoritative source after Segmentation, Teaching Prompt generation, and Optimization.
- Verify exact content, fence language, numeric value, URL, alt or caption, order, and table structure as applicable.
- Re-run MarkdownFlow runtime checks after any rewrite that touches a selected span.
- Treat missing, altered, duplicated, or reordered immutable content as blocking.
