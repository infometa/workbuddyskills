# personal-semantic-preference delete

Soft-delete one personal semantic preference using optimistic locking.

Use this only after explicit user confirmation to remove a saved personal preference.

Command:

```bash
ae-cli personal-semantic-preference delete --project-id <project_id> --id <preference_id> --expected-revision <revision> [--request-id <id>] --yes
```

Read the current item first and pass its revision as `--expected-revision`. This is a high-risk write; use `--dry-run` when the target is ambiguous.

Do not use this command for automatic stale/expired preference handling. Stale or low-freshness personal preferences are hidden by list filtering and backend maintenance.

Output is the gateway envelope. `data.deleted` identifies the deleted preference and status. After deletion, it should no longer appear in `personal-semantic-preference list`.
