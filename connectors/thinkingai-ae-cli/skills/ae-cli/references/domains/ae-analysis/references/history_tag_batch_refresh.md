# analysis history-tag batch-refresh

Batch refresh history tag snapshots over one inclusive date range.

Flags: `--project-id`, `--tag-name`, `--refresh-request` required.

```bash
ae-cli analysis history-tag batch-refresh --project-id <project_id> --tag-name user_level --refresh-request '{"start_time":"2026-07-01","end_time":"2026-07-07","only_abnormal":false,"use_user_table_type":"user_table"}'
```

Input:

- `start_time` and `end_time` are required, inclusive, and use `yyyy-MM-dd`;
- `only_abnormal` is optional boolean, default `false`;
- `use_user_table_type` is optional: `user_table`, `user_backup_table_default`, or `user_backup_table_last_date`.

Do not pass the Java DTO name, camelCase fields such as `startDate`/`endDate`, or alternate `start_date`/`end_date` aliases.

Output is the gateway envelope containing the batch refresh task result.
