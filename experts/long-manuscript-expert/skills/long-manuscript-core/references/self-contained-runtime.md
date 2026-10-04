# Self-contained runtime contract

- All core capability code, schemas, templates, references, and registries reside under `long-manuscript-core`.
- The runtime has no third-party package imports and no donor Skill lookup.
- Connector state cannot change `operationMode` or `domainScene`.
- Connector unavailability must preserve local writing, review, continuation, and Markdown delivery.
- External writes, recipients, publication, entitlement changes, and receipt storage always require their own authorization and readback contracts.
- Missing binary renderers degrade to a visible Markdown artifact; they do not turn into a false file-success claim.
