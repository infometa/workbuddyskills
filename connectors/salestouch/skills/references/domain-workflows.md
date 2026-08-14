# SalesTouch domain workflows

Always call `salestouch_get_capabilities` before relying on the operation lists below. The server response is the source of truth for current readiness and required scopes.

## Commercial execution

Use for customers, opportunities, contacts, interactions, and tasks.

1. Discover with `salestouch_search_objects` or resolve an exact identity with `salestouch_resolve_object`.
2. Read the relevant object and pipeline context with `salestouch_read_commercial_context` and, when needed, `salestouch_read_object_context`.
3. For a confirmed change, call `salestouch_operate_commercial_execution` with one operation advertised by capabilities, resolved targets, evidence, and a stable `clientRequestId`.
4. Verify the returned customer, opportunity, contact, interaction, or task readback.

Typical operations include ensuring a customer or opportunity, recording a customer fact or interaction, upserting a contact, and creating, updating, or completing a task.

## Non-sales work reports

Use for work facts, daily/weekly reports, collaboration issues, and manager review. Do not place this work into customer or opportunity objects merely because the user also works in sales.

1. Read `salestouch_read_work_report_context` for the user or effective manager scope and requested period.
2. Preserve the privacy boundary: summarized personal work facts may be visible while raw private notes remain excluded.
3. Call `salestouch_operate_work_report` only for an operation returned as ready by capabilities.
4. Verify the submitted report or operation status. If a requested weekly/review operation is disabled, provide the read context and readiness gap instead of writing elsewhere.

## Operational forms

Use for repeatable internal data collection and operational execution, not open-ended research.

1. Read existing templates, versions, assignments, submissions, evidence, and report readiness with `salestouch_read_operational_form_context`.
2. For new work, create a draft and version draft before publication.
3. Preview recipients before distribution. Explain counts, scope, exclusions, and any incomplete source.
4. Publication, distribution, or cancellation may require separate formal confirmation. Obtain it only after showing the exact version and recipient effect.
5. After distribution, read assignments and delivery status. After submissions, preserve EvidenceRecord continuity and generate reports only from canonical evidence.

Typical operations include draft/version creation, recipient preview/refresh/cancel, publish, distribute, notification delivery/retry, assignment pause/resume/cancel, cycle snapshot, submit/correct, and report generation.

## Performance management

Use for person-position governance, goals, daily reports, support, plans, reviews, corrections, and organizational learning. Do not reduce this domain to CRM activity counts.

1. Read `salestouch_read_performance_context` for the exact person, position, cycle, or manager scope.
2. Separate observed facts, formal goals, employee acknowledgements/disputes, manager assessments, support requests, and coaching recommendations.
3. Draft before publishing where a draft/publish lifecycle exists.
4. Treat position assignments, cycle opening, formal goals/plans/reviews, correction execution, and knowledge promotion as high-impact when capabilities marks them formal.
5. Verify authoritative readback and keep disputed or unknown information visible.

## Internal organization research

Use for internal surveys, audience governance, anonymity thresholds, research missions, interviews, evidence, insights, and reports. Do not use it for external customer outreach.

1. Read `salestouch_read_organization_research_context` before planning a survey or research mission.
2. State the objective, audience, privacy mode, anonymity threshold, period, and expected decision before proposing a write.
3. Use `salestouch_operate_organization_survey` for survey lifecycle work and `salestouch_operate_research_mission` for evidence-bound research workflows only when capabilities marks the exact operation ready.
4. Internal distribution, lifecycle closure, autonomy approval, and cancellation require exact effect review and may require separate formal confirmation.
5. Never infer respondent identity from anonymous aggregates. Report suppressed cells and evidence gaps.

## Cross-domain requests

Start with `salestouch_read_operating_context`, then use only the domain tools needed to fill material evidence gaps. Maintain each domain's semantics, privacy, freshness, and permission boundary instead of flattening all records into one generic activity list.
