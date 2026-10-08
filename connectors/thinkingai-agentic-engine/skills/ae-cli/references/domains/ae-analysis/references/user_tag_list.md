# analysis user-tag list

List accessible user tags for discovery. Use this before get/update/delete/member/history-tag commands; do not invent `tag_name`.

Flags: `--project-id` required. Optional: `--queries`, `--fields`, `--limit`, `--offset`, `--authenticated-only`.

`--queries` is a JSON array of 1-20 keywords and uses OR matching. Default `--limit` is 50; maximum is 200.

`--offset` is only for stable asset browsing. It is not a tag-member pagination strategy.
When `has_more=true`, continue only with the returned `next_offset`; do not calculate the next page locally.

Output is a paged tag inventory whose identifier is `tag_name`, the same field consumed by get/update/delete/member/history-tag commands. It is not tag members, history snapshots, or definition-build results.

Tags never accept `cluster_name`; that field belongs only to user clusters. Do not retry a tag command by substituting one identifier for the other.

```bash
ae-cli analysis user-tag list --project-id <project_id> --queries '["level","tier"]' --limit 50
ae-cli analysis user-tag list --project-id <project_id> --fields '["tag_name","display_name","users_num"]' --limit 50 --offset 0
```

For a complete catalog, use [`user_tag_export.md`](user_tag_export.md).
