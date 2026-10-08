# analysis-meta virtual-event delete

Use when the user needs to delete a virtual event rule.

Do not use it for super events or by guessed ID; resolve and inspect the virtual event first.

Command:

```bash
ae-cli analysis-meta virtual-event delete --project-id <project_id> --v-event-id <v_event_id> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-meta virtual-event delete --project-id <project_id> --v-event-id <v_event_id> --yes
```

Capability id: `metadata.virtual_event.delete`.

Input sends `project_id`, `v_event_id`.

Output is a successful gateway envelope with no business data.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--v-event-id` | Yes | Virtual event ID. |
