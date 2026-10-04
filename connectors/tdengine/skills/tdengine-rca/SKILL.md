---
name: tdengine-rca
description: Use when diagnosing industrial equipment faults, performance anomalies, alert events, or unexplained metric changes with TDengine data and public MCP tools.
version: "0.6.0"
author: "TDengine"
---

# TDengine Root Cause Analysis

Use public MCP evidence to rank and validate fault hypotheses. Keep discovery,
data retrieval, statistical interpretation, and conclusions traceable. This is
a read-only skill: do not create, update, acknowledge, or delete resources.

## Prohibited Tools

Do not call `ask_idmp`, recommendation tools, `add_*`, `create_*`, update,
acknowledgement, annotation, management, or deletion tools. Never call private
Java endpoints, query a database directly, or invent identifiers.

## Workflow

1. Establish the target, symptom, and time range. Use `search_elements`,
   `get_element_by_path`, or `get_elements_by_ids` when an ID is missing.
2. Read `get_element_context` and `list_element_attributes`. Separate static
   tags from time-series metrics and record units and data types.
3. Retrieve only the evidence needed with `get_attribute_history`,
   `get_batch_attribute_data`, `list_events`, `search_events`, `get_event`,
   `get_event_annotations`, and `get_notification_history`.
4. Compare the incident window with a representative baseline. Check data
   quality before interpreting anomalies.
5. Generate mutually distinguishable hypotheses, state expected evidence for
   each, and run targeted checks.
6. Rank hypotheses by evidence strength and produce an auditable report.

Ask one concise clarification question only when target, symptom, or time range
cannot be discovered safely. Do not silently select among matching elements.

## Evidence Rules

- Preserve timestamps, units, element paths, attribute names, and event IDs.
- Treat correlation and lag correlation as association, not causation.
- Separate observed facts, derived statistics, interpretation, and assumptions.
- Record missing samples, irregular cadence, flat lines, resets, and outliers.
- Prefer a matched historical or peer-device baseline over global averages.
- Report sample count and coverage before claiming trend or periodicity.
- Keep rejected hypotheses in the report with their rejection evidence.
- State uncertainty when evidence is insufficient or contradictory.

## Local Analysis Scripts

Bundled scripts are optional and operate only on data already returned by MCP.
They require Python 3 plus `pandas`, `numpy`, and, for charts, `matplotlib`.
Never pass credentials or service URLs to them.

- `scripts/data_prep.py`: timestamp normalization and numeric cleaning.
- `scripts/analysis_methods.py`: baseline-relative anomaly and drift, lag, and
  correlation helpers.
- `scripts/plotting.py`: incident-versus-baseline charts.
- `scripts/common_io.py`: JSON-safe result output.
- `scripts/hypothesis_runner_template.py`: reusable hypothesis runner.

Use scripts only when their dependencies are available. Otherwise perform the
same calculations in the agent runtime and disclose the method.
Normalize all incident and sample timestamps to timezone-aware UTC before
window slicing. Pass the chosen historical baseline explicitly to anomaly and
drift helpers; never estimate their reference distribution from the incident
window.

## Output Contract

Return sections in this order:

1. Scope: equipment, symptom, analysis window, baseline window.
2. Evidence quality: coverage, cadence, missing data, known limitations.
3. Findings: timestamped facts and derived metrics.
4. Hypothesis table: hypothesis, supporting evidence, contradicting evidence,
   confidence, and status.
5. Most likely cause and contributing conditions.
6. Recommended verification and operational actions, clearly separated.

Do not claim a definitive root cause without discriminating evidence. Do not
recommend writes through MCP as part of this read-only workflow.

## References

- [Clarification prompts](references/clarification-prompts.md)
- [Hypothesis generation](references/hypothesis-generation.md)
- [Analysis methods](references/analysis-methods.md)
- [Code templates](references/code-templates.md)
- [Report template](references/report-template.md)
