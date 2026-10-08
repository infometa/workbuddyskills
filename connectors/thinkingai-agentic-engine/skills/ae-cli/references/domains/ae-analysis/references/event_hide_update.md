# analysis-meta event hide-update

Use when the user needs to batch hide or show events.

Do not use it for deletion: this changes metadata visibility and keeps the event. Review affected assets first when needed.

Command:

```bash
ae-cli analysis-meta event hide-update --project-id <project_id> --event-names '["purchase"]' --is-hide true
ae-cli analysis-meta event hide-update --dry-run
```

Capability id: `metadata.event.hide_update`.

Input sends `project_id`, `event_names`, `is_hide`.

Output is a successful gateway envelope with no business data. Verify visibility with `event list|get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-names` | Yes | Event names JSON array, or a JSON string accepted by common-service. |
| `--is-hide` | Yes | Whether to hide the events. |
