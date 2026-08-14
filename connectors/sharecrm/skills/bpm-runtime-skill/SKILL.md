---
name: "bpm-runtime-skill"
description: "Used to query or process existing business flow instances and business flow tasks. Use when the user mentions business flow to-dos, completion, submit after filling, editing task data, creating related data, executing a specified operation, changing or recalculating handlers, reminding, triggering, canceling, retrying, task details, buttons, lanes, instance forms or logs. First select a unique reference by intent; changes must confirm the target and parameters, and queries must not auto-escalate to changes."
apiName: "bpm_runtime_skill_mcp"
---
# Business Flow Runtime

## Scope

Only handles existing business flow instances, business flow tasks, lanes, instance forms, and runtime task data. Do not use it for business flow definitions, node configuration, publishing, enabling or disabling, or configuration deletion.

This skill only handles explicitly identified tasks, instances, lanes, or business objects. Do not treat instance detail, instance list, lane queries, or task detail as a to-do query.

## Tool Routing

| User Intent | Tool | Type | Primary Target | Use |
| --- | --- | --- | --- | --- |
| Complete current task | `bpm_runtime_task_complete-task` | Write | `taskId` | Complete the current business flow task without editing task data |
| Edit and complete, or update fields then complete | First `bpm_runtime_task_get-task-info`, then choose `bpm_runtime_task_update-data-and-complete-task` or `bpm_runtime_task_edit` + `bpm_runtime_task_complete-task` by `layoutType` | Write | `taskId` + `entityId` + `objectId` | Route completion by layout after confirming the current writable task form |
| Only edit task data | `bpm_runtime_task_edit` | Write | `taskId` | Save task form or business data without completing |
| Complete and create related data | `bpm_runtime_task_complete-and-create-task-data` | Write | `taskId` + activity ID | Complete the current task and create the required related business data in one operation |
| Execute specified task operation | `bpm_runtime_task_operate-task` | Write | `taskId` + `type` | Execute a concrete task-side operation such as a button-driven action identified in current context |
| View task details | `bpm_runtime_task_get-task-info` | Read | `id` (`taskId`) | Read task status, layout, current data, and writable-task context |
| View available buttons | `bpm_runtime_task_get-button-by-task-id` | Read | `taskIds` | Read task-level executable buttons or actions for the specified tasks |
| View tasks by lane | `bpm_runtime_task_get-task-info-by-lane-id` | Read | `laneId` + workflow and instance context | Read tasks that belong to a specific lane |
| View an instance form of a confirmed type | `bpm_runtime_instance_get-instance-form` | Read | `workflowInstanceId` + `instanceFormType` | Read an instance-level form when the form type is already known |
| Query instances by business record | `bpm_runtime_instance_get-instances-by-object` | Read | `objectId` | Read business-flow instances associated with a record |
| Find tasks by instance or view instance log | `bpm_runtime_instance_get-instance-log` | Read | `workflowInstanceId` | Read instance log data and locate task IDs under the instance |
| Cancel instance | `bpm_runtime_instance_cancel` | Write | `id` (`workflowInstanceId`) | Cancel an existing business flow instance |
| Trigger instance | `bpm_runtime_instance_trigger` | Write | `id` (`workflowDefinitionId`) + `objectId` | Trigger a business flow definition for a business record |
| Retry instance after-action | `bpm_runtime_instance_after-action-retry` | Write | `instanceId` | Retry a failed or pending instance-level after-action |
| Retry task after-action | `bpm_runtime_task_after-action-retry` | Write | `taskId` | Retry a failed or pending task-level after-action |
| Manually change handler | `bpm_runtime_task_change-task-handler` | Write | `taskId` + `candidateIds` | Replace the current task handler list with explicit user IDs |
| Recalculate handler | `bpm_runtime_task_refresh-handler-by-task-id` | Write | `taskId` | Recalculate the handler assignment for the specified task |
| Remind specified handler | `bpm_runtime_task_remind` | Write | `taskId` + `remindPersons` | Send a reminder to specified handlers on the task |

## Layout Identification Before Editing And Completing

When the user asks to edit fields and complete the current BPM task, first call `bpm_runtime_task_get-task-info` for that same `taskId`, then route by `layoutType`.

| `layoutType` | Path |
| --- | --- |
| `defaultLayout` | Use `bpm_runtime_task_update-data-and-complete-task` to update fields and complete |
| `objectFlowLayout` | Use `bpm_runtime_task_edit` to save, then `bpm_runtime_task_complete-task` to complete |
| Missing, conflicting, or any other value | Stop and resolve the layout explicitly; do not guess or downgrade to another write path |

The flow-layout path is a closed two-step sequence for the same task and unchanged parameters. The final preview must state "save, then complete". After one later explicit user confirmation, run `bpm_runtime_task_edit` first and run `bpm_runtime_task_complete-task` only if the save succeeds.

## Read Tool Usage Rules

- `bpm_runtime_task_get-task-info` is the primary read tool for task identity, task state, and `layoutType`.
- `bpm_runtime_task_get-button-by-task-id` is the primary read tool when the final executable action or task operation `type` must be confirmed.
- `bpm_runtime_task_get-task-info-by-lane-id` is only for lane-scoped task reads; do not use it to replace a task-detail read.
- `bpm_runtime_instance_get-instance-form` only reads an already confirmed instance form type; do not use it to locate `taskId`, `workflowId`, or `laneId`, and do not treat it as the current task form.
- `bpm_runtime_instance_get-instances-by-object` is the record-to-instance lookup path when starting from a business record.
- `bpm_runtime_instance_get-instance-log` is the preferred read path for locating task IDs under a confirmed instance and for viewing instance execution logs.

## Write Tool Usage Rules

### Task completion

Use `bpm_runtime_task_complete-task` only when the task should be completed without changing task data in the same operation.

### Edit then complete

When field updates are required before completion:

- First read `bpm_runtime_task_get-task-info`
- Route by `layoutType`
- `defaultLayout`: use `bpm_runtime_task_update-data-and-complete-task`
- `objectFlowLayout`: use `bpm_runtime_task_edit`, then `bpm_runtime_task_complete-task`

### Task-only edit

Use `bpm_runtime_task_edit` only to save task data. Do not treat it as completion.

### Complete and create related data

Use `bpm_runtime_task_complete-and-create-task-data` only when the user explicitly needs both task completion and creation of related data for the specified activity.

### Task operation execution

Use `bpm_runtime_task_operate-task` only when the operation `type` is explicitly provided by the user or already confirmed from task buttons in current context. Do not infer `type` from natural-language intent alone.

### Instance operations

- `bpm_runtime_instance_cancel` is for an existing runtime instance identified by `workflowInstanceId`.
- `bpm_runtime_instance_trigger` is for starting a flow definition on a business record and uses the flow definition ID, not the runtime instance ID.
- `bpm_runtime_instance_after-action-retry` retries instance-level after-actions only.

### Task-side recovery and assignment

- `bpm_runtime_task_after-action-retry` retries task-level after-actions only.
- `bpm_runtime_task_change-task-handler` requires explicit user IDs in `candidateIds`.
- `bpm_runtime_task_refresh-handler-by-task-id` recalculates assignment instead of manually replacing candidate IDs.
- `bpm_runtime_task_remind` sends reminders to the specified task handlers.

## Execution Rules

1. First classify the unique target and action. Stop when the target ID is missing, the target type is unclear, the candidate is not unique, the current status conflicts, or required parameters are incomplete.
2. Read tools may execute directly, but they only answer or collect facts and must never auto-escalate to a write.
3. Write tools must use the narrowest confirmed target and parameters from current context. Do not fabricate actions, IDs, field payloads, candidate IDs, `type`, or related activity IDs.
4. Only the confirmed `objectFlowLayout` path may execute the fixed two-step `bpm_runtime_task_edit` then `bpm_runtime_task_complete-task` sequence.
5. After a write, use only the narrowest supporting read path needed for verification. Do not chain a second write because of verification.

## Identifiers And Data Contract

- `taskId` is only for task operations.
- `instanceId` or `workflowInstanceId` is only for instance operations.
- `laneId` is only for lane queries.
- `entityId + objectId` identifies the business object and record.
- `candidateIds` and `remindPersons` must be real user IDs.
- The `id` used by `bpm_runtime_instance_cancel` is the runtime instance ID.
- The `id` used by `bpm_runtime_instance_trigger` is the flow definition ID.
- Those two `id` values have different meanings and must not be mixed.
- When the user refers to "the first one" or "the Nth one", only bind it from the most recently displayed same-type list in current session.
- Business data may only contain real, writable field differences for the current task form. Do not pass full records, empty JSON, double-encoded payloads, or system fields unless the selected tool contract explicitly requires them.

## Write Secondary Confirmation

Before every write, display a final business-facing preview and wait for an explicit affirmative in a later user message for the same unchanged operation.

- The preview should state the target business-flow item, intended action, changed fields or handler changes, opinion if any, impact scope, and any retry or cancel risk.
- Do not expose raw tool names, raw payload JSON, or internal IDs unless the user explicitly asks.
- The initial request, parameter clarification, read-only results, and the preview itself are not authorization.
- Any change to target, action, field data, handler list, retry scope, reminder recipients, opinion, or risk invalidates the prior confirmation and requires a new preview.
- After valid authorization, execute the write once. Do not ask again unless the operation changes.

## Result Reporting

Report the actually executed operation, target, server result, and any read-only verification evidence. If the final business state cannot be independently verified, state that explicitly instead of overstating success.
