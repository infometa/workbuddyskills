# analysis-meta metric export

Use when the user explicitly needs every accessible metric, optionally filtered or projected, in one local file.

Do not use it to calculate metric values or for paginated discovery.

Command:

```bash
ae-cli analysis-meta metric export --project-id <project_id> --output <temporary_path>/metrics.json
ae-cli analysis-meta metric export --project-id <project_id> --queries '["pay","revenue"]' --fields '["metric_name","metric_desc"]' --output <temporary_path>/metrics.json
ae-cli analysis-meta metric export --dry-run
```

Capability id: `metadata.metric.export`.

Input: the gateway receives `project_id` plus optional `ignore_authentication`, `queries`, `fields`, and `authenticated_only`; `output` is local-only.

Output: a successful response must prove `complete=true` and `total` equal to the row count before the CLI atomically publishes a private-mode `.json` array.

Do not use pagination or repeated `list` calls to recreate this behavior. Search the output file locally and keep full rows out of model context.
