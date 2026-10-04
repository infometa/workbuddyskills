---
name: listing-asin-batch-ingest
description: Parse ASIN batches from pasted text or host-provided local CSV, TSV, TXT, JSON, XLSX, or ZIP files; validate and deduplicate identifiers without fetching product data.
---

# Listing ASIN Batch Ingest

## Scope

Normalize ASIN identifiers for downstream Listing work. This Skill does not upload/download files,
search platform workspaces, fetch ASIN details, authorize stores, or publish anything.

## Inputs

- pasted text; or
- an explicit local path / `file://` URI supplied by the host.

Supported content: CSV, TSV, TXT, JSON, Markdown, HTML, XLS/XLSX and bounded ZIP archives. Remote URLs
and opaque platform file IDs are rejected.

## Process

1. Extract case-insensitive `\b[A-Z0-9]{10}\b` candidates.
2. Normalize to uppercase and preserve first-seen order.
3. Validate exact length and characters.
4. Deduplicate within the batch.
5. Preserve useful adjacent columns as `source_context`; never infer product facts from an identifier.

For local files:

```bash
python3 scripts/parse_attachment.py /abs/input.csv --out /abs/summary.json
```

Use `--all-rows` only when the host explicitly requests full local parsing. ZIP extraction remains bounded
by file count and member size.

## Output

Return JSON containing `valid_asins`, `invalid_rows`, `duplicates`, `source_context`, counts and warnings.
Downstream skills still require host-provided product/listing evidence for each ASIN.
