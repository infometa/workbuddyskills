# analysis public-link update

Use when the user wants to edit an existing public link.

Do not use to take a link offline. Use `public-link offline`.

Command:

```bash
ae-cli analysis public-link update --project-id <project_id> --link-id <link_id> --effective-at "2026-07-08 00:00:00" --expires-at "2026-08-08 00:00:00" [--access-controls '{...}'] [--remark <text>] [--company-id <company_id>] [--payload '{...}']
```

Input sends `project_id`, `link_id`, effective/expiration time, and optional public-link fields.

Output is the gateway envelope. `data` contains the update result.
