# analysis-meta event list

Use when the user needs to list project super events, search event metadata, page results, project fields, or filter to authenticated events.

Do not use it for raw tracked events, event counts, or one full definition; it lists project super-event metadata.

Command:

```bash
ae-cli analysis-meta event list --project-id <project_id>
ae-cli analysis-meta event list --project-id <project_id> --queries '["login","sign in"]' --fields '["event_name","event_desc","authentication_status"]' --limit 50 --offset 0 --authenticated-only
ae-cli analysis-meta event list --dry-run
```

Capability id: `metadata.event.list`.

Input sends `project_id`, `queries`, `fields`, `limit`, `offset`, and `authenticated_only`.

Use snake_case projection fields: `event_id`, `event_name`, `event_desc`, `remark`, `event_tag`, `authentication_status`. Do not send legacy camelCase field names.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--queries` | No | JSON array of 1-20 keyword filters. A row is returned when any keyword matches `event_name`, `event_desc`, or `remark`. |
| `--fields` / `-f` | No | Optional JSON array of snake_case fields to return. |
| `--limit` / `-l` | No | Page size. Default: 50, maximum: 200; values outside 1..200 are rejected. |
| `--offset` / `-o` | No | Zero-based page offset. Default: 0; negative values are rejected. |
| `--authenticated-only` | No | When true, return only authenticated events and include `authentication_status` when projected. |
For a complete result, use `analysis-meta event export`; do not page repeatedly to synthesize an export.
