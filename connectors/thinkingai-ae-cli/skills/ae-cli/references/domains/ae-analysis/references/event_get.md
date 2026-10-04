# analysis-meta event get

Use when the user needs to get one super event metadata detail.

Do not use it for event result data, virtual-event-by-ID detail, or fuzzy discovery; use analysis data, `virtual-event get`, or `event list`.

Command:

```bash
ae-cli analysis-meta event get --project-id <project_id> --event-name <event_name>
ae-cli analysis-meta event get --dry-run
```

Capability id: `metadata.event.get`.

Input sends `project_id`, `event_name`.

Output `data.event` contains the super-event metadata detail.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-name` | Yes | Event name. |
