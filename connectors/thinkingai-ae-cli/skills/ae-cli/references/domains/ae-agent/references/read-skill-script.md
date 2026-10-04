# agent +read-skill-script (Read Skill Script)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / read**

## Use Cases
- Read a Skill script file's raw binary content (binary-safe).
- Endpoint: `GET /api/sandbox/agent/skills/[id]/scripts/[...path]`.
- By default returns `{ content, fileName }` where content is best-effort UTF-8 text.
- Use `--output <path>` to save the raw binary content to a local file (preserves binary data).

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Skill record ID (CUID) via `+list-skills` — do not guess.
- `--path` is required and specifies the relative file path within the scripts directory.
- For binary files, always use `--output` to avoid UTF-8 corruption.

## Command
```bash
# Read a text script (default JSON output)
ae-cli agent +read-skill-script --id <skill-cuid> --path helper.sh

# Save binary script to local file
ae-cli agent +read-skill-script --id <skill-cuid> --path tool.bin --output ./tool.bin

# Read from a sub-directory
ae-cli agent +read-skill-script --id <skill-cuid> --path "tools/run.py"

# Dry-run to inspect the request before executing
ae-cli agent +read-skill-script --dry-run --id <skill-cuid> --path helper.sh
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID) |
| `--path` | Yes | Relative file path within scripts (e.g. `"helper.sh"` or `"tools/run.py"`) |
| `--output` | No | Write binary content to a local file (preserves binary data) |

## Decision Rules
- Use `+list-skill-scripts` to discover available file paths before reading.
- For text files (.sh, .py, .js, etc.), the default JSON output `{ content }` is sufficient.
- For binary files, always use `--output <path>` to save to disk.
- Read operation: no confirmation prompt needed.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-scripts` to verify the file path.
- `文件不存在`: the file path does not exist in the scripts directory.

## Recommended Chaining
- `+list-skill-scripts` → confirm `path` → `+read-skill-script --output` → `+del-skill-script` (if cleanup needed)
