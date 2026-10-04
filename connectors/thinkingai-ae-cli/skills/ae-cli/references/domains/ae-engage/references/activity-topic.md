# engage-activity topic

> Capability ids: `engage-activity.topic.{create,update,remove-task,delete,get,copy}` · Domain: `engage`.

Activity topics and tasks under a topic. `copy` loads the source topic, renames it, and re-creates (no dedicated backend copy API).

## Commands

```bash
# Create a topic and its tasks under an activity
ae-cli engage-activity topic create --project-id <project_id> --payload '{ ... }'

# Update a topic and its task relations
ae-cli engage-activity topic update --project-id <project_id> --payload '{"topicId":"topic-1", ...}'

# Remove a task from its topic (high-risk)
ae-cli engage-activity topic remove-task --project-id <project_id> --task-id <task_id> --yes

# Delete a topic (high-risk)
ae-cli engage-activity topic delete --project-id <project_id> --topic-id <topic_id> --yes

# Get a topic detail
ae-cli engage-activity topic get --project-id <project_id> --topic-id <topic_id>

# Copy a topic (loads detail, renames, re-creates)
ae-cli engage-activity topic copy --project-id <project_id> --topic-id <topic_id> [--new-name <name>]
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| create | `--project-id`, `--payload` | payload = `TopicAddDTO` (camelCase). `triggerType` must be `0` (schedule single) or `1` (schedule repeat). |
| update | `--project-id`, `--payload` | payload = `TopicModifyReq` (`topicId` + fields + task lists). |
| remove-task | `--project-id`, `--task-id` | high-risk; requires `--yes`; no dry-run. Only tasks with a non-empty `topicId`. |
| delete | `--project-id`, `--topic-id` | high-risk; requires `--yes`; no dry-run. |
| get | `--project-id`, `--topic-id` | read. |
| copy | `--project-id`, `--topic-id` | `--new-name` optional (default source name + `_copy`). |

## Notes for get / copy / create

TEXT (rich text) params inside `groupContentList[].contentList[].content` need both `value` and Slate `config` (JSON string). If `config` is omitted, Hermes copy/create auto-fills  
`[{"type":"paragraph","children":[{"text":"<value>"}]}]`. See `activity-task.md` Channel content.

Topic-level audience uses `topicClusterKey` / `topicDefinitionRequest`; do **not** pass task-level `clusterKey` at topic root.

### Audience (`targetClusterType`)

| Value | Required | Notes |
|---|---|---|
| `1` (custom) | `topicDefinitionRequest` | Analysis-compatible semantic condition object. |
| `2` (existed) | `topicClusterKey` | From an existing user cluster. |
| `3` (all) | — | **Not supported for activity topics** → `TOPIC_TARGET_CLUSTER_TYPE_UNSUPPORTED`. Use standalone `engage-activity task create` for all-users. |

**`triggerMixQpVersion`:** Capability create/update/copy defaults a blank value to `"4.4"` while compiling the semantic definition.

Task-level extra conditions go in each task's inclusion-only `definitionRequest`. Keep shared conditions in `topicDefinitionRequest`; Hermes performs the topic-to-task merge through the existing domain service. Topic tasks do not have an independent audience mode. `topic get` returns the canonical task marker `targetClusterType=1`; it may be retained when mapping `taskList` into `modifyTaskList`, but no other value is accepted. Do not pass task-level `clusterKey`, all-users selection, or exclusion filters.

### Trigger (`triggerType`)

| Value | Required | Notes |
|---|---|---|
| `0` (schedule single) | `triggerTime` (`yyyy-MM-dd HH:mm`, future) | Preferred for CLI create. |
| `1` (schedule repeat) | `startDate`, `endDate`, `triggerCrontab` | |

Manual (`2`) and every triggered type (`3`-`6`) are rejected with `ACTIVITY_TRIGGER_TYPE_UNSUPPORTED`.

### Shared topic configuration

- A/B and horse-race experiments are not supported. Omit `expConfig` and use exactly one content group per topic task.
- The topic owns schedule, activity timezone, channel, frequency limits, channel touch limits, and whitelist.
- A topic task only owns its name, optional inclusion-only custom audience refinement, one content group, completion indicators, metrics, and description.
- Do not put schedule, trigger rules, channel, frequency, whitelist, experiment, or `clusterKey` on a topic task. The only accepted task-level `targetClusterType` is the canonical get response value `1`.
- Keep the topic schedule inside the parent activity period. Create/update/copy requires parent activity `mappingStatus` `0`, `2`, or `5`.

## Create Topic Orchestration

Use this workflow when a topic has a shared audience plus one or more task-level audience splits, message variants, or completion goals.

1. **Separate the intent before building the payload.** Record the parent activity, topic-level shared audience, task-level extra audience for each task, schedule, channel, message content, and completion goal/window as distinct fields. A completion goal is not an audience condition unless the user explicitly says so.
2. **Resolve the parent activity.** Use `activity list|get` to verify the exact `activityId`, editable status, activity dates, and timezone. For a repeated topic, keep `startDate` and `endDate` inside the activity period and interpret the cron in the activity timezone.
3. **Resolve a real channel.** Query `engage-setting channel list`, then inspect the selected channel before composing content. If several enabled channels match and the user has not specified a provider or an already-confirmed project default, ask which one to use instead of choosing an arbitrary ID.
4. **Read the channel content contract.** Call `engage-task task build-save-guide` with the known trigger, audience, channel type, and `channelId`. Build every `groupContentList[].contentList[].content` item from `fieldRules.channelContentSchema`; do not infer App Push keys or parameter types from memory.
5. **Prepare audience and completion inputs.** Resolve real event/property metadata and categorical values through the applicable Analysis workflow. Put the shared condition in `topicDefinitionRequest` or `topicClusterKey`, and only task-specific conditions in each task's `definitionRequest`. For a rolling condition such as "recent N days" that must be evaluated for future repeated sends, prefer a semantic custom definition; use an existing cluster only after confirming that its refresh semantics match the send cadence. Build the completion goal separately in `completionIndicatorDef`.
6. **Build one native `TopicAddDTO`.** Keep nested payload keys in camelCase. Ensure `tasks` is non-empty, each semantic definition is a JSON object, each task has channel content, and Android/iOS or other variants map to the correct task audience and message.
7. **Validate the complex payload.** Run `topic create ... --validate` while correcting the nested payload. Inspect `normalized_input` and confirm that the schedule, audience boundaries, message variants, and completion window retain the intended semantics. After `valid=true`, execute the same payload directly; do not add a redundant dry-run by default.
8. **Create exactly once.** Run `topic create` with the validated payload. A successful response only reports `data.success`; it does not provide enough evidence to declare the whole orchestration complete.
9. **Resolve IDs and verify the saved topic.** Call `activity info-list` for the parent activity, match the new topic and tasks by their names, then call `topic get` with the returned `topicId`. Verify the channel, dates, cron, semantic topic audience, each semantic task audience, content, completion goal, and draft status.
10. **Verify generated audiences before reporting completion.** Read the generated topic/task cluster keys with the applicable cluster query and wait for terminal computation state. Require `refresh_status=success`, `progress=100`, `real_available=1`, and `cluster_valid=1`. A zero-user result may be valid, but reconcile it with the discovered categorical values and business expectation. If computation fails, correct only the verified cause and re-check; do not retry an unchanged request or report the topic as fully ready.

Recommended command order:

```text
activity list/get
-> channel list/get
-> task build-save-guide
-> prepare topic audience, task audiences, content, and completion goal
-> topic create --validate
-> topic create
-> activity info-list
-> topic get
-> generated audience status checks
```

## Output

- `get`: `data.topic` (includes `topicClusterKey` for an existing audience or `topic_definition_request` plus conversion status for a custom audience).
- `create` / `update` / `remove-task` / `delete` / `copy`: `data.success`.
- `copy` may include `data.trigger_time_stale=true` when source schedule-single time is already past.

## Decision Rules

- `remove-task` and `delete` are `high-risk-write` — require `--yes`, no dry-run.
- `remove-task` only deletes **topic tasks** (`topicId` present). Standalone tasks → use `engage-task task delete`.
- `copy` duplicates the editable topic config and its tasks (not runtime/approval state).
- `copy` saves via **draft** add (`isDraft=true`), so a past schedule-single `triggerTime` is allowed; output may include `trigger_time_stale=true`. Update the time before submitting for approval.
- Prefer `topic get` as a template when inspecting channel/content fields.

## Create / update audience errors

| code | when |
|---|---|
| `TOPIC_TARGET_CLUSTER_TYPE_UNSUPPORTED` | `targetClusterType=3` (all); topics only allow 1/2 |
| `TOPIC_CLUSTER_KEY_REQUIRED` | `targetClusterType=2` missing `topicClusterKey`, or topic-root `clusterKey` alias |
| `TOPIC_DEFINITION_REQUIRED` | `targetClusterType=1` missing `topicDefinitionRequest` |
| `TOPIC_DEFINITION_INVALID` | `topicDefinitionRequest` is not a semantic condition object |
| `TARGET_CLUSTER_TYPE_INVALID` | `targetClusterType` not a known enum value |
| `ACTIVITY_TRIGGER_TYPE_UNSUPPORTED` | topic uses manual or a triggered task type |
| `ACTIVITY_EXPERIMENT_UNSUPPORTED` | topic or a topic task configures an experiment |
| `ACTIVITY_CONTENT_GROUPS_UNSUPPORTED` | a topic task has multiple experiment-style content groups |
| `TOPIC_TASK_OVERRIDE_UNSUPPORTED` | a topic task overrides shared topic settings or selects an independent cluster |
| `TOPIC_TASK_AUDIENCE_EXCLUSION_UNSUPPORTED` | a topic task definition contains exclusion filters |
| `ACTIVITY_STATUS_INVALID` | parent activity is not editable |
| `ACTIVITY_SCHEDULE_OUT_OF_RANGE` | topic schedule is outside the parent activity period |

## Copy errors

`copy` = get topic detail → rename → draft `addTopicAndTask` (no dedicated copy API). Prefer actionable codes over `INVALID_CAPABILITY_REQUEST` / mismatched i18n text like "Campaign does not exist.":

| code | when |
|---|---|
| `TOPIC_NOT_FOUND` | source `topic_id` missing |
| `TOPIC_PROJECT_MISMATCH` | topic exists but not in `--project-id` |
| `ACTIVITY_ID_REQUIRED` | source topic detail has no `activityId` |
| `ACTIVITY_NOT_FOUND` | parent activity missing / deleted / wrong project |
| `TOPIC_TASKS_REQUIRED` | source topic has no tasks |
| `ACTIVITY_STATUS_INVALID` | parent activity is approving/working/complete |
| `ACTIVITY_SCHEDULE_OUT_OF_RANGE` | source topic schedule is outside the parent activity period |
| `ACTIVITY_CONTENT_GROUPS_UNSUPPORTED` | a source topic task has multiple content groups |
| `TOPIC_COUNT_LIMIT` | activity topic count limit exceeded |
| `CHANNEL_NOT_FOUND` | source channel missing / type mismatch |
| `TASK_COUNT_LIMIT` | project task count limit exceeded |
| `RCC_SERVER_REQUIRED` | client push (`channelType=3`) but RCC server is not installed |
| `TRIGGER_TIME_REQUIRED` | schedule-single missing `triggerTime` |

Past `triggerTime` no longer fails copy; check `data.trigger_time_stale` and fix before approval.

## remove-task errors

| code | when |
|---|---|
| `TASK_NOT_FOUND` | `--task-id` missing |
| `TASK_PROJECT_MISMATCH` | task exists but not in `--project-id` |
| `NOT_TOPIC_TASK` | task has no `topicId` (standalone); use `engage-task task delete` |
| `TASK_WORKING` | topic task `mappingStatus=working`; pause/end first |
| `TASK_APPROVING` | topic task pending approval; withdraw first |
