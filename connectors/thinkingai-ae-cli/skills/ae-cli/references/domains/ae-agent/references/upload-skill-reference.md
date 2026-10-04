# agent +upload-skill-reference (Upload Skill Reference)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases
- Upload a single file to a Skill's `references` directory (multipart upload).
- Endpoint: `POST /api/sandbox/agent/skills/[id]/references` (multipart/form-data).
- Max file size: 1MB per file.
- Markdown, text, CSV, spreadsheet, PDF, and other non-dangerous file types are supported.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--file` is required and must be an existing local file.
- Max 1MB per file; server enforces `isDangerousFile` checks.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Upload a single reference
ae-cli agent +upload-skill-reference --id <skill-cuid> --file ./guide.md

# Upload to a sub-directory
ae-cli agent +upload-skill-reference --id <skill-cuid> --file ./advanced.md --sub-path "advanced/"

# Upload a spreadsheet reference
ae-cli agent +upload-skill-reference --id <skill-cuid> --file ./metrics.xlsx

# Dry-run to inspect the request before executing
ae-cli agent +upload-skill-reference --dry-run --id <skill-cuid> --file ./guide.md
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--file` | Yes | Local file path to upload (max 1MB) |
| `--sub-path` | No | Sub-directory under references (e.g. `"advanced/"`) |

## Decision Rules
- Verify the file exists locally and does not exceed 1MB before uploading.
- Keep supporting material in `references`; use `assets` for files consumed as presentation or runtime assets.
- Use `--sub-path` to organize references into sub-directories.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `File not found`: verify the local file path.
- File-too-large API error: the file exceeds the 1MB limit — reduce or split the file.
- Dangerous-file API error: the file type is blocked by the server safety policy.

## Recommended Chaining
- `+list-skills` → `+list-skill-references` → `+upload-skill-reference` → `+list-skill-references` (verify)
