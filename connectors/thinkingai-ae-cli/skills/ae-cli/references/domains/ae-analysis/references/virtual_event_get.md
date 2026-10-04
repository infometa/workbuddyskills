# analysis-meta virtual-event get

Use when the user needs to get virtual event rule.

Do not use it for super-event-by-name detail or event result data; this resolves one virtual event by numeric ID.

Command:

```bash
ae-cli analysis-meta virtual-event get --project-id <project_id> --v-event-id <v_event_id>
ae-cli analysis-meta virtual-event get --dry-run
```

Capability id: `metadata.virtual_event.get`.

Input sends `project_id`, `v_event_id`.

Output `data.virtual_event` contains the virtual-event metadata and rule.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--v-event-id` | Yes | Virtual event ID. |
