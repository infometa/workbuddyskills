# Evidence-backed operating review

Use this workflow for a general manager, business leader, or department manager asking for a weekly/monthly operating summary across sales and non-sales work.

## 1. Establish scope

Call `salestouch_whoami` and confirm the fixed organization and effective manager boundary. Clarify the reporting period only if the user's wording cannot be mapped safely to dates. Use exact dates in the output.

## 2. Read the operating manifest

Call `salestouch_read_operating_context` with the requested period and the applicable domains:

- `commercial`
- `work_report`
- `operational_form`
- `performance`
- `organization_research`

Do not omit a requested domain merely because another domain has more data.

## 3. Fill material gaps

Inspect each domain slice's status, freshness, evidence, and gaps. Call the matching domain read tool only when it can answer a material management question or resolve a highlighted gap. Use object search/resolve/context for exact customer, opportunity, person, position, form, or survey drill-down.

## 4. Synthesize in the CLI

The visible review is authored by the CLI model from returned evidence. Use this structure unless the user requests another artifact:

1. Executive summary for the exact period.
2. Commercial execution: pipeline movement, customer/opportunity risks, commitments, and task closure.
3. Non-sales execution: completed work, blocked collaboration, daily/weekly report coverage, and operational load.
4. Operational forms: distribution, response, overdue assignments, evidence quality, and report readiness.
5. Performance: goal/plan execution, support demand, reviews, corrections, and learning feedback.
6. Internal research: survey/research coverage, anonymity-safe findings, confidence, and unresolved questions.
7. Cross-domain tensions and dependencies.
8. Recommended next actions, each with owner, time horizon, evidence basis, and confidence.
9. Data quality and permission limits.

Do not convert missing data into a neutral or positive assessment. Do not rank individuals from partial activity traces. Keep formal performance conclusions within the performance domain's governed evidence.

## 5. Execute follow-up only on request

If the user asks to act on a recommendation, route each action back to its owning domain, read current state, show the exact mutation, obtain confirmation, and use that domain's operation tool. The management read tool does not write business state.
