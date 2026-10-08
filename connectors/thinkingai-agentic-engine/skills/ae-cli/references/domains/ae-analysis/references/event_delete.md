# analysis-meta event delete

Use when the user needs to batch delete events or virtual events.

Do not use it before `event influence-list` is reviewed for every target, or for tracking-plan entries.

Command:

```bash
ae-cli analysis-meta event delete --project-id <project_id> --event-names '["purchase"]' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis-meta event delete --project-id <project_id> --event-names '["purchase"]' --yes
```

Capability id: `metadata.event.delete`.

Input sends `project_id`, `event_names`.

Output is a successful gateway envelope with no business data. Verify with `event list`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--event-names` | Yes | Event names JSON array, or a JSON string accepted by common-service. |
