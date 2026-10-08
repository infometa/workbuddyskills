# analysis history-tag list

List history snapshots for a tag. Discover the exact `tag_name` with `user-tag list` first.

Do not use it for tag definitions, member rows, or statistics. Output is the available snapshot inventory used to select dates for later commands.

Flags: `--project-id`, `--tag-name` required.

```bash
ae-cli analysis history-tag list --project-id <project_id> --tag-name user_level
```
