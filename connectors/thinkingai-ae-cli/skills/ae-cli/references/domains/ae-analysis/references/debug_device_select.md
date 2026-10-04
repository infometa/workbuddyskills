# tracking debug-device select

Use this command to select the active Debug device for the current CLI user.
Do not use it to create a missing device or retrieve Debug events.

Command:

```bash
ae-cli tracking debug-device select --project-id <project_id> --device-id <device_id>
```

Capability id: `tracking.debug_device.select`.

Input sends `project_id` and `device_id`. The device must come from `tracking debug-device list` or a successful `tracking debug-device add`.
The result confirms the selected device; follow it with `debug-data list` only after the reporting client has sent Debug data with the same ID.

## Parameters

| Parameter      | Required | Description                         |
| -------------- | -------- | ----------------------------------- |
| `--project-id` | Yes      | Numeric AE project ID.              |
| `--device-id`  | Yes      | Existing Debug device ID to select. |
