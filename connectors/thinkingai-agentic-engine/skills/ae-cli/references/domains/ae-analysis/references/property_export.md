# analysis-meta property export

Use when the user explicitly needs every accessible event or user property, including flat dimension-table and complex child rows, in one local file.

Do not use it for paginated discovery, property values, or analysis result data.

Command:

```bash
ae-cli analysis-meta property export --project-id <project_id> --scope event --output <temporary_path>/properties.json
ae-cli analysis-meta property export --project-id <project_id> --scope event --event-name purchase --queries '["amount"]' --fields '["prop_name","prop_desc"]' --output <temporary_path>/properties.json
ae-cli analysis-meta property export --dry-run
```

Capability id: `metadata.property.export`.

Input: the gateway receives `project_id` plus optional `table_type`, `scope`, `event_name`, `queries`, `fields`, and `authenticated_only`; `output` is local-only.

Output: a successful response must prove `complete=true` and `total` equal to the row count before the CLI atomically publishes a private-mode `.json` array.

Do not use pagination or repeated `list` calls to recreate this behavior. Search the output file locally and keep full rows out of model context.
