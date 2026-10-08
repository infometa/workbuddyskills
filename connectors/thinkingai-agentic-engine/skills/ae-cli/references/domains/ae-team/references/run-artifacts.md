# team +run-artifacts (List TeamRun Artifacts)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **TeamRun execution / read**

## Use Cases
- List all artifacts (output files, reports, documents) produced by a completed TeamRun.
- By default, returns metadata only (no content). Use `--include-content true` to fetch full artifact content.
- Supports filtering by artifact type.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real run ID from a previous `+run-start` or `+run-chat` response — do not guess.
- Only call this command after `+run-result` confirms `status = completed`. Artifacts may be incomplete for non-terminal runs.

## Command
```bash
# List artifact metadata (no content)
ae-cli team +run-artifacts --id <run_id>

# Include full content
ae-cli team +run-artifacts --id <run_id> --include-content true

# Filter by type
ae-cli team +run-artifacts --id <run_id> --artifact-type report

# Combine
ae-cli team +run-artifacts --id <run_id> --artifact-type markdown --include-content true

ae-cli team +run-artifacts --dry-run --id <run_id>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | TeamRun ID |
| `--artifact-type` | No | Filter by artifact type (e.g. `report`, `markdown`, `xlsx`) |
| `--include-content` | No | `true` to include full artifact content (default: `false`) |

## Decision Rules
- First call without `--include-content` to get the list and sizes. Then decide whether to fetch content.
- Use `--include-content true` only when the user explicitly wants the artifact body (e.g. to display a report, extract data, or forward the content).
- If the run has not yet completed, call `+run-result` first and wait for terminal status.

## Next Steps on Failure
- `404`: run ID not found — verify from the original start response.
- Empty list: the run completed but produced no artifacts; inspect `+run-result` output for any inline results.

## Recommended Chaining
- `+run-result` (confirm `completed`) → `+run-artifacts`
- `+run-artifacts` → user reviews metadata → `+run-artifacts --include-content true` (fetch content for specific artifact)
