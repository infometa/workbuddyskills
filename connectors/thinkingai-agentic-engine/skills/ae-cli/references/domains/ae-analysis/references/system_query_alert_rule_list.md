# system query-alert-rule list

Use when the user needs to list query-monitor alert rules and metric definitions.

Do not use it outside the system query-alert-rule operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-alert-rule list --company-id <company-id>
```

Capability id: `system.query_alert_rule.list`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
