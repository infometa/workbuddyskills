# analysis-meta exchange rate-refresh

Use when the user needs to refresh exchange-rate data manually.

Do not use it to change rules/configuration, and do not repeatedly refresh to compensate for an invalid rule.

Command:

```bash
ae-cli analysis-meta exchange rate-refresh --project-id <project_id>
ae-cli analysis-meta exchange rate-refresh --dry-run
```

Capability id: `metadata.exchange_rate.refresh`.

Input sends `project_id`.

Output is a successful gateway envelope with no business data after the refresh request completes.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
