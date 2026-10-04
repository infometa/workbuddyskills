# analysis report list-export

Use when the user needs to export the full accessible report catalog or a larger catalog than inline pagination should return.

Do not use for report data values. Use `report-data export` when the output should be report result data, not catalog metadata.

Command:

```bash
ae-cli analysis report list-export --project-id <project_id> [--queries '["growth","retention"]'] [--model-types '["event","sql","tag","revenue"]'] [--fields '["report_id","report_name"]'] [--artifact-format jsonl] [--request-id cli_0123456789abcdef0123456789abcdef] [--timeout-seconds 21600]
```

Input sends `project_id`, optional `queries`, semantic `model_types`, `fields`, lifecycle `request_id`, artifact `format`, and `timeout_seconds`. `queries` accepts 1 to 20 non-empty strings with OR semantics; the singular `query` is not accepted. ae-cli generates and announces `request_id` before dispatch when it is omitted.

Output is the gateway envelope. `data` contains an async artifact descriptor including `run_id`, `artifact_id`, status, and expiration fields. Inspect and download through the dedicated CLI commands using those opaque IDs.
