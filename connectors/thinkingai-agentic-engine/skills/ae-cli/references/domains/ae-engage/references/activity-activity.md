# engage-activity activity

> Capability ids: `engage-activity.activity.{create,update,delete,list,get,pause,end,stats,info-list}` · Domain: `engage`.

Campaign activities — activity entity management. `create`/`update` pass backend DTOs via `--payload` (native camelCase structure; `project_id` is supplied separately as a flag).

## Commands

```bash
# Create an activity (draft)
ae-cli engage-activity activity create --project-id <project_id> \
  --payload '{"activityName":"a1","activityType":"other_type","tzOffset":99,"periodType":0}'

# Update an activity
ae-cli engage-activity activity update --project-id <project_id> \
  --payload '{"activityId":"act-1","activityName":"a1","activityType":"other_type","tzOffset":99,"periodType":0}'

# Delete an activity (draft/denied/ended only, high-risk)
ae-cli engage-activity activity delete --project-id <project_id> --activity-id <activity_id> --yes

# List activities
ae-cli engage-activity activity list --project-id <project_id> [--fuzzy-field <text>] [--page 1] [--page-size 20]

# Get an activity detail
ae-cli engage-activity activity get --project-id <project_id> --activity-id <activity_id>

# Pause / End an activity (write, no dry-run)
ae-cli engage-activity activity pause --project-id <project_id> --activity-id <activity_id>
ae-cli engage-activity activity end --project-id <project_id> --activity-id <activity_id>

# Activity status distribution statistics
ae-cli engage-activity activity stats --project-id <project_id> [--fuzzy-field <text>]

# Query an activity's topics + standalone tasks
ae-cli engage-activity activity info-list --project-id <project_id> --activity-id <activity_id>
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| create | `--project-id`, `--payload` | payload = `ActivityAddDTO`. |
| update | `--project-id`, `--payload` | payload = `ActivityDTO` (`activityId` + base fields). |
| delete | `--project-id`, `--activity-id` | high-risk; requires `--yes`; no dry-run. |
| list | `--project-id` | `--fuzzy-field` / `--page` / `--page-size` optional. |
| get | `--project-id`, `--activity-id` | read. |
| pause | `--project-id`, `--activity-id` | write; no dry-run. |
| end | `--project-id`, `--activity-id` | write; no dry-run. |
| stats | `--project-id` | read; `--fuzzy-field` optional. |
| info-list | `--project-id`, `--activity-id` | read. |

## Output

- `create` / `update`: `data.activity_id`.
- `list`: `data.status_count`, `data.activity_list`, `data.pager_result`.
- `get`: `data.activity`.
- `stats`: `data.status_count`.
- `info-list`: `data.info` with `taskList` (standalone tasks) and `topicList` (topics under the activity).
  This summary intentionally omits stored QP-bearing detail fields such as `qp`,
  `triggerRule`, `completionIndicatorDef`, and `clientQp`. Use the corresponding task
  or topic detail command to obtain the semantic definitions before editing.
- `delete` / `pause` / `end`: `data.success`.

## Timezone (`tzOffset`)

When the project has **timezone disabled**, use `tzOffset: 99` (server default sentinel) on create/update. Using `8` or other offsets returns `PROJECT_TIME_ZONE_NONE` when creating topics/tasks under the activity.

When timezone is enabled, `tzOffset` must match one of the project's configured offsets. Keep activity `tzOffset` aligned with tasks/topics created under it.

## Decision Rules

- `delete` is `high-risk-write` and requires `--yes`; `pause`/`end` are state-changing `write` (no `--yes`) and do not support dry-run.
- Discover real activity IDs via `list` first; never invent IDs.
