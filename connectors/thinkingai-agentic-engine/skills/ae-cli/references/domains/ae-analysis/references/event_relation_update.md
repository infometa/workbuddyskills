# analysis-meta event relation-update

Use when the user needs to update event-property connection or source relations.

Do not use it for display-name/remark-only edits; use `event update`. This command replaces the relation-bearing super-event definition.

Command:

```bash
ae-cli analysis-meta event relation-update --project-id <project_id> --payload '{"event_name":"purchase","source_type":"<source_type>","source_event_name":"<source_event>","super_event_prop_ids":[<property_id>]}'
ae-cli analysis-meta event relation-update --dry-run
```

Capability id: `metadata.event.relation_update`.

Input sends `project_id`, `payload`.

Output is a successful gateway envelope with no business data. Read back with `event get`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Complete relation-bearing super-event object: required `event_name` and `source_type`; optional `event_desc`, `remark`, `source_event_name`, `source_route_code`, and `super_event_prop_ids`. |
