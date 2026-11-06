---
description: Generate a Markdown report of ChainGuard runtime security events and audit history
---

Run the ChainGuard runtime security audit history reporter and show the user the report file path and a summary of runtime interception events.

Execute this command:

```
node ${CODEBUDDY_PLUGIN_ROOT}/dist/security-guard.cjs --report
```

The command outputs JSON with `reportPath` (absolute path to the generated Markdown report) and `summary` (total events, counts by risk level, policy decision, and package ecosystem). Show the user:

1. The report file path (so they can open it)
2. A brief summary of runtime interception events (total logged events, breakdown by policy decision such as deny vs allow)

Scope and Semantics Guidelines:
- Clarify that this report summarizes historical runtime interception and audit events recorded in the local environment audit log (~/.security-guard/audit.jsonl), NOT a static security scan of the current repository.
- Do NOT label runtime interception events as confirmed vulnerabilities in the current repository.
- Do NOT output the full report content into the conversation — it stays in the file to avoid expanding model context (per O1-22 token budget principle).
- If no audit events have been recorded yet, inform the user that no runtime security events have been recorded in this environment yet. Clarify that an empty audit history does not indicate the repository is free of vulnerabilities, but simply that no intercepted package operations have occurred yet.
