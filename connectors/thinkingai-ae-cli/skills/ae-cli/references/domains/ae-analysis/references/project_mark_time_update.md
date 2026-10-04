# project mark-time update

Use when the user needs to update a project date marker.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project mark-time update --project-id <project_id> --mark-time-id <mark_time_id> --marked-at <marked_at> --zone-offset <zone_offset> --content <content> --is-visible <is_visible>
ae-cli project mark-time update --dry-run --project-id <project_id> --mark-time-id <mark_time_id> --marked-at <marked_at> --content <content>
```

Capability id: `project.mark_time.update`.

Input sends `project_id`, `mark_time_id`, `marked_at`, `zone_offset`, `content`, `is_visible`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--mark-time-id` | Yes | Date marker ID. |
| `--marked-at` | Yes | Marker timestamp, for example yyyy-MM-dd HH:mm. |
| `--zone-offset` | No | Marker time zone offset. |
| `--content` | Yes | Marker content. |
| `--is-visible` | No | Whether the marker is visible. 1 visible, 0 hidden. |
