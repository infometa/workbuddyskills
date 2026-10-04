---
name: tdengine-data-insights
description: Use when interpreting TDengine panel data, attribute history, device comparisons, operating trends, anomalies, health indicators, or recurring industrial reports.
version: "0.6.0"
author: "TDengine"
---

# TDengine Data Insights

Turn public MCP query results into decision-oriented industrial insights. This
is a read-only skill. Retrieve evidence, quantify it, explain its operational
meaning, and distinguish facts from interpretation.

## Prohibited Tools

Do not call `ask_idmp`, recommendation tools, `add_*`, `create_*`, update,
management, acknowledgement, annotation, or deletion tools. Do not use private
Java endpoints or direct database access.

## Select the Data Route

| Request | Discovery | Data retrieval |
| --- | --- | --- |
| Interpret a known panel | `search_panels`, `list_panels` | `get_panel` |
| Analyze one metric | `get_element_context`, `list_element_attributes` | `get_attribute_history` |
| Compare current values | `search_elements`, `search_attributes` | `get_batch_attribute_data` |
| Explain event context | `list_events`, `search_events` | `get_event`, `get_event_annotations` |
| Assess a branch or fleet | `list_element_children`, `count_branch_elements` | batched attribute reads |

Reuse discovered IDs and exact attribute names. Never invent an ID or silently
choose one of several matching assets.

## Analysis Workflow

1. Define the business question, target population, metrics, units, and time
   range. Use the panel time window unless the user specifies another.
2. Inspect coverage, timestamp order, sampling cadence, nulls, duplicates,
   stale values, flat lines, resets, and impossible values.
3. Compute descriptive statistics appropriate to sample size: count, minimum,
   maximum, mean or median, dispersion, and percentiles.
4. Quantify trends, changes, anomalies, peer differences, and relationships.
   State the baseline and thresholds used.
5. Translate significant findings into operational impact and prioritized
   actions. Avoid unsupported causal claims.

## Guardrails

- Do not aggregate averages again unless the weighting is known.
- Do not compare metrics with incompatible units without normalization.
- Do not infer health from one current value when history is available.
- Do not extrapolate beyond the observed period without stating uncertainty.
- Correlation does not establish causation.
- For sparse or irregular data, report coverage before trend conclusions.
- Preserve tool timestamps and IDs in supporting evidence.
- Paginate or narrow large requests; do not imply full coverage after page one.

## Bundled Script

`scripts/analyze_ts.py` is an optional Python 3 standard-library utility for
JSON returned by MCP. It summarizes history or panel query data, checks data
quality, aggregates buckets, and detects simple trends and anomalies. It
accepts local data only and must never receive credentials or service URLs.

See [function catalog](references/function-catalog.md) and
[execution recipes](references/execution-recipes.md) before using it.

## Output Contract

Return sections in this order:

1. Executive finding: the decision-relevant result in one short paragraph.
2. Scope and evidence quality: targets, period, coverage, and limitations.
3. Quantified findings: trends, anomalies, comparisons, and relationships.
4. Operational interpretation: what findings may mean and alternatives.
5. Prioritized actions: verification first, intervention second.

Use tables only when they improve comparison. Include exact values and units,
and state when the evidence is insufficient.

## References

- [Execution recipes](references/execution-recipes.md)
- [Function catalog](references/function-catalog.md)
- [Analysis methodology](references/analysis-methodology.md)
- [Known pitfalls](references/gotchas.md)
- [Report structure](references/report-structure.md)
