# analysis user-tag create-id

Create a tag by mapping imported values to an analysis entity.

Flags: `--project-id`, `--display-name`, and `--entity-id` are required. Prefer `--input-file <local_csv>`; the CLI uploads it automatically. `--input-file-id` resumes from an existing upload, while `--file-content` is only for small local tests. Exactly one of the three is allowed. Optional: `--tag-name`, `--remarks`, and conditional `--association-property`.

When supplied, `tag_name` follows the same 1-80 character machine-name rule as calculated tags. `display_name` is 1-80 characters and `remarks` is at most 400 characters.

Use `--input-file` for real local files; use `--input-file-id` only when resuming from an existing upload. Do not inline large ID lists.

Run `analysis entity id-import-options` first. For the primary user entity, column 1 is a real value of the selected `--association-property`; for a non-primary entity, it is that entity's own ID. Column 2 is `tag_value`. The headerless UTF-8 CSV must contain exactly two non-empty columns in every row.

Create returns `operation_status=PROCESSING` and `match_summary_status=PENDING`; poll `user-tag get` until progress is 100 for the final `match_summary`.

```bash
ae-cli analysis user-tag create-id --project-id <project_id> --display-name "VIP Tag" --entity-id <entity_id> --association-property email --input-file /tmp/id-tag.csv --tag-name vip_tag
```
