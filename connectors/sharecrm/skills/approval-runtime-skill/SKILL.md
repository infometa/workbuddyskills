---
name: "approval-runtime-skill"
description: "Used to query or process existing approval instances and approval tasks. Use when users mention approval to-dos, agree, pass, complete, reject, return, withdraw, cancel, edit approval forms, submit after filling, change handler, add sign-off node, remind, carbon copy, reply, task details, progress, or approval instances. First select a unique reference by intent; changes must confirm target and parameters; queries must not auto-escalate to changes."
apiName: "approval_runtime_skill_mcp"
---
# Approval Flow Runtime

## Scope

Only handles existing approval instances, approval tasks, activity feeds, replies, and runtime form data. Do not treat instance detail, task detail, or feed detail as a to-do query. First bind one explicit task, instance, object record, feed, or reply target, then choose the narrowest tool for that target.

## Core Rules

- This MCP skill only uses MCP tools and fixed `apiName` values.
- Read operations may execute directly; write operations must first present a business-facing preview and wait for an explicit affirmative in a later user message.
- `taskId` / `instanceId` / `objectId` / `replyId` / `feedId` are different identifiers and must not be mixed.
- `buttonType` is only for `approval_runtime_get_task_extra_data`; `actionType` is only for final approval actions such as complete or update-and-complete.
- Never fabricate field API names, field values, version values, `originalData`, `rejectToTaskId`, `previousTaskId`, `replyId`, or assignee IDs.

## Layout Identification Before Editing or Completing

When the user asks to edit, save, agree, pass, or complete an approval task, always identify the layout through `approval_runtime_get_task_extra_data` with fixed `apiName: ApprovalTaskExtraData`.

1. Determine `buttonType` from the confirmed action in current context.
2. Reuse a trusted explicit `buttonType` if one already exists for the same task and action.
3. Use these fixed mappings when the action is already uniquely identified:
   - `Agree` -> `AGREE_BUTTON`
   - `CompleteTask` -> `COMPLETE_BUTTON`
   - `Reject` -> `REJECT_BUTTON`
   - `ChangeApprover` -> `CHANGE_HANDLER_BUTTON`
   - `Retrieve` -> `RETRIEVE_BUTTON`
   - `Carbon copy` -> `CARBON_BUTTON`
   - `editForm` with trusted `executionType == update` -> `COMPLETE_BUTTON`
   - `editForm` with any other trusted or missing `executionType` -> `AGREE_BUTTON`
4. Call `approval_runtime_get_task_extra_data` with `instanceId`, `taskId`, and matching `buttonType`.
5. Route only by `approvalForm.objectFlowLayoutExists` from that result:
   - `true`: flow layout, use `approval_runtime_edit` for save and `approval_runtime_complete` for final completion
   - `false`: default layout, use `approval_runtime_update_approval_content` for save-only or `approval_runtime_update_and_complete` for save-and-complete
6. Do not use task detail, instance detail, or any other result to replace this layout judgment.

## Tool Routing

| User Intent | Tool | Fixed `apiName` | Role |
| --- | --- | --- | --- |
| View task detail or feed detail | `approval_runtime_get_task_detail` | `ApprovalFeedDetail` | Read task, to-do, or workflow instance level detail |
| View instance detail | `approval_runtime_instance_detail` | `ApprovalInstanceDetail` | Read full approval instance information |
| Find active instance by business record | `approval_runtime_get_approval_in_95f9b6fb59f0` | `ApprovalInstanceIdByObject` | Resolve the running instance from `entityId + objectId` |
| View task extra data | `approval_runtime_get_task_extra_data` | `ApprovalTaskExtraData` | Read button-scoped extra data, form layout, opinion rules, and task-side runtime data |
| View detail change data | `approval_runtime_detail_change` | `ApprovalInstanceDetailChange` | Read instance detail-line change information |
| Query rejectable targets | `approval_runtime_get_can_refuse_tasks` | `ApprovalCanRefuseTasks` | Get candidate tasks that the current task can reject to |
| Check whether a task can be retrieved | `approval_runtime_retrieve_check` | `ApprovalTaskRetrieveCheck` | Validate retrieve eligibility before retrieve |
| Save flow-layout form only | `approval_runtime_edit` | `ApprovalTaskFormEdit` | Save a flow-layout approval form without completing |
| Save default-layout form only | `approval_runtime_update_approval_content` | `ApprovalTaskDefaultFormEdit` | Save default-layout form data without completing |
| Complete a flow-layout approval task | `approval_runtime_complete` | `ApprovalTaskComplete` | Complete the approval task after flow-layout data is already saved |
| Update and complete a default-layout approval task | `approval_runtime_update_and_complete` | `ApprovalTaskUpdateComplete` | Save required data and complete in one call |
| Reject to a previous task | `approval_runtime_reject_to_before_task` | `ApprovalTaskReject` | Reject from the current task to a selected previous task |
| Retrieve an approval task | `approval_runtime_retrieve` | `ApprovalTaskRetrieve` | Perform retrieve after retrieve-check is satisfied |
| Change regular task handler | `approval_runtime_change_task_handler` | `ApprovalTaskChangeHandler` | Replace the current task assignees |
| Change free approval handler | `approval_runtime_change_free_app_b3714e5440ed` | `ApprovalTaskChangeFreeHandler` | Adjust the free-approval handler definition on the instance |
| Carbon copy / mark as read | `approval_runtime_carbon_copy` | `ApprovalTaskCarbonCopy` | Send carbon-copy style approval-side message data |
| Reply to approval feed/comment | `approval_runtime_reply` | `ApprovalTaskReply` | Create a reply or comment with `replyMessage` |
| Delete approval reply | `approval_runtime_delete_reply` | `ApprovalTaskDeleteReply` | Delete a reply by trusted reply context |

## Write Execution Rules

### Flow-layout save only

Use `approval_runtime_edit` only when `approvalForm.objectFlowLayoutExists == true`.

- `taskId` is required.
- `objectData`, `details`, `originalData`, and `originalDetails` are JSON strings when used.
- When editing the main object, `objectData` must contain the real associated record `_id`, trusted `version`, and only the fields the user explicitly wants to change.
- `originalData` must be the trusted pre-edit snapshot of the same record.

### Default-layout save only

Use `approval_runtime_update_approval_content` only when `approvalForm.objectFlowLayoutExists == false`.

- Required: `entityId`, `objectId`, `taskId`, `data`
- `data` is a JSON string containing only the fields being updated.
- `originalData` is optional, but when passed it must be the trusted pre-edit snapshot of the same record.

### Flow-layout complete

Use the fixed two-step sequence below only when `approvalForm.objectFlowLayoutExists == true`.

1. Save with `approval_runtime_edit`
2. Complete with `approval_runtime_complete`

Requirements:

- The preview must clearly state "save, then complete".
- `approval_runtime_complete` requires `taskId`, `objectId`, and `actionType`.
- `actionType` must match the confirmed completion action for the current task.

### Default-layout complete

Use `approval_runtime_update_and_complete` only when `approvalForm.objectFlowLayoutExists == false`.

- Required: `entityId`, `objectId`, `taskId`, `actionType`, `data`
- `data` is still a JSON string, not an object.
- When the main object is updated, `data` must carry only real changed fields plus any trusted record identity or version data required by the form contract.

### Reject

Before `approval_runtime_reject_to_before_task`, first call `approval_runtime_get_can_refuse_tasks`.

- `rejectToTaskId` must come from that query result.
- Primary write target is `currentTaskId + rejectToTaskId`.
- Optional form/update payload fields such as `data`, `originalData`, `entityId`, and `objectId` must still follow the real form contract for the current task.

### Retrieve

Before `approval_runtime_retrieve`, first call `approval_runtime_retrieve_check`.

- `previousTaskId` must come from trusted current retrieve context.
- Required: `instanceId`, `currentTaskId`, `previousTaskId`, `retrieveOpinion`

### Handler change

- `approval_runtime_change_task_handler`: requires `taskId` and `persons`; `persons` is the final assignee ID list.
- `approval_runtime_change_free_app_b3714e5440ed`: requires `instanceId`; `freeApprovalDef` must follow the tool schema for the current free-approval definition.

### Reply and carbon copy

- `approval_runtime_reply` requires `replyMessage`; `taskId`, `instanceId`, or `opinionId` come from trusted current feed context.
- `approval_runtime_carbon_copy` requires `type`, `taskId`, `instanceId`, and `replyMessage`.
- `replyMessage` is an object payload, not plain text; fields such as `feedId`, `content`, `attachments`, `replyToReplyId`, and visibility scope must come from real user intent and trusted current context.

### Delete reply

Use `approval_runtime_delete_reply` only with trusted current reply context.

- Prefer passing `replyId` together with the related `taskId`, `instanceId`, or `feedId` when that context is available.

## Confirmation Rules For Non-Read Operations

1. Before every write, show a business-facing preview that states the target approval item, intended action, changed fields or assignee/visibility changes, comment or opinion, and impact.
2. Do not expose raw tool names, raw payload JSON, `apiName`, or internal mappings unless the user explicitly asks.
3. Wait for an explicit affirmative in a later user message before calling the write tool.
4. Any change to target, action, field values, assignees, reject target, retrieve path, reply scope, or comment invalidates the prior confirmation and requires a new preview.
5. After confirmation, execute the write once. Do not silently chain another write except the fixed flow-layout "save, then complete" sequence.

## Target Contract

- `taskId` is for task-scoped actions.
- `instanceId` is for instance-scoped actions.
- `entityId + objectId` identifies the business record.
- `currentTaskId` is only the current running task in reject or retrieve flows.
- `rejectToTaskId` must be selected from the rejectable-target query result.
- `previousTaskId` must be taken from trusted retrieve context.
- `replyId` / `feedId` / `opinionId` belong to feed or reply actions and are not interchangeable with task or instance identifiers.

## Success Rule

Only treat the operation as successful when the tool result clearly reports success. If the result is only a validation response, a partial acceptance, or cannot independently prove the final business state, state that truthfully and stop.
