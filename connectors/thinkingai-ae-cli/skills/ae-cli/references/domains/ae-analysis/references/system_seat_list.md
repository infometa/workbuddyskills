# system seat list

Use when the user needs to list company seat assignments.

Do not use it outside the system seat operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system seat list --company-id <company-id>
```

Capability id: `system.seat.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--query` | No | Optional keyword filter. |
| `--limit` | No | Page size. Default and maximum depend on the capability schema. |
| `--offset` | No | Zero-based result offset. |
| `--seat-type` | No | Optional seat type. |
