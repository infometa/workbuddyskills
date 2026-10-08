# analysis history-tag refresh

Refresh one history tag snapshot.

Do not use it to refresh a date range or change the tag definition; use batch refresh or tag update respectively. Output means the refresh was submitted, not that computation has completed.

Flags: `--project-id`, `--tag-name`, `--refresh-date` required. Optional: `--use-user-table-type`.

```bash
ae-cli analysis history-tag refresh --project-id <project_id> --tag-name user_level --refresh-date 2026-07-01
```
