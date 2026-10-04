# agent +add-attachment (Upload Attachments)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Attachments / write**

## Use Cases
- Upload sandbox file(s) to the attachment library.
- Endpoint: `POST /api/sandbox/agent/attachments/upload`.
- Supports single-file (`--file`) or batch (`--files`) uploads.
- MIME type is inferred from the file extension.

## Mandatory Rules (MUST)
- Exactly one of `--file` or `--files` must be provided (they are mutually exclusive).
- `--files` must be a valid JSON array of string paths, e.g. `'["./a.png","./b.pdf"]'`.
- Each file must exist on disk; non-existent paths raise an error.
- Attachment upload supports files up to 50MB each, with a 1GB user quota.
- Batch uploads support partial success — individual file failures don't affect others.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Single file
ae-cli agent +add-attachment --file ./output/report.png

# Multiple files
ae-cli agent +add-attachment --files '["./report.png", "./data.csv", "./chart.pdf"]'

# Dry-run to inspect the request before executing
ae-cli agent +add-attachment --dry-run --file ./output/report.png
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--file` | No* | Single file path |
| `--files` | No* | JSON array of file paths, e.g. `'["./a.png","./b.pdf"]'` |

\* Exactly one of `--file` or `--files` is required.

## Decision Rules
- For a single file, use `--file`; for multiple files, use `--files` with a JSON array.
- Do not pass both `--file` and `--files` — they are mutually exclusive.
- Verify file paths exist before uploading; the CLI reads them from disk.
- Use `--dry-run` first to verify the request shape before executing.

## Supported MIME Types (inferred from extension)
`.png` `.jpg` `.jpeg` `.gif` `.webp` `.svg` `.pdf` `.md` `.txt` `.csv` `.json` `.html` `.xml` `.doc` `.docx` `.xls` `.xlsx` `.pptx` `.zip` (others fall back to `application/octet-stream`).

## Next Steps on Failure
- `--file and --files cannot be used together`: pick one.
- `File not found: <path>`: verify the path and that the file exists.
- `--files must be a valid JSON array`: check the JSON syntax.
- Partial failure in batch: check the response for per-file errors; successful files are still uploaded.

## Recommended Chaining
- `+add-attachment` → `+list-attachments` (verify)
