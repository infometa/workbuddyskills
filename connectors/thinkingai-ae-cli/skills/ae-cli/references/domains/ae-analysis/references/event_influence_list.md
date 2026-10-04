# analysis-meta event influence-list

Use when the user needs to list assets affected by event delete, hide, or update.

Do not use it as mutation or as proof that deletion is safe without reviewing every returned dependency.

Command:

```bash
ae-cli analysis-meta event influence-list --project-id <project_id> --event-name <event_name>
ae-cli analysis-meta event influence-list --dry-run
```

Capability id: `metadata.event.influence_list`.

Input sends `project_id`, `event_name`.

Output is the snake_case event influence object returned by Common, including dependent assets and operation constraints.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-name` | Yes | Event name. |
