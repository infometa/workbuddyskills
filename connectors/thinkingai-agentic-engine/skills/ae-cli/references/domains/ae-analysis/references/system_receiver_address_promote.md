# system receiver-address promote

Use when the user needs to promote a receiver address to company scope.

Do not use it outside the system receiver-address operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-address promote --company-id <company-id> --address-url <address-url> --address-type <address-type>
```

Capability id: `system.receiver_address.promote`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--address-url` | Yes | Receiver address URL. |
| `--address-type` | Yes | Receiver address type. |
| `--remove-project-custom` | No | Remove matching project overrides after promotion. |
