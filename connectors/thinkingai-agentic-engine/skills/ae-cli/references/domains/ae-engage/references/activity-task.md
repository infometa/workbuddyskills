# engage-activity task

> Capability ids: `engage-activity.task.{get,create,update,copy}` · Domain: `engage`.

Campaign activities — standalone tasks (tasks under an activity that do not belong to a topic). `copy` loads the source task detail, renames it, and re-creates it (no dedicated backend copy API).

## Commands

```bash
# Get a standalone task detail
ae-cli engage-activity task get --project-id <project_id> --task-id <task_id>

# Create a standalone task under an activity (webhook + existing cluster)
ae-cli engage-activity task create --project-id <project_id> \
  --payload '{ ... }'

# Update a standalone task
ae-cli engage-activity task update --project-id <project_id> \
  --payload '{"taskId":"task-1","taskName":"t1", ...}'

# Copy a standalone task (loads detail, renames, re-creates)
ae-cli engage-activity task copy --project-id <project_id> --task-id <task_id> [--new-name <name>]
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| get | `--project-id`, `--task-id` | Only standalone tasks with an `activityId`; ordinary tasks use `engage-task task get`. |
| create | `--project-id`, `--payload` | payload = `OperationTaskOpDTO`; set `activityId`, leave `topicId` empty. Only scheduled `triggerType` `0/1` is supported. |
| update | `--project-id`, `--payload` | payload = `OperationTaskOpDTO` including `taskId`. Prefer get detail as base. Only scheduled `triggerType` `0/1` is supported. |
| copy | `--project-id`, `--task-id` | `--new-name` optional (default source name + `_copy`). |

## Output

- `get`: `data.task`.
- `create`: `data.task_id`.
- `update`: `data.success`.
- `copy`: `data.task_id`, optional `data.trigger_time_stale` (true when source schedule-single time is already past).

## Payload notes (for copy / detail shape)

### Channel content

- `channelType` `1` = webhook, `2` = app_push, `3` = client_push, `4` = wechat, `5` = dou_yin`.
- `groupContentList[].contentList[].content` must be a JSON **array string**.
- **TEXT (rich text) params** must include both `value` and `config` (Slate.js JSON **string**). If `config` is missing, Hermes copy auto-fills  
  `config = [{"type":"paragraph","children":[{"text":"<value>"}]}]` as a JSON string.
- Missing `expConfig` on create/update is auto-filled as `{"enableExp":false}` (same shape as task `get`).
- A/B and horse-race experiments are not supported. Do not pass experiment fields or multiple content groups.
- `groupContentList` must contain exactly one non-experiment group. Put language variants in that group's `contentList`.

### Audience (`targetClusterType`)

| Value | Required | Notes |
|---|---|---|
| `2` (existed) | `clusterKey` | From `analysis user-cluster list/get`. |
| `1` (custom) | `definitionRequest` | Analysis-compatible semantic condition object. |
| `3` (all) | — | Do not pass `clusterKey` or `definitionRequest`. |

`get` returns `definition_request`, `definition_status`, and optional `definition_unavailable_reason`, while hiding the stored execution QP. Reuse `definition_request` as payload `definitionRequest` for an update. `copy` converts the source internally and does not require an audience field from the caller.

## Decision Rules

- `triggerType` must be `0` (schedule single) or `1` (schedule repeat). Manual (`2`) and triggered (`3`-`6`) tasks belong under `engage-task`, not `engage-activity`.
- Set `triggerTimeStrategy` to `fixed_time_zone` and `tzOffset` to the parent activity timezone. User timezone and user active time are not supported.
- Keep `triggerTime`, or repeat `startDate`/`endDate`, inside the parent activity period.
- Create/update/copy is limited to editable parent activity states: draft (`0`), paused (`2`), or denied (`5`). Project-configured count and language limits remain authoritative.
- Discover a real `task_id` via `get`/activity `info-list` first; never invent IDs.
- `copy` duplicates the editable task config (not runtime/trigger state).
- `copy` saves via **draft** add (`draft=true`), so a past schedule-single `triggerTime` is allowed; output may include `trigger_time_stale=true`. Update the time before submitting for approval.
- Standalone tasks must **not** include `topicId`; topic tasks use `engage-activity topic create` / `topic copy`.

## Copy errors

`copy` = get detail → rename → draft `add` (no dedicated copy API). Prefer actionable codes over `INVALID_CAPABILITY_REQUEST`:

| code | when |
|---|---|
| `TASK_NOT_FOUND` | source `task_id` missing |
| `TASK_PROJECT_MISMATCH` | task exists but not in `--project-id` |
| `TOPIC_TASK_FORBIDDEN` | source has `topicId` (use `topic copy`) |
| `ACTIVITY_ID_REQUIRED` | source has no `activityId` (not a standalone activity task) |
| `ACTIVITY_TRIGGER_TYPE_UNSUPPORTED` | task uses manual or a triggered task type |
| `ACTIVITY_TRIGGER_TIME_STRATEGY_UNSUPPORTED` | task does not use `fixed_time_zone` |
| `ACTIVITY_TIMEZONE_REQUIRED` | standalone task omits `tzOffset` |
| `ACTIVITY_EXPERIMENT_UNSUPPORTED` | task enables or configures an experiment |
| `ACTIVITY_CONTENT_GROUPS_UNSUPPORTED` | task has more than one experiment-style content group |
| `ACTIVITY_TIMEZONE_MISMATCH` | task timezone differs from the parent activity |
| `ACTIVITY_SCHEDULE_OUT_OF_RANGE` | task schedule is outside the activity period |
| `TRIGGER_TIME_REQUIRED` | schedule-single missing `triggerTime` |
| `CHANNEL_NOT_FOUND` | source channel missing / type mismatch |
| `TASK_COUNT_LIMIT` | project task count limit exceeded |
| `RCC_SERVER_REQUIRED` | client push (`channelType=3`) but RCC server is not installed |

Past `triggerTime` no longer fails copy; check `data.trigger_time_stale` and fix before approval. Unmapped domain `PARAMETER_ERROR` may still return `INVALID_CAPABILITY_REQUEST` with a readable fallback message.
