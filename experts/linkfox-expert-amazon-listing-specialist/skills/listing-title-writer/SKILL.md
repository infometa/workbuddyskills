---
name: listing-title-writer
description: Write or rewrite Amazon Listing titles and Item Highlights from host-provided facts and keyword evidence. Produces portable JSON or Markdown only.
---

# Listing Title Writer

## Scope

Write one or many titles without fetching data, reading platform sessions, uploading files, producing
workbench UI payloads, or exporting Excel. The host supplies normalized product rows and owns storage.

## Inputs

- verified target-product facts;
- marketplace and output language;
- optional existing title;
- optional keyword matrix from `listing-keyword-matrix-build`;
- owned brand names, competitor brands and banned terms;
- optional per-field limits.

Do not treat an ASIN, URL, competitor fact or keyword metric as a target-product fact.

## Method

1. Identify product type, strongest differentiator, one useful attribute and one audience/scene cue.
2. If keyword evidence exists, use one natural core phrase near the front. Never invent volume or rank.
3. Keep pain phrases for Item Highlights or bullets when they make the title awkward.
4. Remove promotions, subjective superlatives, competitor brands, unsupported claims and repetition.
5. Default to 75 characters for Title and 125 for Item Highlights unless a stricter supplied spec applies.
6. Validate every row independently; do not truncate failed rows silently.

`scripts/plan_keywords.py` may classify a supplied keyword matrix. `scripts/listing_spec.py` may normalize
host-provided field limits. Neither script calls external services.

## Output

Return JSON or Markdown with, per row:

```json
{
  "row_id": "1",
  "title": "...",
  "item_highlights": "...",
  "used_keywords": [{"keyword": "...", "field": "title"}],
  "status": "ok",
  "warnings": []
}
```

For rewrites, add a short `change_reason`. For batches, include `total`, `ok`, `review` and `failed`.
The caller may save or transform this portable result after the Skill completes.

## Guardrails

- Preserve verified brand, model, size, count and compatibility facts.
- Never copy competitor branding or distinctive phrasing.
- Never add certification, warranty, safety, medical, performance or quantified claims without facts.
- Do not publish, upload, write to a product library, or generate HTML/XLSX.
