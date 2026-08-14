# Write, confirmation, and recovery contract

## Before a write

Read the current object/domain context and show the user:

- the exact business operation;
- resolved targets and organization;
- important field or lifecycle changes;
- evidence basis and remaining unknowns;
- whether the operation is reversible;
- whether separate formal confirmation is required.

Proceed only after an explicit approval in the current conversation. Silence, a previous approval for another step, or a broad goal is not approval for a new mutation.

## Stable idempotency

Create one unique `clientRequestId` for each intended mutation. Reuse it only when retrying the same mutation after a timeout or recoverable transport failure. A changed target, effect, or payload is a new mutation and needs a new ID and confirmation.

## Formal actions

When capabilities marks an operation as requiring formal authorization:

1. Show the exact high-impact effect, including version, recipients, employee/position/cycle, cancellation, or publication scope.
2. Ask for a separate explicit confirmation in the conversation, then call the exact domain tool with one stable `clientRequestId`.
3. Expect `formal_authorization_required` with a SalesTouch browser confirmation URL. Present or open that URL for the user; do not treat conversational approval as the browser confirmation.
4. After the user approves in SalesTouch, retry the exact same tool call with the same `clientRequestId` and unchanged targets, input, instruction, and evidence references.
5. Never construct or send `formalAuthorization`, `authorizationId`, `confirmedAt`, timestamps, signatures, or proof fields. The MCP runtime and SalesTouch server create and validate the one-operation proof.
6. If the payload changes, the confirmation is denied/expired, or the server rejects the binding, stop. Obtain fresh user intent and use a new `clientRequestId`; do not downgrade to another write path.

## Result states

- `completed`: present the verified readback and evidence.
- `queued` or `running`: retain the operation reference and poll `salestouch_get_operation_status`. Do not resubmit with a new idempotency key.
- `failed` with a retryable/recoverable category: explain the failure and retry only with the same `clientRequestId` after user intent is still valid.
- guarded, permission, identity, or canonicalization failure: change the missing condition or stop. Repeated retries cannot repair it.
- disabled: report the exact readiness reason and available read-only path.

## Corrections

Use an advertised correction, update, dispute, or compensation operation when available. Never use arbitrary API calls, database access, or a different domain's write operation to imitate success.
