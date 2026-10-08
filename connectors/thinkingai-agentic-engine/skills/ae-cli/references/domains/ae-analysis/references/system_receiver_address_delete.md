# system receiver-address delete

Use when the user needs to delete a receiver address.

Do not use it outside the system receiver-address operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system receiver-address delete --dry-run --company-id <company-id> --address-url <address-url> --address-type <address-type>
ae-cli system receiver-address delete --company-id <company-id> --address-url <address-url> --address-type <address-type> --yes
```

Capability id: `system.receiver_address.delete`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--address-url` | Yes | Receiver address URL. |
| `--address-type` | Yes | Receiver address type. |
