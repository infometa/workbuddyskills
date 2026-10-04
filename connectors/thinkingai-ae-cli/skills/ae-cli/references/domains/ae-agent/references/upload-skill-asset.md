# agent +upload-skill-asset (Upload Skill Asset)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / write**

## Use Cases
- Upload a single file to a Skill's `assets` directory (multipart upload).
- Endpoint: `POST /api/sandbox/agent/skills/[id]/assets` (multipart/form-data).
- Max file size: 1MB per file.
- Dangerous file types are rejected server-side.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--file` is required and must point to an existing local file.
- Max 1MB per file; server enforces `isDangerousFile` checks.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
# Upload a single asset
ae-cli agent +upload-skill-asset --id <skill-cuid> --file ./icon.png

# Upload to a sub-directory
ae-cli agent +upload-skill-asset --id <skill-cuid> --file ./data.csv --sub-path "sub/"

# Dry-run to inspect the request before executing
ae-cli agent +upload-skill-asset --dry-run --id <skill-cuid> --file ./icon.png
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--file` | Yes | Local file path to upload (max 1MB) |
| `--sub-path` | No | Sub-directory under assets (e.g. `"sub/"`) |

## Decision Rules
- Verify the file exists locally before uploading.
- Use `--sub-path` to organize assets into sub-directories.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `File not found`: verify the local file path.
- `文件过大（上限 1MB）`: the file exceeds the 1MB limit — compress or split it.
- `禁止上传危险文件类型`: the file type is blocked by server-side security checks.

## Recommended Chaining
- `+list-skills` → `+list-skill-assets` → `+upload-skill-asset` → `+list-skill-assets` (verify)
