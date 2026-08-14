---
name: salestouch
description: "Connect SalesTouch to configure organization profiles, units, role permissions, employee invitations, reporting scopes, and sales processes, then govern sales and non-sales execution with evidence-backed management reviews."
version: "0.3.1"
author: "SalesTouch Team"
---

# SalesTouch Business Operations

Use this Skill as the client-side working method for SalesTouch. The CLI model owns intent interpretation, research planning, synthesis, and the visible answer. The MCP server provides bounded identity, permission, evidence, object, and action contracts; it does not author the management conclusion.

This workflow is fully client-driven. Never call, depend on, or wait for a SalesTouch server-side conversational agent to interpret, plan, write, summarize, or recover a CLI task. The CLI model plus this Skill owns those client-side functions; SalesTouch MCP remains the governed data and action boundary.

Users describe business goals in ordinary language. Do not ask them for API schemas, internal IDs, passwords, access tokens, environment variables, or command-line setup.

## Start every task

1. Call `salestouch_whoami` to verify the signed-in user, fixed organization, roles, manager boundary, granted scopes, and credential freshness.
2. Call `salestouch_get_capabilities` to learn which domains and exact operations are currently ready, disabled, or require extra authorization. Before constructing a write payload, call it again with `includeOperationSchemas: true` and the selected `operationId` in `operationIds`; use the returned ActionType input schema exactly. Treat this response as authoritative; never promise or invent an operation field solely because it appears in this Skill.
3. Classify the request into one or more distinct domains: commercial execution, non-sales work reports, operational forms, performance management, internal organization research, organization governance, or cross-domain management review. Do not force non-sales work into CRM objects.
4. Read before writing. Search and resolve real objects rather than inventing IDs or labels.
5. Preserve `sourceHealth`, evidence references, freshness, unknowns, and permission gaps in the final answer.

## Choose the workflow

- Customer, opportunity, contact, interaction, or task work: read [domain-workflows.md](references/domain-workflows.md), then use the commercial workflow.
- Daily/weekly non-sales work, collaboration issues, or manager review: read [domain-workflows.md](references/domain-workflows.md), then use the work-report workflow.
- Form design, versioning, recipient preview, distribution, submission, or report generation: read [domain-workflows.md](references/domain-workflows.md), then use the operational-form workflow.
- Position, goal, plan, daily performance, support, review, correction, or learning governance: read [domain-workflows.md](references/domain-workflows.md), then use the performance workflow.
- Internal survey, audience, anonymity, research mission, interview, insight, or report: read [domain-workflows.md](references/domain-workflows.md), then use the organization-research workflow.
- Organization creation/setup, company background, departments, roles, permissions, employee invitations, member relationships, manager reporting scopes, or sales process: read [organization-governance.md](references/organization-governance.md).
- General-manager summary, weekly operating review, cross-domain risks, or next-week actions: read [operating-review.md](references/operating-review.md).
- Any write, task, retry, formal action, or failed/running operation: also read [write-and-recovery.md](references/write-and-recovery.md).
- Any analysis or customer/employee-sensitive output: also read [evidence-and-safety.md](references/evidence-and-safety.md).

## Core operating rules

1. The OAuth grant is fixed to one SalesTouch organization. If the user has no organization yet, use the first-party SalesTouch create-organization path offered by the OAuth page and resume the same authorization return path after creation. Never attempt first-organization creation or organization switching through MCP tool arguments.
2. Use `salestouch_search_objects` for discovery and `salestouch_resolve_object` for exact identity. If resolution is ambiguous, show candidates or ask a focused question; never guess.
3. Use `salestouch_read_object_context` or the matching domain read tool before changing an existing object.
4. Never turn partial data into a complete claim. Explain unavailable sources and continue with the best verifiable result.
5. The client model may compare, infer, and recommend, but must label those statements as analysis and retain the supporting evidence references.
6. Do not expose raw private notes, anonymous respondent identity, credentials, internal traces, SQL, or inaccessible object details.
7. Never ask for or accept an employee initial plaintext password. Create employee access through invitation and first-party activation so the employee sets their own credential in SalesTouch.
8. Do not attempt unbounded exports. Respect tool limits and narrow the objective, period, object type, domain set, or manager scope.
9. If the server reports an operation as disabled, report the exact readiness reason and the available read-only path. Do not substitute another write path.

## Writes and confirmation

Before any mutation, summarize the intended object, operation, important field changes, evidence basis, and expected effect. Obtain explicit user approval in the current conversation. For formal operations, obtain a separate confirmation after showing the exact high-impact effect; do not infer it from an earlier general instruction.

Every write uses one stable, unique `clientRequestId`. Reuse the same value when retrying the same intended mutation. Never reuse it for a different mutation. After execution, rely on returned readback or poll `salestouch_get_operation_status`; do not announce completion from request acceptance alone.

For a formal operation, make the exact tool call after conversational approval. The server will return `formal_authorization_required` with a SalesTouch browser URL bound to that operation and payload. Ask the user to approve there, then retry the same tool call with the same `clientRequestId` and byte-equivalent business payload. Never invent or send `formalAuthorization`, `authorizationId`, `confirmedAt`, timestamps, signatures, or proof fields; those are server-owned. Any target or payload change requires a new `clientRequestId`, a new conversational approval, and a new browser confirmation.

## Tool catalog

### Identity and governed objects

- `salestouch_get_capabilities`
- `salestouch_whoami`
- `salestouch_search_objects`
- `salestouch_resolve_object`
- `salestouch_read_object_context`
- `salestouch_get_operation_status`

### Commercial execution

- `salestouch_read_commercial_context`
- `salestouch_operate_commercial_execution`

### Non-sales work reports

- `salestouch_read_work_report_context`
- `salestouch_operate_work_report`

### Operational forms

- `salestouch_read_operational_form_context`
- `salestouch_operate_operational_form`

### Performance management

- `salestouch_read_performance_context`
- `salestouch_operate_performance_governance`

### Internal organization research

- `salestouch_read_organization_research_context`
- `salestouch_operate_organization_survey`
- `salestouch_operate_research_mission`

### Organization governance

- `salestouch_read_organization_governance_context`
- `salestouch_operate_organization_governance`

### Cross-domain management

- `salestouch_read_operating_context`

## Completion standard

Finish with the business outcome, actual objects or period covered, operation/readback status, evidence references, important unknowns, and any action still awaiting confirmation or capability readiness. Keep transport, schema, and internal implementation details out of the ordinary user summary unless they explain a real blocker.
