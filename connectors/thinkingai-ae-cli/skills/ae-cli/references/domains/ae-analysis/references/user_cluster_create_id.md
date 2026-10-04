# analysis user-cluster create-id

Create a cluster by mapping imported values to an analysis entity.

Flags: `--project-id`, `--display-name`, and `--entity-id` are required. Prefer `--input-file <local_csv>`; the CLI uploads it automatically. `--input-file-id` resumes from an existing upload, while `--file-content` is only for small local tests. Exactly one of the three is allowed. Optional: `--cluster-name`, `--remarks`, and conditional `--association-property`.

When supplied, `cluster_name` follows the same 1-80 character machine-name rule as condition/SQL clusters. `display_name` is 1-80 characters and `remarks` is at most 400 characters.

Use `--input-file` for real local files; use `--input-file-id` only when resuming from an existing upload. Do not inline large ID lists.

Run `analysis entity id-import-options` first. For the primary user entity, pass an allowed `--association-property` and put its real values in the single CSV column; `#user_id` is forbidden. For a non-primary entity, omit the flag and put that entity's own IDs in the single column. Every row must be non-empty.

Create returns `operation_status=PROCESSING` and `match_summary_status=PENDING`; it does not report submission-time counters as final matching results. Poll `user-cluster get` until progress is 100 for the final `match_summary`.

```bash
ae-cli analysis user-cluster create-id --project-id <project_id> --display-name "VIP IDs" --entity-id <entity_id> --association-property email --input-file /tmp/vip.csv --cluster-name vip_ids
```
