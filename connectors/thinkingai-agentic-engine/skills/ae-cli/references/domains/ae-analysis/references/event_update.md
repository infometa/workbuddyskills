# analysis-meta event update

Use when the user needs to update event display names and remarks.

Do not use it to change source-event/property relations; use `event relation-update` for the complete relation definition.

Command:

```bash
ae-cli analysis-meta event update --project-id <project_id> --event-name <event_name> --event-desc <event_desc> --remark <remark>
ae-cli analysis-meta event update --dry-run
```

Capability id: `metadata.event.update`.

Input sends `project_id`, `event_name`, `event_desc`, `remark`.

Output is a successful gateway envelope with no business data. Read back with `event get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-name` | Yes | Event name. |
| `--event-desc` | No | Event display name. |
| `--remark` | No | Event remark. |
