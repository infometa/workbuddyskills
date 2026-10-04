# tracking debug-data list

Use this command to query Debug data received from one device and verify an SDK reporting flow.

Command:

```bash
ae-cli tracking debug-data list \
  --project-id <project_id> \
  --device-id <device_id> \
  --start-time "YYYY-MM-DD HH:mm:ss" \
  [--event-name <event_name>]
```

Capability id: `tracking.debug_data.list`.

Input sends `project_id`, `device_id`, `start_time`, and optional `event_name`. When omitted, `start_time` defaults to one hour ago in local time.

The normalized result includes `has_data`, `event_count`, `data_count`, `event_list`, and `device_data_list`. Treat validation as successful only when `has_data` is true and the returned event names, property structures, and error fields are correct.

## Parameters

| Parameter      | Required | Description                                                                |
| -------------- | -------- | -------------------------------------------------------------------------- |
| `--project-id` | Yes      | Numeric AE project ID.                                                     |
| `--device-id`  | Yes      | Debug device ID used by the reporting client.                              |
| `--start-time` | No       | Query start time in local `YYYY-MM-DD HH:mm:ss`; defaults to one hour ago. |
| `--event-name` | No       | Exact event name filter.                                                   |
