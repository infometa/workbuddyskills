# analysis-meta metric create

Use when the user needs to create a metric from event or retention analysis configuration.

Do not use it to query metric values. Use this gateway command for an exact metric definition.

Command:

```bash
ae-cli analysis-meta metric create --project-id <project_id> --metric-name payment_success_rate --metric-desc 'Payment Success Rate' --model-type event --metric-events '[{"time_range":{"mode":"previous","unit":"day","value":7},"metrics":[{"formula":"finish / order","dependencies":[{"alias":"finish","event":"purchase_finish","aggregation":"total_count"},{"alias":"order","event":"order_create","aggregation":"total_count"}]}]}]' --metric-params '{"format":"percent"}'
ae-cli analysis-meta metric create --project-id <project_id> --metric-name retained_users --metric-desc 'Retained Users' --model-type retention --metric-events '[...]' --metric-params '{}'
```

Capability id: `metadata.metric.create`.

Input sends typed snake_case fields. For event metrics, common validates the semantic definition and compiles it to the backend QP; for example, each `dependencies[].event` becomes the native `eventName`. Common then serializes `metric_events` and `metric_params` for the backend.

Output `data.metric` contains the created metric summary.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--metric-name` | Yes | Metric technical name. |
| `--metric-desc` | Yes | Metric display name. |
| `--model-type` | Yes | Semantic metric model type: `event` or `retention`; the CLI converts it to the backend `metric_mode`. |
| `--metric-events` | Yes | Exactly one semantic event-analysis definition. A native snake_case QP array is accepted for compatibility. |
| `--metric-remark` | No | Metric remark. |
| `--metric-params` | No | Metric params JSON object; common defaults it to `{}` when needed. |

## Decision Rules

- Pass `--model-type event` or `--model-type retention`. `metric create` does not expose the backend-only `--metric-mode` selector.
- For an event formula, pass exactly one item in `metric_events` and exactly one item in its `metrics`; every dependency requires `alias`, `event`, and `aggregation`.
- Use public snake_case fields such as `time_range` and `dependencies[].event`; do not send backend-only camelCase fields such as `eventName` in the semantic definition.
- For event metrics, `--metric-params` is usually a format config such as `{"format":"integer"}`.
- For retention metrics, `--metric-params` should be the retention `eventView` configuration.
