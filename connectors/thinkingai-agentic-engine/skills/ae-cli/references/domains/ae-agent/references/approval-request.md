# agent approval-request (Manage Approval Requests)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md) and read [`approval-type.md`](approval-type.md) before submitting.

Domain: **Generic Approval Request / read + write**

## Commands

```bash
ae-cli agent approval-request list --status pending --limit 20
ae-cli agent approval-request list --cursor <next_cursor> --approval-type-id skill.publish@1
ae-cli agent approval-request get --approval-request-id <request-id>
ae-cli agent approval-request submit --approval-type-id skill.publish@1 --resource-id <skill-id> --reason "Publish this Skill" --payload '{"description":"Publish this Skill"}' --client-request-id <unique-id>
ae-cli --dry-run agent approval-request cancel --approval-request-id <request-id> --expected-version 0 --client-request-id <unique-id>
ae-cli agent approval-request cancel --approval-request-id <request-id> --expected-version 0 --reason "No longer needed" --client-request-id <unique-id>
```

## Mandatory Rules

- Keep resource and request identities separate: `--resource-id` identifies the business resource; `--approval-request-id` identifies the approval aggregate.
- Generate a stable unique `--client-request-id` for each logical write. Reuse it only to replay the identical command.
- Read the latest request before cancellation and pass its `optimistic_version` as `--expected-version`.
- `--payload` must be a JSON object whose keys recursively use snake_case and match the selected type's `input_schema`.
- Request filters use opaque cursor pagination. Pass `next_cursor` unchanged to the next `--cursor` call.
- A requester may cancel their own pending request without a reason. A company manager cancelling another user's request must provide `--reason`.
- Write commands are ordinary `write` operations. They do not require `--yes`.

## Agent Company Publication

Read [Agent distribution](agent-distribution.md) for dependency preflight, immutable snapshot preview, and the complete workflow. Use `--approval-type-id agent.publish@1 --resource-id <agent-id>` with the selected type's payload contract; do not use legacy Skill-only submission commands. Agent and bundled personal Skills are reviewed together, independently of standalone Skill approvals. An approved request is not proof of successful publication: inspect its Effect result.

## Dry-run Boundary

`--dry-run` is a local method, URL, and body preview. It does not call te-agent and therefore does not verify server permissions, current request state, artifact availability, registered type state, or future conditional routing.

## Error Handling

- `approval_active_request_conflict`: inspect the active request instead of creating another one.
- `approval_version_conflict`: refresh the request/task, then decide whether to issue a new logical command with a new client request ID.
- `approval_idempotency_conflict`: do not reuse the client request ID with a changed payload.
- Permission and tenant-hidden not-found errors must not be bypassed or retried with guessed IDs.

## Transition Metadata

- Transition status: transitional
- Owning module: te-agent approval domain
- Current transport: CLI-token-only versioned REST at `/agent/api/cli/approval/v1`
- Gateway target: `approval.request.list`, `approval.request.get`, `approval.request.submit`, and `approval.request.cancel`
- Review after: 2026-11-17
- Exit condition: Migrate these commands when equivalent Gateway schemas preserve idempotency, optimistic concurrency, cursor pagination, authorization, dry-run, and structured output contracts.
