# agent approval-effect (Inspect and Retry Approval Effects)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Generic Approval Effect / read + high-risk-write**

## Commands

```bash
ae-cli agent approval-effect list --status failed --limit 20
ae-cli agent approval-effect list --status manual_required --approval-request-id <request-id>
ae-cli agent approval-effect get --effect-id <effect-id>
ae-cli --dry-run agent approval-effect retry --effect-id <effect-id> --expected-version 3 --expected-attempt 1 --reason "Artifact storage was restored" --client-request-id <unique-id>
ae-cli --yes agent approval-effect retry --effect-id <effect-id> --expected-version 3 --expected-attempt 1 --reason "Artifact storage was restored" --client-request-id <unique-id>
```

## Mandatory Rules

- Effect identity is independent from request and task identity. Use `--effect-id`; use `--approval-request-id` only as a list filter.
- List/get return a safe view with request/type/resource summary, status, attempt, stable failure category, and safe result reference. They do not return artifact contents, credentials, runner leases, idempotency keys, or sensitive decision payloads.
- Retry only an Effect whose latest server state is `failed` or `manual_required`. Never infer Adapter idempotency or retry a `pending`, `running`, or `succeeded` Effect.
- Immediately before retry, run `get` and pass both `optimistic_version` as `--expected-version` and `attempt` as `--expected-attempt`.
- `--reason` is required and becomes auditable retry evidence. Generate a unique `--client-request-id` for the logical retry.
- Retry is `high-risk-write`. Obtain explicit user authorization, then pass `--yes`. Do not bypass permission, tenant-hidden, state, version, attempt, or artifact errors.
- The CLI transport does not perform business retries. Refresh state and ask for a new decision after a stable conflict.

## Dry-run Boundary

`--dry-run` is only a local method, URL, and body preview. The body uses snake_case and sets the server-required `confirm_risk` field, but the preview does not verify current administrator status, live Effect state, or artifact availability, and it does not authorize actual execution or bypass the CLI confirmation gate.

## Error Handling

- `approval_effect_retry_conflict`: re-run `get`; the status, optimistic version, attempt, or runner ownership changed. Do not blindly replay stale values, and stop unless the refreshed Effect is `failed` or `manual_required`.
- Artifact unavailable/manual recovery errors: repair the underlying storage or Adapter condition before considering another retry.
- Permission and tenant-hidden not-found errors must not be bypassed or retried with guessed IDs.

## Transition Metadata

- Transition status: transitional
- Owning module: te-agent approval domain
- Current transport: CLI-token-only versioned REST at `/agent/api/cli/approval/v1`
- Gateway target: `approval.effect.list`, `approval.effect.get`, and `approval.effect.retry`
- Review after: 2026-11-17
- Exit condition: Migrate these commands when equivalent Gateway schemas preserve safe output, administrator authorization, high-risk confirmation, expected version/attempt fencing, idempotency, cursor pagination, dry-run, and structured error contracts.
