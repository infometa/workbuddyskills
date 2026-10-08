# analysis user-cluster delete

Delete a user cluster after dependency/influence review.

Do not use it to clear members, stop computation, or hide a cluster. Output confirms deletion of the exact `cluster_name`; verify it is absent from `user-cluster list`.

Flags: `--project-id`, `--cluster-name` required. Add `--confirmed` and `--yes` only after the user accepts the dry-run impact.

```bash
ae-cli analysis user-cluster delete --project-id <project_id> --cluster-name old_cluster --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis user-cluster delete --project-id <project_id> --cluster-name old_cluster --confirmed --yes
```
