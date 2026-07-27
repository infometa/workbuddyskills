---
name: career-broker-core
description: Internal-only shared references, setup guides, and helper scripts for the Tencent Career Broker expert. Do not invoke directly for user tasks; other skills and the main agent read these resources for runtime rules, setup guidance, capability registry, and MCP inspection.
disable-model-invocation: true
user-invocable: false
---

# Career Broker Core Resources

This internal skill exists only to keep the expert package structure aligned with the WorkBuddy Agent expert specification:

- shared reference content is stored under `skills/career-broker-core/references/`
- setup documents are stored under `skills/career-broker-core/references/setup/`
- shared helper scripts are stored under `skills/career-broker-core/scripts/`

Do not route user requests to this skill directly. It is a shared resource container for the main agent and other career-broker skills.
