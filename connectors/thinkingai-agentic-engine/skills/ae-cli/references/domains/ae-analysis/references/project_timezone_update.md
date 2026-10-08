# project timezone update

Use when the user needs to update one project time zone configuration item.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project timezone update --project-id <project_id> --item timezone_toggle --payload '{"toggle":true}'
ae-cli project timezone update --project-id <project_id> --item timezone_toggle --payload '{"toggle":true}' --dry-run
```

Capability id: `project.timezone.update`.

Input sends `project_id`, `payload`, and `item`. The payload is selected by `item`; use exactly one of these snake_case shapes:

| `item` | `payload` | Notes |
|---|---|---|
| `timezone_toggle` | `{"toggle":true}` | `toggle` is required and boolean. Use `true` to enable multi-timezone and `false` to disable it. Never send `time_zone_enabled`. |
| `zone_offset` | `{"column_name":"#zone_offset"}` | `column_name` is required and selects the event property used as the timezone offset. |
| `user_timezone` | `{"column_name":"user_timezone","codetable":"timezone_code_table"}` | `column_name` is required. `codetable` is optional. |
| `project_timezone_display` | `{"display_timezones":[{"timezone":8,"is_default":true},{"timezone":0,"is_default":false}]}` | `display_timezones` is a non-empty array. `timezone` is an integer from -12 through 14, or 99 for no fixed display timezone; `is_default` is optional and boolean. |

Do not infer a payload field from the `project timezone get` output. In particular, its `time_zone_enabled` response field is not accepted by the update DTO; `timezone_toggle` always uses `payload.toggle`.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Item-specific payload from the table above. Do not send camelCase aliases or response-only fields. |
| `--item` | Yes | Timezone item: timezone_toggle, zone_offset, user_timezone, project_timezone_display. |
