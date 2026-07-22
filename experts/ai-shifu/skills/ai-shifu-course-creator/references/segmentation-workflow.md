# Segmentation Workflow

Turn course source material into traceable semantic segments and lesson-boundary candidates. This file does not orchestrate downstream generation.

## Required References

- `language-policy.md`
- `authoring-mode.md#mode-selection`
- `data-contracts.md#segment-schema`
- `data-contracts.md#segmentation-fallback-fields`
- `source-preservation.md`

## Segmentation

### Segmentation Methodology

#### Objective

Produce stable lesson-oriented semantic segments from noisy source material while preserving immutable artifacts.

#### Core Rules

1. Preserve source order unless explicit ordering hints are provided.
2. Keep each code block, image reference, and table block as one traceable source span. Apply `source-preservation.md` and set `preserve_block` before Teaching Prompt generation.
3. Segment by semantic shift, not heading depth alone.
4. Keep each lesson candidate centered on one teachable question.
5. Attach source spans to every segment.

#### Failure Handling

If structure is weak, output a fallback segmentation, mark uncertain spans, and provide focused rerun hints using `data-contracts.md#segmentation-fallback-fields`.

### Outputs

Produce a segment list that conforms to `data-contracts.md#segment-schema`, including its canonical segment types and transfer signals, plus workflow-local lesson-boundary candidates with one core question each.

Apply `language-policy.md` to the complete Segmentation output.

### Validation

- Segment output covers all valid source spans in traceable order.
- Every segment passes [data-contracts.md#segment-schema](data-contracts.md#segment-schema).
- The preservation and one-core-question rules in [Core Rules](#core-rules) pass; each immutable span is marked according to `source-preservation.md`.
