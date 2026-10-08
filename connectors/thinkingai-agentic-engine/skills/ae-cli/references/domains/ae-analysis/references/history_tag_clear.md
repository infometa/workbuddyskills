# analysis history-tag clear

Clear history tag snapshots in a date range after explicit user confirmation.

Do not use it to cancel a running refresh or to remove the tag itself. Output confirms the requested date range was cleared; verify remaining snapshots with `history-tag list`.

Flags: `--project-id`, `--tag-name`, `--start-time`, `--end-time` required. Values use `yyyy-MM-dd`. Add `--confirmed` and `--yes` only after the user accepts the dry-run impact.

```bash
ae-cli analysis history-tag clear --project-id <project_id> --tag-name user_level --start-time 2026-07-01 --end-time 2026-07-07 --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis history-tag clear --project-id <project_id> --tag-name user_level --start-time 2026-07-01 --end-time 2026-07-07 --confirmed --yes
```
