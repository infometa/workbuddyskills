# tracking debug-device add

Use this command to create or update a Debug device for one AE project.
Do not use it to select the active device or query Debug data; use `debug-device select` and `debug-data list` for those actions.

Command:

```bash
ae-cli tracking debug-device add --project-id <project_id> --device-id <device_id> --device-name <device_name>
```

Capability id: `tracking.debug_device.add`.

Input sends `project_id`, `device_id`, and `device_name`. Prefer a stable device ID that the validation script can reuse. After creation, select the same device with `tracking debug-device select`.
The result confirms that the device was created or updated; use `debug-device list` to verify the saved device before selecting it.

## Parameters

| Parameter       | Required | Description                                          |
| --------------- | -------- | ---------------------------------------------------- |
| `--project-id`  | Yes      | Numeric AE project ID.                               |
| `--device-id`   | Yes      | Stable Debug device ID used by the reporting client. |
| `--device-name` | Yes      | Human-readable Debug device name.                    |
