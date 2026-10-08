# analysis-meta exchange rule-validate

Use when the user needs to validate affected range before saving exchange-rate rules.

Do not use it to persist rules. Validation is the mandatory preflight for `exchange rule-update`.

Command:

```bash
ae-cli analysis-meta exchange rule-validate --project-id <project_id> --payload '{"target_currency":"USD","exchange_rules":[{"source_currency":"EUR","source_currency_column":"currency","target_column_desc":"amount_usd"}]}'
ae-cli analysis-meta exchange rule-validate --dry-run
```

Capability id: `metadata.exchange_rule.validate`.

Input sends `project_id`, `payload`.

Output `data` is the pre-save affected-range/conflict result. It does not modify rules.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | `{target_currency,exchange_rules}`; both are required and `exchange_rules` must be non-empty. Rule fields include `id`, `source_currency`, `source_currency_column`, required `target_column_desc`, and optional `operate_type`. |
