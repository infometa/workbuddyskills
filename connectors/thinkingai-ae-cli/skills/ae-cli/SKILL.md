---
name: ae-cli
display_name: ThinkingAI AE
display_name_en: ThinkingAI AE
description: Use ae-cli to query and manage data, analytics, metadata, tracking, knowledge bases, Agent resources, Engage, DataOps, Community, teams, and system administration in the configured ThinkingAI AE environment.
description_zh: 使用 ae-cli 查询和管理 ThinkingAI AE 环境中的数据、分析、元数据、埋点、知识库、Agent、Engage、DataOps、社区、团队与系统资源。
description_en: Use ae-cli to query and manage data, analytics, metadata, tracking, knowledge bases, Agent resources, Engage, DataOps, Community, teams, and system resources.
version: 1.0.0
author: ThinkingData
---

# ThinkingAI AE CLI

Use `ae-cli-workbuddy` as the only execution path for ThinkingAI AE operations. It reads the host and credentials selected during the WorkBuddy connection flow without sharing state with the user's normal `ae-cli` installation. Do not switch hosts during a business task; ask the user to reconnect the connector when a different AE environment is required.

## Route the request

Read only the matching domain manual before composing a command:

- Analysis, reports, dashboards, metrics, events, properties, tracking plans, and governance: @references/domains/ae-analysis/SKILL.md
- Capability discovery and long-tail gateway operations: @references/domains/ae-capability/SKILL.md
- Metadata data tables and property bindings: @references/domains/ae-metadata/SKILL.md
- Knowledge-base discovery: @references/domains/ae-kb-discovery/SKILL.md
- Knowledge-base operations and retrieval: @references/domains/ae-kb/SKILL.md
- Local file import and offline data: @references/domains/ae-data-integration/SKILL.md
- SDK integration guidance: @references/domains/ae-data-integration-helper/SKILL.md
- Tracking-plan generation: @references/domains/ae-generate-tracking-plan/SKILL.md
- Tracking-code generation: @references/domains/ae-generate-tracking-code/SKILL.md
- Engage: @references/domains/ae-engage/SKILL.md
- DataOps: @references/domains/ae-dataops/SKILL.md
- Community analysis and reporting: @references/domains/ae-community/SKILL.md
- Agent, approval, automation, model, MCP, Skill, attachment, and memory resources: @references/domains/ae-agent/SKILL.md
- Using an existing local Agent: @references/domains/ae-use-agent/SKILL.md
- Agent teams and TeamRuns: @references/domains/ae-team/SKILL.md
- System administration: @references/domains/ae-system/SKILL.md
- Global or multi-cluster analysis routing: read both @references/domains/ae-analysis/SKILL.md and @references/domains/ae-analysis-global/SKILL.md

Follow any additional reference-routing requirement in the selected domain manual. Do not load unrelated domain manuals or complete command indexes.

## Execution rules

- Reference manuals show commands with the generic `ae-cli` executable. When executing any referenced command in WorkBuddy, replace only that leading executable with `ae-cli-workbuddy`. Never execute bare `ae-cli` from this connector.
- Treat the selected domain manual and its referenced files as the command contract. Never invent commands, flags, IDs, schemas, or payload fields.
- Use JSON output. Parse the top-level `ok`, `data`, `error`, `meta`, and `_notice` fields before answering.
- Keep JSON results on stdout and diagnostics on stderr. Preserve request IDs and actionable error details.
- Resolve project and resource identifiers with documented list or search commands before dependent operations unless the exact identifier was verified in the current conversation.
- Use validation or dry-run when required by the domain manual. Never treat a dry-run as an executed write.
- Require explicit user confirmation immediately before deletions, permission changes, cancellations, or any operation documented as high risk. Pass `--yes` only after that confirmation.
- If authentication is missing or expired, tell the user to reconnect this connector in WorkBuddy. Do not start a separate interactive login from a business task.
- Reply in the user's language while preserving command names, identifiers, JSON keys, and business data exactly.
