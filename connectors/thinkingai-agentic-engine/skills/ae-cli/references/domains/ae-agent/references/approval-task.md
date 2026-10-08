# agent approval-task (Review Approval Tasks)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Generic Approval Task / read + write**

## Commands

```bash
ae-cli agent approval-task list --status pending --limit 20
ae-cli agent approval-task list --approval-request-id <request-id>
ae-cli agent approval-task get --task-id <task-id>
ae-cli --dry-run agent approval-task approve --task-id <task-id> --expected-version 0 --client-request-id <unique-id>
ae-cli agent approval-task approve --task-id <task-id> --expected-version 0 --note "Reviewed" --client-request-id <unique-id>
ae-cli agent approval-task reject --task-id <task-id> --expected-version 0 --reason "Missing evidence" --client-request-id <unique-id>
```

## Mandatory Rules

- Keep task and request identities separate. `--task-id` selects the actionable unit; `--approval-request-id` only filters task lists.
- Never guess task IDs. Discover current tasks with `approval-task list`, then read the chosen task with `get`.
- Read the latest task immediately before a decision and pass its `optimistic_version` as `--expected-version`.
- Approval allows an optional `--note`; rejection requires a non-empty `--reason`.
- Generate a stable unique `--client-request-id` for each logical decision. Reuse it only to replay the identical decision.
- Current server role and company membership are authoritative. A task returned earlier may become ineligible before the write.
- Write commands are ordinary `write` operations. They do not require `--yes`.

## Dry-run Boundary

`--dry-run` is a local method, URL, and body preview. It does not call te-agent and therefore does not verify current approver eligibility, live task/request versions, or future multi-step and conditional routing.

## Error Handling

- `approval_version_conflict`: refresh both the task and request before deciding whether to retry.
- `approval_idempotency_conflict`: do not reuse the client request ID with a changed action or payload.
- Permission and tenant-hidden not-found errors must not be bypassed or retried with guessed IDs.

## Transition Metadata

- Transition status: transitional
- Owning module: te-agent approval domain
- Current transport: CLI-token-only versioned REST at `/agent/api/cli/approval/v1`
- Gateway target: `approval.task.list`, `approval.task.get`, `approval.task.approve`, and `approval.task.reject`
- Review after: 2026-11-17
- Exit condition: Migrate these commands when equivalent Gateway schemas preserve task identity, current-role authorization, optimistic concurrency, idempotency, cursor pagination, dry-run, and structured output contracts.
