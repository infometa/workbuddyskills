# engage-activity approval

> Capability ids: `engage-activity.approval.{submit,approve,reject,cancel}` · Domain: `engage`.

Campaign activities — activity approval workflow. Current actions target an activity (`ApprovalActivityIdDealDTO`: `projectId` + `activityId` + `reason`); each is a state-changing `write` and does not support dry-run. `reject` requires `reason`; other actions treat `reason` as optional.

## Commands

```bash
# Submit an activity for approval
ae-cli engage-activity approval submit --project-id <project_id> --activity-id <activity_id> [--reason <reason>]

# Approve an activity
ae-cli engage-activity approval approve --project-id <project_id> --activity-id <activity_id>

# Reject an activity (reason required)
ae-cli engage-activity approval reject --project-id <project_id> --activity-id <activity_id> --reason <reason>

# Cancel/withdraw a submitted approval
ae-cli engage-activity approval cancel --project-id <project_id> --activity-id <activity_id>
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| submit | `--project-id`, `--activity-id` | `--reason` optional. Activity must have draft/pending standalone or topic tasks. |
| approve | `--project-id`, `--activity-id` | `--reason` optional. |
| reject | `--project-id`, `--activity-id`, `--reason` | `--reason` required, max 72 characters. |
| cancel | `--project-id`, `--activity-id` | `--reason` optional. |

## Output

- All actions: `data.success`.

## Decision Rules

- All approval actions are `write` (real state changes) and do not support dry-run; they do not require `--yes` (only `high-risk-write` does).
- Approve/reject require the caller to be a valid approver of the activity (enforced server-side).
- Submit requires at least one standalone or topic task under the activity that can enter approval.
- Submit and approve load complete task details and scan both standalone tasks and topic tasks before invoking the product approval service.
- Approval does not repair or normalize unsupported activity task configurations.
- If preflight returns `ACTIVITY_TASK_COMPATIBILITY_VIOLATION`, inspect `error.meta.violations`, withdraw/cancel approval when necessary, and update or recreate each reported task as scheduled, fixed-timezone, and non-experiment before resubmitting.

## Common Errors

| code | when |
|---|---|
| `ACTIVITY_NOT_FOUND` | activity id missing in project |
| `ACTIVITY_NO_APPROVAL_TASK` | activity has no standalone/topic tasks to submit |
| `ACTIVITY_TASK_COMPATIBILITY_VIOLATION` | one or more persisted activity tasks use unsupported trigger, timezone, experiment, or content-group configuration; details are in `error.meta.violations` |
| `ACTIVITY_TRIGGER_TYPE_REQUIRED` | a persisted activity task is missing its trigger type; reported inside the compatibility violation list |
| `ACTIVITY_STATUS_INVALID` | activity not in draft/pending |
| `APPROVAL_NOT_PENDING` | no under-approval record |
| `NOT_APPROVER` | caller is not a project approver |
| `REASON_REQUIRED` | reject without `--reason` |
| `REASON_TOO_LONG` | reject reason longer than 72 characters |
| `CAPABILITY_PERMISSION_DENIED` | cancel caller is neither owner nor ops-manage-other-assets |
| `TOO_FREQUENT` | concurrent approve/submit lock conflict |
