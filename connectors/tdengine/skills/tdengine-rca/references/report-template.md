# Root Cause Analysis Report Template

Use this template for the final RCA deliverable. Replace every bracketed field
with observed evidence or an explicit `Not available`. Keep facts, calculations,
interpretation, and assumptions distinguishable.

```markdown
# Root Cause Analysis Report

## 1. Executive Summary

- **Incident:** [brief description]
- **Target:** [element name and full path]
- **Element ID:** [verified ID]
- **Equipment class or template:** [name, or Not available]
- **Occurrence time:** [ISO 8601 timestamp or range]
- **Analysis window:** [start to end]
- **Baseline:** [matched historical period or peer group]
- **Impact:** [affected equipment, process, production, or safety scope]
- **Severity:** [High / Medium / Low, with basis]
- **Most likely cause:** [one-sentence evidence-qualified conclusion]
- **Confidence:** [High / Medium / Low, with limiting evidence]

## 2. Evidence Quality

| Item | Result |
|---|---|
| Data coverage | [start, end, and percentage] |
| Sampling cadence | [expected and observed] |
| Missing or null samples | [count and percentage] |
| Timestamp issues | [duplicates, gaps, reordering, or None observed] |
| Unit or mapping concerns | [details or None observed] |
| Known limitations | [unavailable attributes, events, peers, or context] |

## 3. Timeline

| Time | Observation or event | Source | Evidence ID |
|---|---|---|---|
| [T-baseline] | [relevant baseline state] | [attribute/event/operator] | [ID or query scope] |
| [T-first] | [first observed anomaly] | [sensor/alarm] | [ID or metric] |
| [T-incident] | [reported fault or trip] | [user/alarm] | [ID or statement] |
| [T-detect] | [monitoring detection] | [event/analysis] | [ID] |
| [T-response] | [operator or maintenance action] | [annotation/user] | [ID or statement] |

## 4. Findings

### 4.1 Reported Symptom

[User-reported symptom, clearly identified as reported rather than measured.]

### 4.2 Key Metric Changes

| Metric | Unit | Baseline | Incident value | Change | Timestamp |
|---|---|---|---|---|---|
| [attribute] | [unit] | [range/statistic] | [value] | [absolute and relative] | [time] |

### 4.3 Events and Alarms

| Time | Event | Severity | Status | Event ID |
|---|---|---|---|---|
| [time] | [event name] | [level] | [acknowledged/unacknowledged] | [ID] |

### 4.4 Time-Series and Cross-Asset Evidence

- **Trend:** [increasing, decreasing, stable, volatile, or inconclusive]
- **Change points:** [timestamps and method]
- **Periodicity:** [period and method, or not supported]
- **High associations:** [attribute pairs, coefficient, lag, sample count]
- **Peer or historical comparison:** [matched scope and measured difference]

## 5. Hypothesis Evaluation

| ID | Hypothesis | Supporting evidence | Contradicting evidence | Status | Confidence |
|---|---|---|---|---|---|
| H001 | [testable mechanism] | [measured evidence] | [measured evidence] | Supported / Rejected / Inconclusive | [level and basis] |
| H002 | [testable mechanism] | [measured evidence] | [measured evidence] | Supported / Rejected / Inconclusive | [level and basis] |

### H001: [Hypothesis Title]

- **Prediction:** [what should be observable if true]
- **Validation method:** [window, filters, calculation, threshold, baseline]
- **Result:** [sample count and exact values]
- **Interpretation:** [why the result supports, rejects, or cannot decide]

Repeat this subsection for each hypothesis.

## 6. Root Cause and Contributing Conditions

### Most Likely Root Cause

[State the mechanism and cite discriminating evidence. If evidence is not
sufficient, state that no root cause is confirmed and identify the leading
hypothesis.]

### Triggering and Contributing Conditions

- [condition and evidence]
- [condition and evidence]

### Why Existing Detection or Protection Did Not Prevent the Impact

[Explain the observed gap, or state Not established.]

## 7. Impact Assessment

- **Downtime:** [duration or Not available]
- **Production impact:** [measured or estimated, label estimates]
- **Related assets or systems:** [scope]
- **Safety or quality impact:** [scope or None reported]

## 8. Recommendations

### Immediate Verification

- [ ] **Check:** [specific inspection or measurement]
  - **Expected result:** [what distinguishes the leading hypothesis]
  - **Owner:** [role, if known]

### Short-Term Actions

- [ ] **Action:** [specific mitigation]
  - **Verification:** [how to confirm effectiveness]
  - **Risk or prerequisite:** [constraint]

### Long-Term Prevention

- [ ] **Action:** [specific engineering or process change]
  - **Success metric:** [measurable outcome]
  - **Time frame:** [when known]

### Monitoring Improvements

- [ ] [metric or event to monitor, threshold rationale, and evaluation window]

Recommendations are proposals. Do not create or update resources as part of
this read-only workflow.

## 9. Appendix

### Data Sources

- **Element IDs:** [IDs]
- **Element paths:** [paths]
- **Template IDs:** [IDs]
- **Attribute IDs and names:** [list]
- **Event IDs:** [list]
- **Analysis range:** [start to end]
- **Baseline range or peers:** [scope]

### Calculation Notes

- [method, parameters, assumptions, and software used]

### Unresolved Questions

- [missing evidence required to increase confidence]
```
