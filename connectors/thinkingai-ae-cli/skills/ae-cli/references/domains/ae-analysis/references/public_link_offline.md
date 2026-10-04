# analysis public-link offline

Use when the user wants to take one or more public links offline without deleting records.

Do not use to permanently delete links. Use `public-link delete`.

Command:

```bash
ae-cli analysis public-link offline --project-id <project_id> [--link-id <link_id>] [--link-ids '[1,2]'] [--company-id <company_id>]
```

Input sends `project_id`, optional `company_id`, and either `link_id` or `link_ids`.

Output is the gateway envelope. `data` contains the offline result.
