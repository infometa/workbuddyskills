# analysis user-cluster update

Update a condition or SQL user cluster. Discover the exact `cluster_name` first.

This is a `high-risk-write`. First run the final command with `--dry-run`, summarize the exact cluster and fields that will change, and wait for explicit user confirmation. Then run the unchanged command with `--yes`. Do not use it for ID-file membership replacement, to create a missing cluster, to change its analysis entity, or to change it between condition and SQL types.

Supplying `--definition-request` automatically starts recomputation after the definition is updated; do not call `user-cluster refresh` afterward. Updating only `--display-name` or `--remark` does not recompute. `--auto-refresh-cron` changes an existing enabled auto-refresh schedule and does not enable auto refresh. A successful update means the definition was saved, not that the new result is complete. Poll `user-cluster get` until `progress=100` and `refresh_end_time` is not older than `update_time` before using `users_num` or querying members.

The response distinguishes both paths. A definition update returns `computation.triggered_automatically=true`, `result_freshness.is_stale=true`, and normally `next_action=poll_get` with an exact capability/input pair. A display-name/remark-only update returns `computation.status=not_triggered`, `result_freshness.status=fresh`, and `next_action=none`.

Flags: `--project-id`, `--cluster-name` required. Optional: `--display-name`, `--definition-request`, `--authenticated-only`, `--remark`, `--zone-offset`, `--auto-refresh-cron`. There is no `--entity-id` update flag. When the definition changes, `definition_request.type` must match the existing cluster type; it selects the definition variant but does not change the saved type.

`display_name` is at most 80 characters and `remark` is at most 400 characters. The CLI rejects violations before dispatch. `cluster_name` is an existing exact identifier and cannot be renamed by update.

Read `user_cluster_models.md` before changing the definition. The backend validates and compiles `definition_request` inside update and refuses to modify the cluster if clarification is required. Condition definitions are saved as mixed-condition clusters.

```bash
ae-cli analysis user-cluster update --project-id <project_id> --cluster-name retained_users --display-name "Retained Users v2" --dry-run

ae-cli analysis user-cluster update --project-id <project_id> --cluster-name retained_users --display-name "Retained Users v2" --yes

ae-cli analysis user-cluster update --project-id <project_id> --cluster-name retained_users --auto-refresh-cron '0 30 2 * * ? *' --dry-run
```
