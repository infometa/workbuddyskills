# Data Insight Report Structure

Use this structure for a complete decision-oriented report. Keep the evidence traceable to the time range, elements, attributes, and tools used.

## Report Template

```markdown
# [Title that states the subject and analysis scope]

## Executive Summary

[Two or three sentences with the answer first. Quantify the most important finding, state confidence, and name the main caveat.]

## Context and Scope

- Decision or question: [...]
- Elements/devices: [...]
- Attributes or panel: [...]
- Time range: [...]
- Sampling interval and observed point count: [...]
- Data source: [tool calls and resource identifiers]

## Data Quality

- Completeness: [...]
- Missing or duplicate points: [...]
- Sampling regularity: [...]
- Known limitations: [...]

## Findings

### Finding 1: [specific result]

**Observation:** [What changed or differs, with values and units.]

**Evidence:**

| Measure | Baseline | Observed | Difference |
|---|---:|---:|---:|
| [...] | [...] | [...] | [...] |

**Interpretation:** [What the evidence supports. Distinguish correlation from causation.]

**Confidence:** [High/medium/low and why.]

### Finding 2: [specific result]

[Repeat the same evidence-first structure.]

### Finding 3: [specific result]

[Repeat only when it materially changes the decision.]

## Conclusion

[Answer the original question directly. Include ranges or uncertainty instead of false precision.]

## Recommended Actions

1. **Immediate:** [Action, owner, and observable success criterion.]
2. **Next:** [Validation or monitoring step.]
3. **If evidence remains weak:** [Additional data or experiment needed.]

## Method Notes

- Transformations and filters: [...]
- Aggregation and comparison baseline: [...]
- Functions used: [...]
- Assumptions: [...]
```

## Formatting Requirements

- Lead with findings, not the procedure.
- Always include units, absolute timestamps, and the exact analysis range.
- Quantify differences with both absolute values and percentages when meaningful.
- Use tables for comparisons and short prose for interpretation.
- State sample size and data-quality limitations beside the affected result.
- Do not claim causality from correlation alone.
- Separate observations, interpretations, and recommendations.
- Do not expose credentials, tokens, internal endpoints, or raw sensitive records.
