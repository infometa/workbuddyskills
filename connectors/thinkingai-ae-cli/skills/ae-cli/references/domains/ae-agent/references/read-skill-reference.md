# agent +read-skill-reference (Read Skill Reference)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- Read or download a Skill reference file.
- Endpoint: `GET /api/sandbox/agent/skills/[id]/references/[...path]`.
- Text responses return `{ content, fileName }` by default.
- Non-text responses require `--output <path>` to preserve the original bytes.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--path` is required and specifies the relative file path within the references directory.

## Command
```bash
# Read a reference (default JSON output)
ae-cli agent +read-skill-reference --id <skill-cuid> --path guide.md

# Save reference to local file
ae-cli agent +read-skill-reference --id <skill-cuid> --path guide.md --output ./guide.md

# Download a non-text reference (required for spreadsheets, PDFs, and other binary files)
ae-cli agent +read-skill-reference --id <skill-cuid> --path metrics.xlsx --output ./metrics.xlsx

# Read from a sub-directory
ae-cli agent +read-skill-reference --id <skill-cuid> --path "advanced/tips.md"

# Dry-run to inspect the request before executing
ae-cli agent +read-skill-reference --dry-run --id <skill-cuid> --path guide.md
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--path` | Yes | Relative file path within references (e.g. `"guide.md"` or `"advanced/tips.md"`) |
| `--output` | No | Write the original bytes to a local file; required for non-text files |

## Decision Rules
- Use `+list-skill-references` to discover available file paths before reading.
- Use the default JSON output only for text references.
- Always use `--output` for spreadsheets, PDFs, archives, images, and other non-text files.
- Read operation: no confirmation prompt needed.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-references` to verify the file path.
- `output_required`: re-run with `--output <path>` to preserve binary content.

## Recommended Chaining
- `+list-skill-references` → confirm `path` → `+read-skill-reference` → `+del-skill-reference` (if cleanup needed)
