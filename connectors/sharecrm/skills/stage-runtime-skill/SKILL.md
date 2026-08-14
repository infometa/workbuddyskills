---
name: "stage-runtime-skill"
description: "Used to query or process existing stage accelerator instances, stages, and tasks. Use when the user mentions stage status, stage tasks, completion, submit after filling, save flow layout form, terminal-state prerequisite task, returned task, move to stage, trigger, reactivate, cancel, change handler, recalculate assignees, disassociate, asynchronous move-to result, or rollback validation. First select a unique reference by intent; changes must confirm the target and parameters; queries or validations must not automatically perform changes."
apiName: "stage_runtime_skill_mcp"
---
# Stage Accelerator Runtime

## Scope

Only handles existing stage accelerator instances, stages, tasks, and their runtime data. Do not use it for stage accelerator definitions, nodes, publishing, start or stop, or configuration deletion.

This skill only handles explicitly identified instances, stages, tasks, stage tasks, and business records. Do not treat instance detail, task detail, or validation results as authorization to write.

## Tool Routing

| User Intent | Tool | Type | Primary Target | Role |
| --- | --- | --- | --- | --- |
| Validate whether rollback to a target stage is possible | `stage_runtime_back-to-validate` | Read | `workflowInstanceId` + `stageId` | Check whether rollback is allowed; result only, no automatic move |
| Query stage instance by business object | `stage_runtime_get-instance-id-by-object-id` | Read | `entityId` + `objectId` | Resolve the current stage instance from a business record |
| Cancel an entire stage instance | `stage_runtime_cancel` | Write | `entityId` + `objectId` | Cancel the full stage instance for the business record |
| Move to a specific target stage | `stage_runtime_move-to` | Write | `workflowInstanceId` + `stageId` | Move an instance to an explicit target stage |
| Query asynchronous move result | `stage_runtime_query-move-to-result` | Read | `jobId` | Query the result of `move-to` asynchronous execution |
| Validate whether reactivation is allowed | `stage_runtime_reactive-validate` | Read | `workflowInstanceId` | Check whether reactivation may proceed; result only, no automatic reactive |
| Reactivate instance and enter a specific stage | `stage_runtime_reactive` | Write | `workflowInstanceId` + `activeStageId` | Reactivate a stage instance and enter the specified stage |
| Trigger a stage instance for a business object | `stage_runtime_trigger` | Write | `entityId` + `objectId` + `sourceWorkflowId` | Trigger a stage flow on a business record |
| Manually change task handler | `stage_runtime_change-task-handler` | Write | `taskId` + `candidateIds` | Replace current task handlers with explicit user IDs |
| Complete returned task and move to target stage | `stage_runtime_complete-back-to-task` | Write | `workflowInstanceId` + `stageId` | Complete a returned task and move to a stage, with optional default-layout or flow-layout data |
| Complete terminal-state prerequisite task | `stage_runtime_complete-terminal-pre-task` | Write | `taskId` | Complete a terminal pre-task with required task data |
| Directly complete a stage task | `stage_runtime_complete` | Write | `taskId` | Complete a task without field updates |
| Disassociate task from specified business records | `stage_runtime_disassociate` | Write | `taskId` + `objectIds` | Remove business record associations from the task |
| Only save flow layout form | `stage_runtime_edit` | Write | `taskId` | Save flow-layout form data without completing |
| View task details | `stage_runtime_get-task-by-id` | Read | `taskId` | Read task status, task data, and writable task context |
| View tasks by instance and stage | `stage_runtime_get-tasks-info-by-instance-id-and-stage-id` | Read | `workflowInstanceId` + `stageId` | Read tasks under a given instance and stage |
| Recalculate stage task assignees | `stage_runtime_regenerate-stage-tasks-handler` | Write | `stageTaskId` | Recalculate handlers for a stage task |
| Recalculate runtime task assignees | `stage_runtime_regenerate-task-handler` | Write | `taskId` | Recalculate handlers for a runtime task |
| Complete task after updating default layout fields | `stage_runtime_update-and-complete` | Write | `taskId` | Update default-layout task data and complete in one call |

## Read And Validation Rules

- `stage_runtime_back-to-validate` is a pure validation read. It may execute directly once the target instance and target stage are confirmed. It only reports whether rollback is allowed and must not automatically call `stage_runtime_move-to` or `stage_runtime_complete-back-to-task`.
- `stage_runtime_reactive-validate` is also validation-only. It may only report whether reactivation is allowed and must not automatically call `stage_runtime_reactive`.
- `stage_runtime_get-task-by-id` is the primary read tool for task identity, task state, returned task context, and task-editable data.
- `stage_runtime_get-tasks-info-by-instance-id-and-stage-id` is the primary read tool for stage-scoped task lists under a known instance.
- `stage_runtime_get-instance-id-by-object-id` is the record-to-instance lookup path when the user starts from `entityId + objectId`.
- `stage_runtime_query-move-to-result` is only for `jobId` returned by `stage_runtime_move-to`.

## Completion, Editing, And Movement Rules

### Regular completion

Use `stage_runtime_complete` when the task should be completed without changing business fields in the same request.

- Its `data` is only task-side associated data.
- Do not treat it as field-update JSON.

### Default-layout update and complete

Use `stage_runtime_update-and-complete` when the user needs to update default-layout fields and complete together.

- `taskId` is required.
- `data` must be the wrapper object required by the task contract.
- `data.updateJson` must be a JSON string containing real writable field changes only.

### Flow-layout save only

Use `stage_runtime_edit` only to save flow-layout form data.

- It does not complete the task.
- `objectData`, `details`, `originalData`, and `originalDetails` are string parameters whose contents must be valid JSON.

### Returned task completion

Use `stage_runtime_complete-back-to-task` when the task is a returned task and the business action is to complete it and move to a target stage.

- Before this write, first run `stage_runtime_back-to-validate`.
- `workflowInstanceId` and `stageId` must both be explicit and confirmed.
- `data` is for default-layout data.
- `flowLayoutEditData` is for flow-layout save data and may include `taskId`, `objectData`, `details`, `optionInfo`, `originalData`, `originalDetails`, and `notValidate`.

### Terminal pre-task completion

Use `stage_runtime_complete-terminal-pre-task` only for terminal-state prerequisite tasks.

- At least one of the required task data payloads must be provided according to the task contract.
- Do not replace it with regular `complete`.

### Rollback and move

Use `stage_runtime_move-to` only with an explicit target stage.

- When the user is effectively rolling back to an earlier stage, run `stage_runtime_back-to-validate` first.
- A passed validation is not authorization to execute the move.
- Do not guess "previous stage" or "last stage"; `stageId` must be explicitly determined.

### Reactivation

Before `stage_runtime_reactive`, first run `stage_runtime_reactive-validate`.

- Even if validation passes, reactivation still needs a separate write preview and explicit confirmation.
- `activeStageId` must be explicit and confirmed.

## Async Rules

- `stage_runtime_move-to` may run asynchronously. When it returns `jobId`, only `stage_runtime_query-move-to-result` may be used to query that async result.
- Continue async result polling only when the service provides a polling interval such as `queryIntervalSecond`; otherwise report that the request was accepted and the final state is unverified.
- `stage_runtime_complete-back-to-task` is special: its `async` default is `true`. To force synchronous execution, explicitly pass `false`.
- For other asynchronous stage operations without a dedicated result-query path in this skill, do not report accepted requests or `jobId` as final business success.

## Write Data Rules

- Arrays and objects must follow the target tool contract exactly.
- Field updates may only use real writable fields returned by task context or explicitly provided by the user.
- Do not fabricate `stageId`, `activeStageId`, `candidateIds`, `objectIds`, `sourceWorkflowId`, `data`, `flowLayoutEditData`, `objectData`, `originalData`, or `version-like` concurrency fields.
- Risk flags such as `ignoreNoBlockValidate`, `ignoreSkipInNoBlockValidate`, `noBlockValidate`, `notValidate`, and related bypass fields default to omitted or `false`.
- Only pass a validation-bypass flag as `true` when the user explicitly requests it, understands the impact, and confirms that exact flag in the final write preview.

## Identifier Contract

- `entityId` is the business object API name.
- `objectId` is the business record ID.
- `workflowInstanceId` is the stage accelerator runtime instance ID.
- `stageId` is the explicit rollback or move target stage.
- `activeStageId` is the stage to enter after reactivation.
- `taskId` is the runtime task ID.
- `stageTaskId` is the stage task ID and must not be mixed with `taskId`.
- `activityId` is only optional task-detail context.
- `jobId` is only for `stage_runtime_query-move-to-result`.
- `candidateIds` must be real user IDs.
- `objectIds` must be real business record IDs.

## Write Secondary Confirmation

Before every write, present a final business-facing preview and wait for an explicit affirmative in a later user message for the same unchanged operation.

- The preview should state the recognizable stage instance or task target, target stage when applicable, field changes or handler or association changes, comment, async choice, and impact scope.
- Do not expose raw tool names, raw payload JSON, or internal IDs unless the user explicitly asks.
- Validation results, parameter clarification, and read-only outputs are not authorization.
- Any change to target, target stage, action, task data, handler list, associated records, async choice, validation bypass flags, or comment invalidates the prior confirmation and requires a new preview.
- After valid authorization, execute the write once. Do not silently chain another write.

## Result Reporting

Report the actually executed operation, target, server result, and any read-only verification evidence.

- Only treat the operation as successful when the response clearly proves success.
- For async acceptance without a terminal result, report that the request was accepted and the final business state remains unverified.
