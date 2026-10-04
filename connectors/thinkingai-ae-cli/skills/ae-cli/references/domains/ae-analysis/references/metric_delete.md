# analysis-meta metric delete

Use when the user needs to delete a metric.

Do not use it to remove a metric from one report or to delete by guessed ID; resolve and inspect the metric first.

Command:

```bash
ae-cli analysis-meta metric delete --project-id <project_id> --metric-id <metric_id> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-meta metric delete --project-id <project_id> --metric-id <metric_id> --yes
```

Capability id: `metadata.metric.delete`.

Input sends `project_id`, `metric_id`.

Output is a successful gateway envelope with no business data. Verify with `metric list|get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--metric-id` | Yes | Metric ID. |

## Decision Rules
- Use `analysis-meta metric list` first to confirm the metric ID before deleting.
- This is a destructive operation; keep the confirmation prompt unless automation is explicitly required.

## Recommended Chain
- `analysis-meta metric list` -> `analysis-meta metric delete`
