# system query-alert-rule update

Use when the user needs to batch upsert and delete query-monitor alert rules.

Do not use it outside the system query-alert-rule operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system query-alert-rule update --dry-run --company-id <company-id>
ae-cli system query-alert-rule update --company-id <company-id> --yes
```

Capability id: `system.query_alert_rule.update`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--upserts` | No | Rule upsert JSON array. |
| `--delete-ids` | No | Positive rule-ID JSON array to delete. |
