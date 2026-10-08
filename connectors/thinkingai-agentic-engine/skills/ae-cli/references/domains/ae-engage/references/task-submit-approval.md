# engage-task task submit-approval

Submit an existing draft engagement task for approval. The legacy full save-and-submit request remains supported.
This is a regular write operation.

> Capability id: `engage-task.task.submit-approval` · Domain: `engage`.

```bash
ae-cli engage-task task submit-approval --project-id <project_id> --task-id <task_id>
```

## Parameters

| Flag | Required | Notes |
|---|---|---|
| `--project-id` / `-p` | yes | Numeric project ID. |
| `--task-id` | conditional | Existing draft task ID. Recommended after `task save`. |
| `--request` | conditional | Legacy `ApprovalSaveAndSubmitDTO` / `OperationTaskOpDTO` JSON (camelCase or snake_case). |

Provide exactly one of `--task-id` or `--request`.

## Output

- `data.task_id`

## Request notes

- Prefer `task save` followed by `submit-approval --task-id`. The server loads the persisted draft, validates its
  trigger rule, and reuses the existing save-and-submit approval workflow.
- Never put `taskId` or `task_id` inside `--request`. Existing drafts must use `--task-id`; embedded task IDs fail
  with `REQUEST_TASK_ID_NOT_ALLOWED` so request fields are never silently discarded.
- Do not reconstruct or pass `trigger_rule`. It is an internal persisted field.
- The legacy `--request` mode remains available for existing callers.
- Required body fields (server validates): `task_name`, `channel_type`, `channel_id`, `group_content_list`, `target_cluster_type`, `trigger_type`, `completion_indicator_def`, `frequency_limits`, `enable_channel_touch_limits`, `group_id`, `trigger_time_strategy`.
- Missing `expConfig` is auto-filled as `{"enableExp":false}` (same as activity task create/update).
- TEXT channel params missing `config` are auto-filled with Slate.js JSON from `value`.
- For schedule-single (`triggerType=0`), include a future `triggerTime` (and `tzOffset` / `triggerTimeStrategy` as needed).
- Prefer save → submit by task ID; do not invent `taskId` / `channelId`.

## Common Errors

| code | when |
|---|---|
| `APPROVAL_INPUT_INVALID` | neither or both of `task_id` and `request` supplied |
| `REQUEST_REQUIRED` | `--request` missing or not an object |
| `REQUEST_TASK_ID_NOT_ALLOWED` | `request.taskId` or `request.task_id` supplied; use `--task-id` |
| `REQUEST_FIELDS_REQUIRED` | required body fields absent/blank |
| `CAPABILITY_EXECUTION_FAILED` | unmapped domain failure; check `invocation_id` / Hermes logs |
