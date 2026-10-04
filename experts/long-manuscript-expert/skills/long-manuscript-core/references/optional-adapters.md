# Optional WeCom and FBS adapters

Adapters are a value-add layer, not a product prerequisite. The package first creates a stable PortIntent and continues locally when no connector is available.

- WeCom design provenance: explicit CLI/auth preflight, business-domain routing, current-operation target resolution, internal-ID non-disclosure, append-by-default writes, explicit overwrite semantics, and honest failure reporting.
- FBS design provenance: identity and entitlement reads precede optional scene/receipt calls; consume records require the same binding; probes do not prove business closure.
- External writes require an approval receipt bound to the authoritative provider/scene binding, idempotency digest, target descriptor, expected readback, and minimum data scope. A host must inject a trusted clock and an atomic durable nonce ledger; dispatch is allowed only after the ledger returns a sealed nonce-consumption receipt, which is bound into action or reconciliation evidence.
- Targets requiring internal IDs need a fresh target-resolution receipt bound to the current provider snapshot and binding fingerprint, and discovery must independently report the same fingerprint. Public results use operation-specific allowlists; raw IDs and tokens never enter the public projection.
- Every attempt has a bounded timeout. Pre-dispatch failures preserve the local manuscript workflow. Timeout, partial success, missing provider receipt, or failed readback after dispatch becomes `outcome_unknown`/reconciliation-required, blocks replay, and cannot be reported as success.
- Package acceptance tests use injected mock transports only. The package never imports connector code, credentials, or a live endpoint.
