# engage-task push-record query

Query delivery and push records for an engagement task. Hermes automatically selects scheduled, user-time-zone, or triggered record data based on the task configuration.

> Capability id: `engage-task.push-record.query` · Domain: `engage`.

```bash
ae-cli engage-task push-record query \
  --project-id <project-id> \
  --task-id <task-id> \
  --page-num 1 \
  --page-size 20
```

## Parameters

- `--project-id`, `-p`: Numeric project ID.
- `--task-id`: Engagement task ID.
- `--page-num`: Optional page number for scheduled tasks. Defaults to `1`.
- `--page-size`: Optional page size for scheduled tasks. Defaults to `20`.
- `--start-date`: Optional start date in `yyyy-MM-dd` format. Must not be after `--end-date`.
- `--end-date`: Optional end date in `yyyy-MM-dd` format. Must not be before `--start-date`.

## Output

Returns `record_type`, `items`, `total`, and pagination metadata when the selected backend record type is paginated.

The count fields depend on `record_type`:

| `record_type` | Actual push field | Successful push field |
| --- | --- | --- |
| `scheduled` | `actual_trigger_num` | `trigger_num` |
| `user_time_zone` | `actual_trigger_num` | `trigger_num` |
| `triggered` | `actual_push_num` | `push_success_num` |

Scheduled records and nested user-time-zone execution records use stable English `status_name`
values:

| `status` | `status_name` |
| --- | --- |
| `0` | `Waiting` |
| `1` | `Ready` |
| `2` | `Pushing` |
| `3` | `Sent` |
| `4` | `Retrying` |
| `5` | `Failed` |

Top-level user-time-zone task instances use a separate status enum:

| `status` | `status_name` |
| --- | --- |
| `0` | `Sending` |
| `1` | `Sent` |
| `2` | `Finished` |

Use `status` and the count fields for automated assertions. `status_name` never returns an internal
`hermes.*` localization key.
