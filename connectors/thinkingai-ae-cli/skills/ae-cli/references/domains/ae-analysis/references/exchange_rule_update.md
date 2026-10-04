# analysis-meta exchange rule-update

Use when the user needs to save currency field, amount field, and target currency rules.

Do not use it before `exchange rule-validate`, or when the user only wants to inspect current rules.

Command:

```bash
ae-cli analysis-meta exchange rule-update --project-id <project_id> --payload '{"target_currency":"USD","exchange_rules":[{"source_currency":"EUR","source_currency_column":"currency","target_column_desc":"amount_usd"}]}'
ae-cli analysis-meta exchange rule-update --dry-run
```

Capability id: `metadata.exchange_rule.update`.

Input sends `project_id`, `payload`.

Output is a successful gateway envelope with no business data. Read back with `exchange rule-list`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | The exact `{target_currency,exchange_rules}` object already accepted by `exchange rule-validate`; do not reconstruct a different payload after validation. |
