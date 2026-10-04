# analysis user-cluster list

List accessible user clusters for discovery. Use this before any get/update/delete/member command; do not invent `cluster_name`.

Flags: `--project-id` required. Optional: `--queries`, `--fields`, `--limit`, `--offset`, `--authenticated-only`.

`--queries` is a JSON array of 1-20 keywords and uses OR matching. Default `--limit` is 50; maximum is 200.

`--offset` is only for stable asset browsing. It is not a member-data pagination strategy.
When `has_more=true`, continue only with the returned `next_offset`; do not calculate the next page locally.

Output is a paged cluster inventory, not cluster members or definition-build results.

```bash
ae-cli analysis user-cluster list --project-id <project_id> --queries '["retained","retention"]' --limit 50
ae-cli analysis user-cluster list --project-id <project_id> --fields '["cluster_name","display_name","users_num"]' --limit 50 --offset 0
```

For a complete catalog, use [`user_cluster_export.md`](user_cluster_export.md).
