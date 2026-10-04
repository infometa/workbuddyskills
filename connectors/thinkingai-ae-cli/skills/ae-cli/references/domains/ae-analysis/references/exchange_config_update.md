# analysis-meta exchange config-update

Use when the user needs to update exchange-rate configuration switch or value.

Do not use it to edit conversion rules or refresh rate data; those are `exchange rule-update` and `exchange rate-refresh`.

Command:

```bash
ae-cli analysis-meta exchange config-update --project-id <project_id> --config-val <config_val>
ae-cli analysis-meta exchange config-update --dry-run
```

Capability id: `metadata.exchange_config.update`.

Input sends `project_id`, `config_val`.

Output is a successful gateway envelope with no business data.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--config-val` | Yes | Exchange-rate configuration value. |
