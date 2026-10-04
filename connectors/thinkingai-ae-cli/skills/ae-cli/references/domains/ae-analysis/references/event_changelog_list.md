# analysis-meta event changelog-list

Use when the user needs to list event metadata change logs.

Do not use it for the current event definition or tracking data; use `event get` or an analysis query.

Command:

```bash
ae-cli analysis-meta event changelog-list --project-id <project_id> --event-name <event_name>
ae-cli analysis-meta event changelog-list --dry-run
```

Capability id: `metadata.event.changelog_list`.

Input sends `project_id`, `event_name`.

Output `data.changelogs[]` contains metadata change records for the event.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-name` | Yes | Event name. |
