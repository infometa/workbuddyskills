# API Reference

Based on [Textin Parse API v1](https://docs.textin.com/xparse/v1/).

## Command Syntax

```bash
xparse-cli parse <FILE> [options]
```

## Request Parameters

### Document Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `--password` | string | Encryption password for protected PDFs |
| `--page-range` | string | Pages to process: `1-5` or `1-2,10-15` (optional, default: all) |

### Capabilities (Output Control)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--include-hierarchy` | flag | on | Parent-child relationships and element associations |
| `--include-inline-objects` | flag | on | Formulas, handwriting, checkboxes, embedded images |
| `--include-char-details` | flag | off | Character-level coordinates and OCR confidence scores |
| `--include-image-data` | flag | on | Image URLs and Base64 encoding |
| `--include-table-structure` | flag | on | Structured table cell data with coordinates |
| `--include-pages` | flag | on | Per-page metadata and preview images |
| `--include-title-tree` | flag | on | Hierarchical document outline |

### Output Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `--output` | path | Save result to file (instead of printing to stdout) |

## Response: JSON View

### Success Response Structure

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "schema_version": "1.3.0",
    "file_id": "doc_12345",
    "job_id": "job_01HXYZ",
    "success_count": 18,
    "metadata": {
      "file_name": "report.pdf",
      "file_type": "pdf",
      "page_count": 18
    },
    "markdown": "# Document Title\n\n## Section 1\n\nContent...",
    "elements": [
      {
        "type": "Title",
        "level": 1,
        "text": "Document Title",
        "page_number": 1,
        "coordinates": [0.05, 0.08, 0.95, 0.12]
      },
      {
        "type": "NarrativeText",
        "text": "Body text content...",
        "page_number": 2,
        "coordinates": [0.05, 0.15, 0.95, 0.40]
      },
      {
        "type": "Table",
        "page_number": 3,
        "coordinates": [0.05, 0.20, 0.95, 0.50],
        "html": "<table>...</table>"
      },
      {
        "type": "Image",
        "page_number": 4,
        "coordinates": [0.10, 0.30, 0.90, 0.70]
      }
    ],
    "title_tree": [
      {
        "level": 1,
        "text": "Document Title",
        "children": [
          {
            "level": 2,
            "text": "Section 1",
            "children": [
              {
                "level": 3,
                "text": "Subsection 1.1"
              }
            ]
          }
        ]
      }
    ],
    "summary": {
      "duration_ms": 2340
    }
  }
}
```

### Response Fields

#### Top Level
- **code**: HTTP-like status code (200 = success)
- **message**: Status description
- **data**: Parsed results and metadata

#### Metadata
- **schema_version**: API schema version (e.g., "1.3.0")
- **file_id**: Unique document identifier
- **job_id**: Parse job identifier
- **success_count**: Number of pages successfully parsed (billing basis)
- **metadata**:
  - `file_name`: Original filename
  - `file_type`: File format (pdf, docx, pptx, etc.)
  - `page_count`: Total pages

#### Markdown
- **markdown**: Full document converted to Markdown format (if requested via `--view markdown`)

#### Elements
Array of document components. Each element contains:

- **type**: Element classification
  - `Title`: Heading (with `level` 1-6)
  - `NarrativeText`: Body paragraph
  - `ListItem`: Bullet or numbered list item
  - `Table`: Tabular data
  - `Image`: Embedded image or figure
  - `Formula`: Mathematical formula
  - `CodeSnippet`: Code block
  - `Header`: Page header
  - `Footer`: Page footer
  - `Checkbox`: Form checkbox
  - `Handwriting`: Handwritten text (OCR)

- **text**: Element content string
- **page_number**: Page location (1-indexed)
- **coordinates**: Normalized bounding box `[x1, y1, x2, y2]` where 0-1 represents relative position on page
- **level**: Heading level (1-6, for Title elements only)
- **html**: HTML representation (for Table elements)
- **metadata**: Additional info (hierarchy, continuation flags, inline objects)

#### Title Tree
Hierarchical outline with nested structure:
- **level**: Heading level (1-6)
- **text**: Heading text
- **children**: Nested child headings

#### Summary
- **duration_ms**: Processing time in milliseconds

## Response: Markdown View

```markdown
# Document Title

## Section 1

Content goes here.

### Subsection 1.1

Subsection content.

| Column A | Column B |
|----------|----------|
| Cell 1   | Cell 2   |

![Figure](image.png)
```

Plain text Markdown format suitable for reading or further processing.

## Error Responses

Errors return `code` ≠ 200:

```json
{
  "code": 400,
  "message": "Invalid request",
  "location": {
    "stage": "validation",
    "page_number": null,
    "element_id": null
  }
}
```

### Error Code Categories

This section groups error codes by handling intent. It is meant for CLI and skill usage, not as a full platform error manual.

#### Success

| Code | Meaning |
|------|---------|
| 200 | Success |

#### Authentication & Access

| Code | Meaning | Action |
|------|---------|--------|
| 40101 | `x-ti-app-id` missing or invalid | Check `XPARSE_APP_ID` |
| 40102 | `x-ti-secret-code` missing or invalid | Check `XPARSE_SECRET_CODE` |
| 40103 | Client IP not in whitelist | Check whitelist settings in TextIn console |

#### Account & Quota

| Code | Meaning | Action |
|------|---------|--------|
| 40003 | Insufficient balance | Use the service-provided `upgrade_url` when present, contact the account's regional support when absent, or switch to the free API if applicable |

#### Rate & Free-Tier Limits

| Code | Meaning | Action |
|------|---------|--------|
| 40306 | Service-defined rate or per-request page limit | Follow structured `error_code`: retry `RATE_LIMITED`, reduce pages for `PAGE_LIMIT_EXCEEDED` |
| 40307 | Daily free quota exhausted | Stop; ask whether to wait or explicitly retry with `--api paid` |

#### Request & Parameter Errors

| Code | Meaning | Action |
|------|---------|--------|
| 40004 | Parameter error | Check command syntax and parameter values |
| 40400 | Invalid request URL | Verify endpoint or request path |
| 40424 | Page range out of bounds | Check `--page-range` against actual page count |
| 40427 | DPI value not supported | Use a supported DPI value in (72, 144, 216) |

#### File & Input Errors

| Code | Meaning | Action |
|------|---------|--------|
| 40301 | Unsupported image type | Use a supported image format |
| 40302 | File exceeds size limit | Split pages, or after explicit user approval retry with `--api paid` |
| 40303 | File format not supported | Use a supported document format |
| 40305 | File missing or not uploaded | Verify file path or upload step |
| 40425 | File format not supported by parse engine | Use a supported format |
| 40426 | File is corrupted | Verify file integrity and retry with a valid file |
| 40428 | Office to PDF conversion failed or timed out | Simplify document or retry later |
| 40429 | PDF content is empty | Verify that the document contains readable content |

#### Encryption & Password

| Code | Meaning | Action |
|------|---------|--------|
| 40423 | Password incorrect | Retry with the correct password |

#### Processing & Service Errors

| Code | Meaning | Action |
|------|---------|--------|
| 30203 | Base service fault | Retry after a short delay |
| 40422 | Service-defined file processing failure; the direct reason is in `message` | Keep `SERVICE_ERROR`, show `message`, follow `PROVIDE_FILE`, and preserve `request_id` |
| 500 | Internal server error | Retry; contact support if persistent |
| 50207 | Partial parse failure | Check `success_count` and inspect partial output |

## Element Types

### Text Elements
- **Title**: Headings with hierarchy level
- **NarrativeText**: Body paragraphs
- **ListItem**: Bullet or numbered items

### Structural Elements
- **Table**: Tabular data with cell structure
- **Image**: Embedded images and figures
- **CodeSnippet**: Code blocks

### Inline Elements (with `--include-inline-objects`)
- **Formula**: Mathematical formulas
- **Checkbox**: Form checkboxes
- **Handwriting**: Handwritten text

### Metadata Elements
- **Header**: Page headers
- **Footer**: Page footers

## Related Documentation

- [TextIn Parse Config](https://docs.textin.com/xparse/v1/parse-config)
- [TextIn Parse Response](https://docs.textin.com/xparse/v1/parse-response)
