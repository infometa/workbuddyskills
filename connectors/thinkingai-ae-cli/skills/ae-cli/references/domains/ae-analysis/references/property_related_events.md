# analysis-meta property related-events

Use when the user needs to list events related to one event property.

Do not use it for user properties or for event result data; it resolves event metadata related to one event property.

Command:

```bash
ae-cli analysis-meta property related-events --project-id <project_id> --prop-name <prop_name>
ae-cli analysis-meta property related-events --dry-run
```

Capability id: `metadata.property.related_events`.

Input sends `project_id`, `prop_name`.

Output `data.events[]` contains super events related to the event property.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--prop-name` | Yes | Event property column name. |
