# analysis user-tag delete

Delete a user tag after dependency/influence review.

Do not use it to clear history snapshots or hide a tag. Output confirms deletion of the exact `tag_name`; verify it is absent from `user-tag list`.

Flags: `--project-id`, `--tag-name` required. Add `--confirmed` and `--yes` only after the user accepts the dry-run impact.

```bash
ae-cli analysis user-tag delete --project-id <project_id> --tag-name old_tag --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis user-tag delete --project-id <project_id> --tag-name old_tag --confirmed --yes
```
