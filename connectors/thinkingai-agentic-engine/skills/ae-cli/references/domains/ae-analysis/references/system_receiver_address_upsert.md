# system receiver-address upsert

Use when the user needs to create or update a typed receiver address.

Do not use it outside the system receiver-address operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-address upsert --company-id <company-id> --scope <scope> --address-url <address-url> --address-type <address-type>
```

Capability id: `system.receiver_address.upsert`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--scope` | Yes | Receiver scope. |
| `--address-url` | Yes | Receiver address URL. |
| `--address-type` | Yes | Receiver address type. |
| `--project-ids` | No | Project ID JSON array; required for project scope. |
| `--original-address-url` | No | Original URL when changing an existing address. |
| `--original-address-type` | No | Original address type. |
