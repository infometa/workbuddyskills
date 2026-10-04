# personal-semantic-preference get

Get one personal semantic preference by ID.

Use this command after `personal-semantic-preference list` identifies a likely current-user preference. Pass `--mark-used` when the preference is adopted for the answer, query path, or as the matched target for an update.

Command:

```bash
ae-cli personal-semantic-preference get --project-id <project_id> --id <preference_id> [--mark-used]
```

Input uses `project_id`, `id`, and optional `mark_used`. `id` must be the exact `preference_<id>` value returned by list/add.

Do not use this command as a keyword search or asset catalog lookup. Do not call it repeatedly for every catalog row. Do not use `--mark-used` for a candidate that turns out not to match the user's intent or is only inspected and then rejected.

Output is the gateway envelope. `data.preference` contains the full personal preference, including content, complete ordered `resource_refs`, and revision. When `--mark-used` is set, the backend increments `heat_count` and updates `last_used_at` for that record.
