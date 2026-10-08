# analysis-meta metric update

Use when the user needs to update metric definition, name, and remark.

Do not use it to query metric values.

Before updating `--metric-events` / `--metric-params`, validate the event and property names with `analysis-meta event list` and `analysis-meta property list` in the same `project_id`.

Command:

```bash
ae-cli analysis-meta metric update --project-id <project_id> --metric-id <metric_id> --metric-desc 'New display name' --metric-remark 'New remark'
ae-cli analysis-meta metric update --project-id <project_id> --metric-id <metric_id> --metric-name demo --metric-desc demo --model-type event --metric-events '[]'
ae-cli analysis-meta metric update --project-id <project_id> --metric-id <metric_id> --metric-name demo --metric-desc demo --metric-remark demo --model-type retention --metric-events '[]' --metric-params '{}'
ae-cli analysis-meta metric update --project-id <project_id> --metric-id <metric_id> --metric-desc 'New display name' --dry-run
```

Capability id: `metadata.metric.update`.

Input sends typed snake_case fields.

Output `data.metric` contains the updated summary for a full-definition update containing `metric_events`. A display-name/remark-only edit succeeds without business data.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--metric-id` | Yes | Metric ID. |
| `--metric-name` | No | Metric technical name for a full-definition update. |
| `--metric-desc` | No | Metric display name. |
| `--metric-remark` | No | Metric remark. |
| `--metric-mode` | No | Metric model mode for a full-definition update. |
| `--model-type` | No | Semantic metric model type: `event` or `retention`. Prefer this over `--metric-mode`. |
| `--metric-events` | No | Metric event-analysis QP JSON array for a full-definition update. |
| `--metric-params` | No | Metric params JSON object. |

## Decision Rules
- For full-definition updates, pass `--metric-name`, `--metric-desc`, one of `--model-type` / `--metric-mode`, and `--metric-events` together.
- If both `--model-type` and `--metric-mode` are present, they must match: `event -> 0`, `retention -> 1`.
- Use `analysis-meta metric get` before updating if the current definition needs to be preserved and edited.
- This is an ordinary write operation; execute it without the high-risk confirmation flag.
