# analysis-meta event export

Use when the user explicitly needs every accessible event, optionally filtered or projected, in one local file.

Do not use it for paginated discovery, raw tracked events, or analysis result data.

Command:

```bash
ae-cli analysis-meta event export --project-id <project_id> --output <temporary_path>/events.json
ae-cli analysis-meta event export --project-id <project_id> --queries '["login","sign in"]' --fields '["event_name","event_desc"]' --output <temporary_path>/events.json
ae-cli analysis-meta event export --dry-run
```

Capability id: `metadata.event.export`.

Input: the gateway receives `project_id` plus optional `queries`, `fields`, and `authenticated_only`; `output` is local-only.

Output: a successful response must prove `complete=true` and `total` equal to the row count before the CLI atomically publishes a private-mode `.json` array.

Do not use pagination or repeated `list` calls to recreate this behavior. Search the output file locally and keep full rows out of model context.
