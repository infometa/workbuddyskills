# analysis-meta event create

Use when the user needs to create super events and optionally associate event properties.

Do not use it for a virtual event, tracking-plan event, or description-only update. Use the corresponding virtual-event, tracking-plan, or `event update` command.

Command:

```bash
ae-cli analysis-meta event create --project-id <project_id> --payload '{"event_name":"purchase","event_desc":"Purchase","source_type":"<source_type>","source_event_name":"<source_event>"}'
ae-cli analysis-meta event create --dry-run
```

Capability id: `metadata.event.create`.

Input sends `project_id`, `payload`.

Output is a successful gateway envelope with no business data. Read back with `event get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Super-event object. Required: `event_name`, `source_type`. Optional: `event_desc`, `remark`, `source_event_name`, `source_route_code`, `super_event_prop_ids`. Use real source metadata; `{}` is invalid. |
