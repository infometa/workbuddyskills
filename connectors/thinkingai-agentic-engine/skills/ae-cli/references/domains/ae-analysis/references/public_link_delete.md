# analysis public-link delete

Use when the user explicitly wants to delete one or more public links.

Do not use to temporarily stop access while keeping records. Use `public-link offline`.

Command:

```bash
ae-cli analysis public-link delete --project-id <project_id> [--link-id <link_id>] [--link-ids '[1,2]'] [--company-id <company_id>] --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis public-link delete --project-id <project_id> [--link-id <link_id>] [--link-ids '[1,2]'] [--company-id <company_id>] --yes
```

Input sends `project_id`, optional `company_id`, and either `link_id` or `link_ids`.

Output is the gateway envelope. `data` contains the delete result.
