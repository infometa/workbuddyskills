# Document navigation

Use these commands only for a successfully parsed complete local document. The
`parse` command writes the cache used by all navigation primitives.

## Standard workflow

```text
get_doc_info -> parse -> get_outline/search_text/read_pages -> read_content
```

1. `get_doc_info <FILE>` returns the stable `doc_id`, page count, and document type locally.
2. `parse <FILE> --api auto` parses the complete document and writes its navigation cache.
3. Navigate until every needed section or fact has been identified.
4. Batch independent extraction calls together.

Do not use `--page-range` for the cache-building parse. A page-range response is
partial and intentionally does not overwrite the complete-document cache.

## Plan before reading

Before the first `read_content` call:

1. List every section or fact needed for the user's question.
2. Complete all outline drill-downs when `truncated=true`.
3. Search for named facts, amounts, dates, or keywords.
4. Select the smallest set of sections or elements that covers the request.

Target no more than eight `read_content` calls per task. Prefer reading one
parent section, which includes its children, over reading every child separately.

## Navigation decisions

| User intent | Action |
|-------------|--------|
| Knows section name and outline is not truncated | `get_outline` then `read_content <element_id>` |
| Knows section name and outline is truncated | Drill down with `get_outline --parent-id <id>`, then read the exact target |
| Knows a keyword but not its location | `search_text`; use returned context directly or read the matched element |
| Knows keyword and target section | `get_outline`, then `search_text --scope <section_id>` |
| Knows page number | `read_pages <start> <end>`; maximum 20 pages per call |
| Document has no headings | `search_text`, then fall back to `read_pages` |

Never guess an `element_id`. When an outline is truncated, expand the relevant
branch before calling `read_content`.

## Prefer search for facts

For revenue, profit, percentages, dates, names, and similar facts, call
`search_text` first. Its context often contains enough evidence without loading
an entire section. For a large section, narrow the search with `--scope`.

Escalate to `read_content` when full table structure, surrounding paragraphs, or
all child content is required.

## Command reference

| Command | Result and constraint |
|---------|-----------------------|
| `get_doc_info <FILE>` | Local `doc_id`, `page_count`, and `doc_type`; no API call |
| `get_outline <DOC_ID> [--depth N] [--parent-id <ID>]` | Hierarchical headings and exact element IDs; drill down when truncated |
| `search_text <DOC_ID> <PATTERN> [--regex] [--max-results N] [--scope <ID>]` | Matches with context, page, element ID, and heading reference |
| `read_content <DOC_ID> <ELEMENT_ID>` | Section Markdown, table HTML/Markdown, or paragraph content |
| `read_pages <DOC_ID> <START> <END>` | Page Markdown, tables, and images; maximum 20 pages |
| `get_confidence <DOC_ID> --element-id <ID>` | Optional OCR confidence check for a suspect element |

The `doc_id` is derived from the absolute local path. Preserve it exactly from
`get_doc_info`. Use IDs returned by outline or search without modifying them.

## Output budgeting

- Start large outlines at `--depth 1`, then expand only relevant branches.
- Use scoped search before reading a section spanning more than about 30 pages.
- A 20-page `read_pages` response can be large; use smaller ranges when the
  context budget is limited.
- Issue independent `read_content` and `search_text` calls in one batch after
  the plan is complete, rather than adding a new reasoning turn for each call.

## Error recovery

| Error | Response |
|-------|----------|
| Cache miss for `doc_id` | Run a complete local `parse <FILE> --api auto`, then retry navigation |
| Unknown `doc_id` | Run `get_doc_info <FILE>` and retain its exact output |
| Element ID not found | Re-read the relevant outline/search result; do not guess |
| Page range too large | Reduce `read_pages` to at most 20 pages |
| Rate limited | Allow the CLI's bounded retry; retry manually once at most |
| Free quota exhausted | Inspect `quota --output json`, explain the available options, and obtain approval before paid use |
| Password-protected document | Ask the user for the password |

There is no separate cache-preparation command. Recover a cache miss by parsing
the complete local document.

## Example

```bash
xparse-cli get_doc_info /path/to/annual-report.pdf
# {"doc_id":"a1b2c3d4e5f6","page_count":120,"doc_type":"report"}

xparse-cli parse /path/to/annual-report.pdf --api auto --output /path/to/results

xparse-cli get_outline a1b2c3d4e5f6 --depth 1
xparse-cli get_outline a1b2c3d4e5f6 --parent-id b2c3d4
xparse-cli search_text a1b2c3d4e5f6 "net profit" --scope b2c3d4

# After navigation is complete, batch the exact reads needed by the task.
xparse-cli read_content a1b2c3d4e5f6 f1a2b3
xparse-cli read_content a1b2c3d4e5f6 c4d5e6
```
