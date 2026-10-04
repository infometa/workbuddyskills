# system receiver-detection update

Use when the user needs to update typed receiver-address detection configuration.

Do not use it outside the system receiver-detection operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-detection update --company-id <company-id> --address-url <address-url> --execute-type <execute-type> --schedule-type <schedule-type> --allow-notification <true_or_false>
```

Capability id: `system.receiver_detection.update`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--address-url` | Yes | Receiver address URL. |
| `--execute-type` | Yes | Detection execution scope. |
| `--schedule-type` | Yes | Detection schedule. |
| `--allow-notification` | Yes | Allow detection notifications. |
