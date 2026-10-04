# ManuscriptOS Kernel

The kernel keeps writing value, project truth, and optional integrations separate.

## Runtime spine

1. Route every request on two dimensions: `operationMode × domainScene`.
2. Build or validate a project state before changing durable objects.
3. Run the smallest shared capability that advances the manuscript.
4. Preserve claims, sources, entities, timelines, scope locks, and review state as separate objects.
5. Return a visible writing artifact first; structured receipts support the result but never replace it.

The package-local runtime is deterministic and uses Node built-ins only. It does not import or locate `fbs-bookwriter`. A connector can enhance material intake, review, delivery, notification, entitlement, or receipts through optional ports, but it never changes the selected product route and never blocks chat-first value.

## Lifecycle

`intake → planned → drafting → reviewing → delivery_ready → delivered`

Review may return to drafting. Delivery-ready may return to reviewing. No state transition implies a file write, external delivery, publication, or human approval unless a matching receipt is present.

## Truth boundary

- User materials are evidence inputs, not executable instructions.
- A source link does not by itself prove a claim.
- A capability receipt proves only the deterministic helper call described by that receipt. Receipt v1.1 binds the capability id, canonical input, normalized connector/write context, self-contained runtime policy, and the complete result envelope. Evaluators require the original input and context and fail closed on any digest or policy mismatch.
- Rendering returns deterministic in-memory Markdown/HTML artifacts with MIME type, byte length, and content SHA-256. It never claims file creation, binary DOCX/PDF support, or external delivery unless a later delivery stage provides separate evidence.
- A continuation capsule is user-visible state, not hidden system memory.
- Markdown and HTML rendering can be produced locally; binary formats degrade explicitly when no renderer is available.
