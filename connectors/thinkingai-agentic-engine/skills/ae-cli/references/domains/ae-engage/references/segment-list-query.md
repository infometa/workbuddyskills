# engage-task segment-list query

Query segments created from or associated with an engagement task.

> Capability id: `engage-task.segment-list.query` · Domain: `engage`.

```bash
ae-cli engage-task segment-list query --project-id <project-id> --task-id <task-id>
```

## Parameters

- `--project-id` / `-p`: Numeric project ID.
- `--task-id`: Engagement task ID.

## Output

Returns `items` and `total`. Each item includes cluster identity, display name, user count, refresh status, and `analysis_visible`.
