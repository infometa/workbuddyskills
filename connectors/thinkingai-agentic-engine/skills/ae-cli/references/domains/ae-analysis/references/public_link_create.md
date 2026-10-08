# analysis public-link create

Use when the user explicitly wants to generate a public link for a dashboard or BI panel.

Do not use for internal resource URLs. Use `analysis-meta asset url-get` when applicable.

Command:

```bash
ae-cli analysis public-link create --project-id <project_id> --resource-type dashboard --resource-id <id> --effective-at "2026-07-08 00:00:00" --expires-at "2026-08-08 00:00:00" [--access-controls '{...}'] [--remark <text>] [--company-id <company_id>] [--payload '{...}']
```

Input sends `project_id`, `resource_type`, `resource_id`, `effective_at`, `expires_at`, and optional public-link fields.

Output is the gateway envelope. `data` contains the generated public-link result.
