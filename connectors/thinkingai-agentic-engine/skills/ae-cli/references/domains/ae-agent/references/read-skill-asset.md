# agent +read-skill-asset (Read Skill Asset)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- Read a Skill asset file's raw binary content (binary-safe).
- Endpoint: `GET /api/sandbox/agent/skills/[id]/assets/[...path]`.
- By default returns `{ content, fileName }` where content is best-effort UTF-8 text.
- Use `--output <path>` to save the raw binary content to a local file (preserves binary data).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--path` is required and specifies the relative file path within the assets directory.
- For binary files (images, PDFs, etc.), always use `--output` to avoid UTF-8 corruption.

## Command
```bash
# Read a text asset (default JSON output)
ae-cli agent +read-skill-asset --id <skill-cuid> --path guide.txt

# Save binary asset to local file
ae-cli agent +read-skill-asset --id <skill-cuid> --path icon.png --output ./icon.png

# Read from a sub-directory
ae-cli agent +read-skill-asset --id <skill-cuid> --path "sub/data.csv" --output ./data.csv

# Dry-run to inspect the request before executing
ae-cli agent +read-skill-asset --dry-run --id <skill-cuid> --path icon.png
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--path` | Yes | Relative file path within assets (e.g. `"icon.png"` or `"sub/data.csv"`) |
| `--output` | No | Write binary content to a local file (preserves binary data) |

## Decision Rules
- Use `+list-skill-assets` to discover available file paths before reading.
- For text files (.md, .txt, .csv, .json), the default JSON output `{ content }` is sufficient.
- For binary files (.png, .pdf, .zip, etc.), always use `--output <path>` to save to disk — the default text output may corrupt binary data.
- Read operation: no confirmation prompt needed.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-assets` to verify the file path.
- `文件不存在`: the file path does not exist in the assets directory.

## Recommended Chaining
- `+list-skill-assets` → confirm `path` → `+read-skill-asset --output` → `+del-skill-asset` (if cleanup needed)
