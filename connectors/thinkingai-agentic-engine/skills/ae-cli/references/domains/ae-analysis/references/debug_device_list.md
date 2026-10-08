# tracking debug-device list

Use this command to list Debug devices for one AE project and identify the device selected by the current CLI user.

Command:

```bash
ae-cli tracking debug-device list --project-id <project_id>
```

Capability id: `tracking.debug_device.list`.

Input sends `project_id`. The result contains the available Debug devices and current selection. Use the returned device IDs for `debug-device select` and `debug-data list`; do not invent an ID.

## Parameters

| Parameter      | Required | Description            |
| -------------- | -------- | ---------------------- |
| `--project-id` | Yes      | Numeric AE project ID. |
