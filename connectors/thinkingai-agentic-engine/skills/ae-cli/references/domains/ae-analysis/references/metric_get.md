# analysis-meta metric get

Use when the user needs to get metric definition, events, and params.

Do not use it to query metric values or trends; it returns the saved metric definition only.
Do not call it just to expand a saved metric before normal ad-hoc analysis. If the user asks to query a saved metric, pass the metric display/name/remark directly in `analysis adhoc run --definition`; the backend compiler resolves saved metrics internally.

Command:

```bash
ae-cli analysis-meta metric get --project-id <project_id> --metric-id <metric_id>
ae-cli analysis-meta metric get --dry-run
```

Capability id: `metadata.metric.get`.

Input sends `project_id`, `metric_id`.

Output `data.metric` contains the saved metric definition, or no metric when the ID does not resolve.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--metric-id` | Yes | Metric ID. |

## Recommended Chaining

- analysis-meta metric get -> analysis-meta metric update
- For ad-hoc saved metric query: analysis adhoc run/export
