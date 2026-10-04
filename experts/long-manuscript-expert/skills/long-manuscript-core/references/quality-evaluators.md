# Quality evaluators

The package contains 32 deterministic machine evaluators plus one separate human-review receipt gate. Machine gates never substitute for human approval.

All evaluations are local and self-contained. They do not require BookWriter, network access, connectors, credentials, the system clock, or environment variables. A result is accepted only when its invocation, evaluator bytes, policy, scene pack, evidence, artifact set, result, and receipt digests agree.

Delivery is fail-closed: missing, failed, unavailable, malformed, or human-pending gates block `delivery_ready`. For DOCX and PDF, a matching hash alone is insufficient; the independent binary inspector also checks container structure and readable content.
